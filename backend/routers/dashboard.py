"""Dashboard API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.user import User
from models.analysis import Analysis
from schemas import DashboardResponse, AnalysisSummary
from services.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard data for the current user."""
    query = db.query(Analysis)
    if current_user.role != "admin":
        query = query.filter(Analysis.user_id == current_user.id)

    # Total analyses
    total = query.count()

    # Average health score
    avg_score_row = query.with_entities(func.avg(Analysis.health_score)).first()
    avg_score = round(avg_score_row[0] or 100, 1)

    # Recent analyses
    recent = query.order_by(Analysis.created_at.desc()).limit(5).all()
    recent_summaries = [
        AnalysisSummary(
            id=a.id,
            title=a.title,
            health_score=a.health_score,
            issue_count=len(a.issues_json) if a.issues_json else 0,
            status=a.status,
            created_at=a.created_at,
        )
        for a in recent
    ]

    # Error summary — count by failure type across all analyses
    error_summary: dict[str, int] = {}
    all_analyses = query.all()
    for a in all_analyses:
        if a.issues_json:
            for issue in a.issues_json:
                ftype = issue.get("failure_type", "unknown")
                error_summary[ftype] = error_summary.get(ftype, 0) + 1

    # Health trend (last 10 analyses by date)
    trend_analyses = query.order_by(Analysis.created_at.desc()).limit(10).all()
    health_trend = [
        {
            "date": a.created_at.isoformat() if a.created_at else "",
            "score": a.health_score or 0,
            "title": a.title,
        }
        for a in reversed(trend_analyses)
    ]

    return DashboardResponse(
        total_analyses=total,
        average_health_score=avg_score,
        recent_analyses=recent_summaries,
        error_summary=error_summary,
        health_trend=health_trend,
    )
