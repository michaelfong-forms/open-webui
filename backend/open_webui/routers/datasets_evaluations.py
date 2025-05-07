from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Optional, List
from open_webui.models.datasets_evaluations import (
    DatasetEvaluationForm,
    DatasetEvaluationModel,
    DatasetEvaluationUserResponse,
    DatasetEvaluations,
)
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.auth import get_verified_user
from open_webui.utils.access_control import has_access, has_permission

router = APIRouter()


@router.get("/", response_model=List[DatasetEvaluationUserResponse])
async def get_evaluations(user=Depends(get_verified_user)):
    return (
        DatasetEvaluations.get_evaluations()
        if user.role == "admin"
        else DatasetEvaluations.get_evaluations_by_user_id(user.id)
    )


@router.get("/evaluation", response_model=Optional[DatasetEvaluationModel])
async def get_evaluation_by_id(id: str, user=Depends(get_verified_user)):
    evaluation = DatasetEvaluations.get_evaluation_by_id(id)
    if evaluation and (
        user.role == "admin"
        or evaluation.user_id == user.id
        or has_access(user.id, "read", evaluation.access_control)
    ):
        return evaluation
    raise HTTPException(status_code=401, detail=ERROR_MESSAGES.NOT_FOUND)


@router.get("/dataset", response_model=List[DatasetEvaluationModel])
async def get_evaluations_by_dataset_id(
    dataset_id: str, user=Depends(get_verified_user)
):
    return DatasetEvaluations.get_evaluations_by_dataset_id(dataset_id)


@router.post("/create", response_model=Optional[DatasetEvaluationModel])
async def create_evaluation(
    request: Request, form_data: DatasetEvaluationForm, user=Depends(get_verified_user)
):
    if user.role != "admin" and not has_permission(
        user.id, "workspace.datasets", request.app.state.config.USER_PERMISSIONS
    ):
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.UNAUTHORIZED)
    evaluation = DatasetEvaluations.insert_evaluation(user.id, form_data)
    if evaluation:
        return evaluation
    raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT())


@router.post(
    "/evaluation/status/update", response_model=Optional[DatasetEvaluationModel]
)
async def update_evaluation_status(
    id: str, status: str, user=Depends(get_verified_user)
):
    evaluation = DatasetEvaluations.get_evaluation_by_id(id)
    if not evaluation:
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.NOT_FOUND)
    if (
        user.role != "admin"
        and evaluation.user_id != user.id
        and not has_access(user.id, "write", evaluation.access_control)
    ):
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.UNAUTHORIZED)
    return DatasetEvaluations.update_evaluation_status(id, status)


@router.delete("/evaluation/delete", response_model=bool)
async def delete_evaluation(id: str, user=Depends(get_verified_user)):
    evaluation = DatasetEvaluations.get_evaluation_by_id(id)
    if not evaluation:
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.NOT_FOUND)
    if (
        user.role != "admin"
        and evaluation.user_id != user.id
        and not has_access(user.id, "write", evaluation.access_control)
    ):
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.UNAUTHORIZED)
    return DatasetEvaluations.delete_evaluation_by_id(id)
