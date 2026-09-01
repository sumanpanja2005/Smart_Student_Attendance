import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import get_current_user
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
)
from app.services.notification_repository import NotificationRepository

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List logged-in user's notifications",
)
def list_my_notifications(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Retrieves logged-in user's notifications and unread count."""
    user_id = current_user["id"]
    notifications = NotificationRepository.list_notifications(user_id, limit=limit)
    unread_count = NotificationRepository.get_unread_count(user_id)
    return NotificationListResponse(notifications=notifications, unread_count=unread_count)


@router.get(
    "/unread-count",
    summary="Get unread notifications count",
)
def get_unread_count(
    current_user: dict = Depends(get_current_user),
):
    """Retrieves unread notifications count for logged-in user."""
    count = NotificationRepository.get_unread_count(current_user["id"])
    return {"unread_count": count}


@router.patch(
    "/{notification_id}/read",
    summary="Mark single notification as read",
)
def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Marks specified notification as read (enforces ownership)."""
    success = NotificationRepository.mark_as_read(notification_id, current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied.",
        )
    return {"success": True, "message": "Notification marked as read."}


@router.patch(
    "/read-all",
    summary="Mark all user notifications as read",
)
def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user),
):
    """Marks all notifications for logged-in user as read."""
    count = NotificationRepository.mark_all_as_read(current_user["id"])
    return {"success": True, "updated_count": count}


@router.delete(
    "/{notification_id}",
    summary="Delete single notification",
)
def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Deletes specified notification (enforces ownership)."""
    success = NotificationRepository.delete_notification(notification_id, current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied.",
        )
    return {"success": True, "message": "Notification deleted."}


# --- PREFERENCES ---
@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Get logged-in user's notification preferences",
)
def get_notification_preferences(
    current_user: dict = Depends(get_current_user),
):
    """Retrieves notification preferences for logged-in user."""
    return NotificationRepository.get_preferences(current_user["id"])


@router.patch(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Update logged-in user's notification preferences",
)
def update_notification_preferences(
    payload: NotificationPreferenceUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Updates notification preferences for logged-in user."""
    update_dict = payload.dict(exclude_unset=True)
    pref = NotificationRepository.update_preferences(current_user["id"], update_dict)
    from app.services.audit_service import AuditService
    AuditService.log_event(
        action="NOTIFICATION_PREFERENCES_UPDATED",
        event_type="NOTIFICATION_PREFERENCES_UPDATED",
        resource_type="NOTIFICATION_PREFERENCE",
        message="User updated notification preferences",
        actor_user_id=current_user["id"],
        actor_role=current_user["role"],
    )
    return pref
