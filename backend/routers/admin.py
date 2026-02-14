"""Admin API routes — user management and global analytics."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.user import User
from models.analysis import Analysis
from schemas import UserResponse, UserUpdate, AdminAnalytics
from services.auth import require_role

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """List all users. Admin only."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [UserResponse.model_validate(u) for u in users]


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Update a user's role. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.role:
        if data.role not in ("student", "engineer", "admin"):
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = data.role

    if data.full_name is not None:
        user.full_name = data.full_name

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Delete a user. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(user)
    db.commit()
    return {"detail": "User deleted"}


@router.get("/analytics", response_model=AdminAnalytics)
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Get system-wide analytics. Admin only."""
    total_users = db.query(User).count()
    total_analyses = db.query(Analysis).count()

    avg_row = db.query(func.avg(Analysis.health_score)).first()
    avg_score = round(avg_row[0] or 0, 1)

    # Users by role
    role_counts = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_by_role = {role: count for role, count in role_counts}

    # Recent activity
    recent = (
        db.query(Analysis)
        .join(User)
        .order_by(Analysis.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activity = [
        {
            "user": a.user.username if a.user else "Unknown",
            "title": a.title,
            "score": a.health_score,
            "date": a.created_at.isoformat() if a.created_at else "",
        }
        for a in recent
    ]

    return AdminAnalytics(
        total_users=total_users,
        total_analyses=total_analyses,
        average_score=avg_score,
        users_by_role=users_by_role,
        recent_activity=recent_activity,
    )
