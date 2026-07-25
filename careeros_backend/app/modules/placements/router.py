from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.placements.dependencies import (
    get_application_service,
    get_college_service,
    get_placement_drive_service,
    verify_placement_officer_access,
)
from app.modules.placements.schemas import (
    CollegeCreate,
    CollegeResponse,
    DriveRegistrationResponse,
    DriveRegistrationUpdate,
    OfferLetterCreate,
    OfferLetterResponse,
    PlacementDriveCreate,
    PlacementDriveResponse,
)
from app.modules.placements.services.application_service import ApplicationService
from app.modules.placements.services.college_service import CollegeService
from app.modules.placements.services.placement_drive_service import PlacementDriveService
from app.modules.placements.tasks import (
    calculate_drive_eligibility_background,
    rank_students_for_drive_background,
)

router = APIRouter(prefix="/placements", tags=["placements"])


# ── College Management ──────────────────────────────────────────────────────
@router.post("/colleges", response_model=CollegeResponse, status_code=status.HTTP_201_CREATED)
async def create_college(
    college_in: CollegeCreate,
    current_user: User = Depends(get_current_user),
    college_service: CollegeService = Depends(get_college_service),
):
    return await college_service.create_college(current_user.id, college_in)


# ── Placement Drives ────────────────────────────────────────────────────────
@router.post("/drives", response_model=PlacementDriveResponse, status_code=status.HTTP_201_CREATED)
async def create_drive(
    drive_in: PlacementDriveCreate,
    college_id: UUID = Depends(verify_placement_officer_access),
    drive_service: PlacementDriveService = Depends(get_placement_drive_service),
):
    return await drive_service.create_drive(college_id, drive_in)


@router.get("/drives", response_model=List[PlacementDriveResponse])
async def list_college_drives(
    college_id: UUID = Depends(verify_placement_officer_access),
    drive_service: PlacementDriveService = Depends(get_placement_drive_service),
):
    return await drive_service.get_college_drives(college_id)


@router.get("/drives/{drive_id}", response_model=PlacementDriveResponse)
async def get_drive(
    drive_id: UUID,
    college_id: UUID = Depends(verify_placement_officer_access),
    drive_service: PlacementDriveService = Depends(get_placement_drive_service),
):
    drive = await drive_service.get_drive(drive_id)
    if not drive or drive.college_id != college_id:
        raise HTTPException(status_code=404, detail="Drive not found.")
    return drive


# ── Eligibility (background) ────────────────────────────────────────────────
@router.post("/drives/{drive_id}/calculate-eligibility", status_code=status.HTTP_202_ACCEPTED)
async def trigger_eligibility_calculation(
    drive_id: UUID,
    college_id: UUID = Depends(verify_placement_officer_access),
    drive_service: PlacementDriveService = Depends(get_placement_drive_service),
):
    drive = await drive_service.get_drive(drive_id)
    if not drive or drive.college_id != college_id:
        raise HTTPException(status_code=404, detail="Drive not found.")

    calculate_drive_eligibility_background.delay(str(drive_id))
    return {"status": "accepted", "message": "Eligibility calculation started in background."}


# ── Student Registrations ───────────────────────────────────────────────────
@router.post(
    "/drives/{drive_id}/register",
    response_model=DriveRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_for_drive(
    drive_id: UUID,
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
):
    return await application_service.register_student(drive_id, current_user.id)


@router.get("/drives/{drive_id}/registrations", response_model=List[DriveRegistrationResponse])
async def list_drive_registrations(
    drive_id: UUID,
    college_id: UUID = Depends(verify_placement_officer_access),
    drive_service: PlacementDriveService = Depends(get_placement_drive_service),
    application_service: ApplicationService = Depends(get_application_service),
):
    drive = await drive_service.get_drive(drive_id)
    if not drive or drive.college_id != college_id:
        raise HTTPException(status_code=404, detail="Drive not found.")
    return await application_service.get_drive_registrations(drive_id)


@router.patch("/registrations/{registration_id}", response_model=DriveRegistrationResponse)
async def update_registration_status(
    registration_id: UUID,
    update_in: DriveRegistrationUpdate,
    college_id: UUID = Depends(verify_placement_officer_access),
    application_service: ApplicationService = Depends(get_application_service),
):
    reg = await application_service.update_registration_status(registration_id, update_in)
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found.")
    return reg


# ── Offer Letters ────────────────────────────────────────────────────────────
@router.post(
    "/registrations/{registration_id}/offer",
    response_model=OfferLetterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def release_offer(
    registration_id: UUID,
    offer_in: OfferLetterCreate,
    college_id: UUID = Depends(verify_placement_officer_access),
    application_service: ApplicationService = Depends(get_application_service),
):
    return await application_service.add_offer_letter(registration_id, offer_in)


# ── Student Rankings (background) ───────────────────────────────────────────
@router.post("/drives/{drive_id}/rank", status_code=status.HTTP_202_ACCEPTED)
async def trigger_student_ranking(
    drive_id: UUID,
    college_id: UUID = Depends(verify_placement_officer_access),
    drive_service: PlacementDriveService = Depends(get_placement_drive_service),
):
    drive = await drive_service.get_drive(drive_id)
    if not drive or drive.college_id != college_id:
        raise HTTPException(status_code=404, detail="Drive not found.")

    rank_students_for_drive_background.delay(str(drive_id))
    return {"status": "accepted", "message": "Student ranking started in background."}
