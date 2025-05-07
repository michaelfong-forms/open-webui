import time
import uuid
from typing import Optional, List

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Text, Boolean, BigInteger, JSON

from open_webui.internal.db import Base, get_db, JSONField
from open_webui.models.users import Users, UserResponse
from open_webui.utils.access_control import has_access


##############################
# Dataset Task DB Schema
##############################


class DatasetTask(Base):
    __tablename__ = "dataset_task"

    id = Column(Text, primary_key=True)
    dataset_id = Column(Text, nullable=True)
    user_id = Column(Text, nullable=False)

    instruction = Column(Text, nullable=False)
    input = Column(Text, nullable=False)
    output = Column(Text, nullable=False)

    evaluation_criteria = Column(Text, nullable=True)
    meta = Column(JSONField)
    is_training_example = Column(Boolean, default=False)
    access_control = Column(JSON, nullable=True)

    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class DatasetTaskModel(BaseModel):
    id: str
    dataset_id: str
    user_id: str
    instruction: str
    input: str
    output: str
    evaluation_criteria: Optional[str] = None
    meta: dict
    is_training_example: bool
    access_control: Optional[dict] = None
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


##############################
# Forms
##############################


class DatasetTaskUserResponse(DatasetTaskModel):
    user: Optional[UserResponse] = None


class DatasetTaskForm(BaseModel):
    dataset_id: str
    instruction: str
    input: str
    output: str
    evaluation_criteria: Optional[str] = None
    meta: dict
    is_training_example: Optional[bool] = False
    access_control: Optional[dict] = None


class DatasetTasksTable:
    def insert_task(
        self, user_id: str, form_data: DatasetTaskForm
    ) -> Optional[DatasetTaskModel]:
        task = DatasetTaskModel(
            **form_data.model_dump(),
            id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        try:
            with get_db() as db:
                result = DatasetTask(**task.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                return DatasetTaskModel.model_validate(result)
        except Exception:
            return None

    def get_tasks(self) -> list[DatasetTaskUserResponse]:
        with get_db() as db:
            tasks = []
            for task in (
                db.query(DatasetTask).order_by(DatasetTask.updated_at.desc()).all()
            ):
                user = Users.get_user_by_id(task.user_id)
                tasks.append(
                    DatasetTaskUserResponse.model_validate(
                        {
                            **DatasetTaskModel.model_validate(task).model_dump(),
                            "user": user.model_dump() if user else None,
                        }
                    )
                )
            return tasks

    def get_tasks_by_user_id(
        self, user_id: str, permission: str = "write"
    ) -> list[DatasetTaskUserResponse]:
        tasks = self.get_tasks()
        return [
            task
            for task in tasks
            if task.user_id == user_id
            or has_access(user_id, permission, task.access_control)
        ]

    def get_tasks_by_dataset_id(self, dataset_id: str) -> list[DatasetTaskModel]:
        with get_db() as db:
            return [
                DatasetTaskModel.model_validate(t)
                for t in db.query(DatasetTask).filter_by(dataset_id=dataset_id).all()
            ]

    def get_task_by_id(self, id: str) -> Optional[DatasetTaskModel]:
        with get_db() as db:
            task = db.get(DatasetTask, id)
            return DatasetTaskModel.model_validate(task) if task else None

    def update_task_by_id(
        self, id: str, form_data: DatasetTaskForm
    ) -> Optional[DatasetTaskModel]:
        try:
            with get_db() as db:
                db.query(DatasetTask).filter_by(id=id).update(
                    {
                        **form_data.model_dump(exclude={"id"}),
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                task = db.get(DatasetTask, id)
                db.refresh(task)
                return DatasetTaskModel.model_validate(task)
        except Exception:
            return None

    def delete_task_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                db.query(DatasetTask).filter_by(id=id).delete()
                db.commit()
                return True
        except Exception:
            return False


DatasetTasks = DatasetTasksTable()
