import time
import uuid
from typing import Optional, List

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Text, BigInteger, JSON

from open_webui.internal.db import Base, get_db, JSONField
from open_webui.models.users import Users, UserResponse
from open_webui.utils.access_control import has_access


##############################
# Dataset Evaluation DB Schema
##############################


class DatasetEvaluation(Base):
    __tablename__ = "dataset_evaluation"

    id = Column(Text, primary_key=True)
    dataset_id = Column(Text, nullable=True)
    user_id = Column(Text, nullable=False)

    target_model_id = Column(Text, nullable=True)
    judge_model_id = Column(Text, nullable=True)
    meta = Column(JSONField)

    status = Column(Text, default="pending")
    task_ids = Column(JSONField)
    passed_task_ids = Column(JSONField)
    access_control = Column(JSON, nullable=True)

    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class DatasetEvaluationMeta(BaseModel):
    target_model: Optional[dict] = None
    judge_model: Optional[dict] = None

    model_config = ConfigDict(extra="allow")


class DatasetEvaluationModel(BaseModel):
    id: str
    dataset_id: str
    user_id: str
    target_model_id: Optional[str] = None
    judge_model_id: Optional[str] = None
    meta: DatasetEvaluationMeta
    status: str
    task_ids: List[str]
    passed_task_ids: List[str]
    access_control: Optional[dict] = None
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##############################
# Forms
##############################


class DatasetEvaluationUserResponse(DatasetEvaluationModel):
    user: Optional[UserResponse] = None


class DatasetEvaluationForm(BaseModel):
    dataset_id: str
    target_model_id: Optional[str] = None
    judge_model_id: Optional[str] = None
    meta: DatasetEvaluationMeta
    task_ids: List[str]
    passed_task_ids: Optional[List[str]] = []
    status: Optional[str] = "pending"
    access_control: Optional[dict] = None


class DatasetEvaluationsTable:
    def insert_evaluation(
        self, user_id: str, form_data: DatasetEvaluationForm
    ) -> Optional[DatasetEvaluationModel]:
        evaluation = DatasetEvaluationModel(
            **form_data.model_dump(),
            id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        try:
            with get_db() as db:
                result = DatasetEvaluation(**evaluation.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                return DatasetEvaluationModel.model_validate(result)
        except Exception:
            return None

    def get_evaluations(self) -> list[DatasetEvaluationUserResponse]:
        with get_db() as db:
            evaluations = []
            for e in (
                db.query(DatasetEvaluation)
                .order_by(DatasetEvaluation.updated_at.desc())
                .all()
            ):
                user = Users.get_user_by_id(e.user_id)
                evaluations.append(
                    DatasetEvaluationUserResponse.model_validate(
                        {
                            **DatasetEvaluationModel.model_validate(e).model_dump(),
                            "user": user.model_dump() if user else None,
                        }
                    )
                )
            return evaluations

    def get_evaluations_by_user_id(
        self, user_id: str, permission: str = "write"
    ) -> list[DatasetEvaluationUserResponse]:
        evaluations = self.get_evaluations()
        return [
            e
            for e in evaluations
            if e.user_id == user_id or has_access(user_id, permission, e.access_control)
        ]

    def get_evaluations_by_dataset_id(
        self, dataset_id: str
    ) -> list[DatasetEvaluationModel]:
        with get_db() as db:
            return [
                DatasetEvaluationModel.model_validate(e)
                for e in db.query(DatasetEvaluation)
                .filter_by(dataset_id=dataset_id)
                .all()
            ]

    def get_evaluation_by_id(self, id: str) -> Optional[DatasetEvaluationModel]:
        with get_db() as db:
            e = db.get(DatasetEvaluation, id)
            return DatasetEvaluationModel.model_validate(e) if e else None

    def update_evaluation_status(
        self, id: str, status: str
    ) -> Optional[DatasetEvaluationModel]:
        try:
            with get_db() as db:
                db.query(DatasetEvaluation).filter_by(id=id).update(
                    {"status": status, "updated_at": int(time.time())}
                )
                db.commit()
                e = db.get(DatasetEvaluation, id)
                db.refresh(e)
                return DatasetEvaluationModel.model_validate(e)
        except Exception:
            return None

    def delete_evaluation_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                db.query(DatasetEvaluation).filter_by(id=id).delete()
                db.commit()
                return True
        except Exception:
            return False


DatasetEvaluations = DatasetEvaluationsTable()
