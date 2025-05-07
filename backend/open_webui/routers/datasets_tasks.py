from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Optional, List
from open_webui.models.datasets_tasks import (
    DatasetTaskForm,
    DatasetTaskModel,
    DatasetTaskUserResponse,
    DatasetTasks,
)
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.auth import get_verified_user
from open_webui.utils.access_control import has_access, has_permission

router = APIRouter()


@router.get("/", response_model=List[DatasetTaskUserResponse])
async def get_tasks(user=Depends(get_verified_user)):
    return (
        DatasetTasks.get_tasks()
        if user.role == "admin"
        else DatasetTasks.get_tasks_by_user_id(user.id)
    )


@router.get("/task", response_model=Optional[DatasetTaskModel])
async def get_task_by_id(id: str, user=Depends(get_verified_user)):
    task = DatasetTasks.get_task_by_id(id)
    if task and (
        user.role == "admin"
        or task.user_id == user.id
        or has_access(user.id, "read", task.access_control)
    ):
        return task
    raise HTTPException(status_code=401, detail=ERROR_MESSAGES.NOT_FOUND)


@router.get("/dataset", response_model=List[DatasetTaskModel])
async def get_tasks_by_dataset_id(dataset_id: str, user=Depends(get_verified_user)):
    return DatasetTasks.get_tasks_by_dataset_id(dataset_id)


@router.post("/create", response_model=Optional[DatasetTaskModel])
async def create_task(
    request: Request, form_data: DatasetTaskForm, user=Depends(get_verified_user)
):
    if user.role != "admin" and not has_permission(
        user.id, "workspace.datasets", request.app.state.config.USER_PERMISSIONS
    ):
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.UNAUTHORIZED)
    task = DatasetTasks.insert_task(user.id, form_data)
    if task:
        return task
    raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT())


@router.post("/task/update", response_model=Optional[DatasetTaskModel])
async def update_task(
    id: str,
    form_data: DatasetTaskForm,
    user=Depends(get_verified_user),
):
    task = DatasetTasks.get_task_by_id(id)
    if not task:
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.NOT_FOUND)
    if (
        user.role != "admin"
        and task.user_id != user.id
        and not has_access(user.id, "write", task.access_control)
    ):
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.UNAUTHORIZED)

    return DatasetTasks.update_task_by_id(id, form_data)


@router.delete("/task/delete", response_model=bool)
async def delete_task(id: str, user=Depends(get_verified_user)):
    task = DatasetTasks.get_task_by_id(id)
    if not task:
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.NOT_FOUND)
    if (
        user.role != "admin"
        and task.user_id != user.id
        and not has_access(user.id, "write", task.access_control)
    ):
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.UNAUTHORIZED)
    return DatasetTasks.delete_task_by_id(id)
