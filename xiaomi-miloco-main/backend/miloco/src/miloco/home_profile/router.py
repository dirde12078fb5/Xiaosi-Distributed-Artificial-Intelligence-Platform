# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""home_profile controller — 家庭档案 CRUD + commit + 渲染。"""

import logging

from fastapi import APIRouter, Depends, Query

from miloco.home_profile.schema import (
    CandidateWriteBody,
    ImportBody,
    ProfileWriteBody,
    ReassignBody,
    ResetBody,
)
from miloco.manager import get_manager
from miloco.middleware import verify_token
from miloco.schema.common_schema import NormalResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/home-profile", tags=["HomeProfile"])

manager = get_manager()


@router.get("/entries", summary="List Entries", response_model=NormalResponse)
async def list_entries(
    target: str = Query("both", pattern="^(profile|candidates|both)$"),
    current_user: str = Depends(verify_token),
):
    data = manager.home_profile_service.list_entries(target)
    return NormalResponse(code=0, message="ok", data=data)


@router.post("/candidates:write", summary="Candidate Write", response_model=NormalResponse)
async def candidate_write(body: CandidateWriteBody, current_user: str = Depends(verify_token)):
    results = manager.home_profile_service.candidate_write(body.ops)
    return NormalResponse(code=0, message="ok", data=[r.model_dump() for r in results])


@router.post("/profile:write", summary="Profile Write", response_model=NormalResponse)
async def profile_write(body: ProfileWriteBody, current_user: str = Depends(verify_token)):
    results = manager.home_profile_service.profile_write(body.ops, body.user_edit)
    return NormalResponse(code=0, message="ok", data=[r.model_dump() for r in results])


@router.post("/commit", summary="Commit", response_model=NormalResponse)
async def commit(current_user: str = Depends(verify_token)):
    data = manager.home_profile_service.commit()
    return NormalResponse(code=0, message="ok", data=data)


@router.post("/subject:reassign", summary="Reassign Subject", response_model=NormalResponse)
async def reassign_subject(body: ReassignBody, current_user: str = Depends(verify_token)):
    data = manager.home_profile_service.reassign_subject(body.mappings)
    return NormalResponse(code=0, message="ok", data=data)


@router.get("/rendered", summary="Get Rendered Profile", response_model=NormalResponse)
async def rendered(current_user: str = Depends(verify_token)):
    data = manager.home_profile_service.rendered()
    return NormalResponse(code=0, message="ok", data={"markdown": data})


@router.post("/import", summary="Import Legacy Data", response_model=NormalResponse)
async def import_data(body: ImportBody, current_user: str = Depends(verify_token)):
    data = manager.home_profile_service.import_data(body)
    return NormalResponse(code=0, message="ok", data=data)


@router.post("/reset", summary="Reset Profile (Full Overwrite + Commit)", response_model=NormalResponse)
async def reset(body: ResetBody, current_user: str = Depends(verify_token)):
    data = manager.home_profile_service.reset(body)
    return NormalResponse(code=0, message="ok", data=data)
