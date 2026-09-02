from fastapi import APIRouter, HTTPException, status, Depends
from app.core.security import verify_password, create_access_token
from app.db.mongo import db_manager
from app.schemas.user import LoginRequest, TokenResponse, UserResponse
from app.api.deps import get_current_user
from app.services.academic_service import sanitize_doc
from app.services.audit_service import AuditService
from app.services.security_audit_service import SecurityAuditService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest):
    """
    Authenticates user with email & password, returning JWT access token and user info.
    """
    db = db_manager.db
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable",
        )

    user = db.users.find_one({"email": credentials.email.lower().strip()})
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        # Audit failed login safely
        SecurityAuditService.log_failed_login(email=credentials.email, reason="Invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        SecurityAuditService.log_failed_login(email=credentials.email, reason="Account deactivated")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your account has been deactivated. Please contact an administrator.",
        )

    user_id_str = str(user["_id"])
    token_payload = {
        "sub": user_id_str,
        "user_id": user_id_str,
        "role": user.get("role"),
    }
    access_token = create_access_token(data=token_payload)

    user_data = sanitize_doc(user)

    # Audit successful login safely
    AuditService.log_auth_event(
        event_type="AUTH_LOGIN",
        message=f"User {user.get('email')} logged in successfully.",
        actor_user_id=user_id_str,
        actor_role=user.get("role"),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user_data),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Returns the authenticated user's profile."""
    return UserResponse(**current_user)


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """
    Stateless JWT logout confirmation.
    The client application clears the stored access token upon receiving this response.
    """
    if current_user:
        AuditService.log_auth_event(
            event_type="AUTH_LOGOUT",
            message=f"User {current_user.get('email')} logged out.",
            actor_user_id=current_user.get("id"),
            actor_role=current_user.get("role"),
        )
    return {"status": "ok", "message": "Successfully logged out"}
