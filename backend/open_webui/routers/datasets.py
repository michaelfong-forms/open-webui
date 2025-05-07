from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.models.datasets import (
    DatasetForm,
    DatasetUserResponse,
    DatasetModel,
    Datasets,
)
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.utils.access_control import has_access, has_permission

router = APIRouter()


@router.get("/", response_model=List[DatasetUserResponse])
async def get_datasets(user=Depends(get_verified_user)):
    return (
        Datasets.get_datasets()
        if user.role == "admin"
        else Datasets.get_datasets_by_user_id(user.id, "read")
    )


@router.get("/dataset", response_model=Optional[DatasetModel])
async def get_dataset_by_id(id: str, user=Depends(get_verified_user)):
    dataset = Datasets.get_dataset_by_id(id)
    if dataset and (
        user.role == "admin"
        or dataset.user_id == user.id
        or has_access(user.id, "read", dataset.access_control)
    ):
        return dataset
    raise HTTPException(status_code=401, detail=ERROR_MESSAGES.NOT_FOUND)


@router.post("/create", response_model=Optional[DatasetModel])
async def create_dataset(
    request: Request, form_data: DatasetForm, user=Depends(get_verified_user)
):
    if user.role != "admin" and not has_permission(
        user.id, "workspace.datasets", request.app.state.config.USER_PERMISSIONS
    ):
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.UNAUTHORIZED)
    if Datasets.get_dataset_by_id(form_data.id):
        raise HTTPException(status_code=400, detail="Dataset ID already taken")
    dataset = Datasets.insert_new_dataset(user.id, form_data)
    if not dataset:
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT())
    return dataset


@router.post("/dataset/update", response_model=Optional[DatasetModel])
async def update_dataset(
    id: str, form_data: DatasetForm, user=Depends(get_verified_user)
):
    dataset = Datasets.get_dataset_by_id(id)
    if not dataset:
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.NOT_FOUND)
    if (
        user.role != "admin"
        and dataset.user_id != user.id
        and not has_access(user.id, "write", dataset.access_control)
    ):
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.ACCESS_PROHIBITED)
    return Datasets.update_dataset_by_id(id, form_data)


@router.delete("/dataset/delete", response_model=bool)
async def delete_dataset(id: str, user=Depends(get_verified_user)):
    dataset = Datasets.get_dataset_by_id(id)
    if not dataset:
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.NOT_FOUND)
    if (
        user.role != "admin"
        and dataset.user_id != user.id
        and not has_access(user.id, "write", dataset.access_control)
    ):
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.ACCESS_PROHIBITED)
    return Datasets.delete_dataset_by_id(id)
