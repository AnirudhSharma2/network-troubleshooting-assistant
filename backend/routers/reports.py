"""Reports API routes — PDF generation."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from database import get_db
from models.user import User
from models.analysis import Analysis
from services.auth import get_current_user
from services.report import generate_pdf_report

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/{analysis_id}/pdf")
def download_report_pdf(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download a PDF report for an analysis."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if current_user.role != "admin" and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    analysis_data = {
        "title": analysis.title,
        "issues": analysis.issues_json or [],
        "health_score": analysis.health_score or 0,
        "score_breakdown": analysis.score_breakdown or {},
        "explanation": analysis.explanation or "",
        "fix_commands": analysis.fix_commands or "",
    }

    pdf_bytes = generate_pdf_report(analysis_data, user_name=current_user.username)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="troubleshooting_report_{analysis_id}.pdf"'
        },
    )
