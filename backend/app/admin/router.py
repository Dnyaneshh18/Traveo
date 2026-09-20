"""
Traveo Backend — Admin & Operations Router

REST endpoints for operational dashboards, driver verification queue,
system configuration editor, and audit logs. Protected by RBAC (RequireAdmin).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import DriverApprovalRequest, SystemConfigUpdateRequest
from app.admin.service import AdminService
from app.core.database import get_db_session
from app.dependencies import RequireAdmin
from app.schemas.base import success_response

router = APIRouter()


def _get_admin_service(db: AsyncSession = Depends(get_db_session)) -> AdminService:
    return AdminService(db)


# ── GET /admin/dashboard ────────────────────────────────────
@router.get("/dashboard")
async def get_dashboard_kpis(
    user_info: tuple[str, str] = Depends(RequireAdmin),
    service: AdminService = Depends(_get_admin_service),
):
    """
    Get real-time operational KPIs for the Admin Panel.
    """
    result = await service.get_dashboard_kpis()
    return success_response(
        data=result.model_dump(),
        message="Dashboard KPIs retrieved.",
    )


# ── POST /admin/drivers/{driver_id}/verification ────────────
@router.post("/drivers/{driver_id}/verification")
async def review_driver_verification(
    driver_id: str,
    request: DriverApprovalRequest,
    user_info: tuple[str, str] = Depends(RequireAdmin),
    service: AdminService = Depends(_get_admin_service),
):
    """
    Approve or reject a driver verification application.
    """
    admin_id = user_info[0]
    await service.review_driver_verification(admin_id, driver_id, request)
    return success_response(
        message=f"Driver verification status updated to {request.status.value}."
    )


# ── PUT /admin/configuration ────────────────────────────────
@router.put("/configuration")
async def update_system_config(
    request: SystemConfigUpdateRequest,
    user_info: tuple[str, str] = Depends(RequireAdmin),
    service: AdminService = Depends(_get_admin_service),
):
    """
    Update a runtime system configuration parameter.
    """
    admin_id = user_info[0]
    result = await service.update_system_config(admin_id, request)
    return success_response(
        data=result.model_dump(),
        message="System configuration updated.",
    )


# ── GET /admin/audit-logs ────────────────────────────────────
@router.get("/audit-logs")
async def get_audit_logs(
    user_info: tuple[str, str] = Depends(RequireAdmin),
    service: AdminService = Depends(_get_admin_service),
):
    """
    Get recent system audit logs.
    """
    results = await service.get_audit_logs()
    return success_response(
        data=[r.model_dump() for r in results],
        message="Audit logs retrieved.",
    )
