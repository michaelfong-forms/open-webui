import time
from typing import Optional, List

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Text, Boolean, BigInteger, JSON

from open_webui.internal.db import Base, get_db, JSONField
from open_webui.models.users import Users, UserResponse
from open_webui.utils.access_control import has_access


####################
# Datasets DB Schema
####################


class Dataset(Base):
    __tablename__ = "dataset"

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False)

    name = Column(Text, nullable=False)
    version = Column(Text, default="1.0")
    evaluation_method = Column(Text, default="Criteria Based")

    meta = Column(JSONField)
    access_control = Column(JSON, nullable=True)

    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class DatasetMeta(BaseModel):
    description: Optional[str] = None


class DatasetModel(BaseModel):
    id: str
    user_id: str
    name: str
    version: str
    evaluation_method: str
    meta: DatasetMeta
    access_control: Optional[dict] = None
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class DatasetUserResponse(DatasetModel):
    user: Optional[UserResponse] = None


class DatasetForm(BaseModel):
    id: str
    name: str
    version: Optional[str] = "1.0"
    evaluation_method: Optional[str] = "Criteria Based"
    meta: DatasetMeta
    access_control: Optional[dict] = None


class DatasetsTable:
    def insert_new_dataset(
        self, user_id: str, form_data: DatasetForm
    ) -> Optional[DatasetModel]:
        dataset = DatasetModel(
            **form_data.model_dump(),
            user_id=user_id,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )

        try:
            with get_db() as db:
                result = Dataset(**dataset.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                return DatasetModel.model_validate(result)
        except Exception:
            return None

    def get_dataset_by_id(self, id: str) -> Optional[DatasetModel]:
        with get_db() as db:
            dataset = db.get(Dataset, id)
            return DatasetModel.model_validate(dataset) if dataset else None

    def get_datasets(self) -> list[DatasetUserResponse]:
        with get_db() as db:
            datasets = []

            for dataset in db.query(Dataset).order_by(Dataset.updated_at.desc()).all():
                user = Users.get_user_by_id(dataset.user_id)
                datasets.append(
                    DatasetUserResponse.model_validate(
                        {
                            **DatasetModel.model_validate(dataset).model_dump(),
                            "user": user.model_dump() if user else None,
                        }
                    )
                )
            return datasets

    def get_datasets_by_user_id(
        self, user_id: str, permission: str = "write"
    ) -> list[DatasetUserResponse]:
        datasets = self.get_datasets()

        return [
            dataset
            for dataset in datasets
            if dataset.user_id == user_id
            or has_access(user_id, permission, dataset.access_control)
        ]

    def update_dataset_by_id(
        self, id: str, form_data: DatasetForm
    ) -> Optional[DatasetModel]:
        try:
            with get_db() as db:
                db.query(Dataset).filter_by(id=id).update(
                    {**form_data.model_dump(exclude={"id"}), "updated_at": int(time.time())}
                )
                db.commit()
                dataset = db.get(Dataset, id)
                db.refresh(dataset)
                return DatasetModel.model_validate(dataset)
        except Exception:
            return None

    def delete_dataset_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                db.query(Dataset).filter_by(id=id).delete()
                db.commit()
                return True
        except Exception:
            return False


Datasets = DatasetsTable()
