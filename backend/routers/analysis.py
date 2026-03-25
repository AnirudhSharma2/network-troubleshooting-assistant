"""Analysis API routes — core troubleshooting endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.analysis import Analysis
from schemas import AnalysisRequest, AnalysisResponse, AnalysisSummary, IssueDetail
from services.auth import get_current_user
from services.rule_engine.engine import rule_engine
from services.scoring import calculate_health_score
from services.analysis_assistant import build_analysis_artifacts
from services.ai.factory import get_ai_provider

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.post("", response_model=AnalysisResponse)
def run_analysis(
    data: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run a full troubleshooting analysis on submitted CLI output.

    Pipeline: Parse → Rules → Scoring → Evidence/Plan → Store
    """
    # Step 1: Rule engine analysis
    result = rule_engine.analyze(data.input_text)
    parsed_summary = result["parsed"]
    parsed_data = result["parsed_data"]
    issues = result["issues"]

    # Step 2: Health scoring
    score_result = calculate_health_score(issues)
    health_score = score_result["total_score"]

    # Step 3: Deterministic assistant artifacts
    assistant = build_analysis_artifacts(
        raw_text=data.input_text,
        parsed=parsed_data,
        issues=issues,
        score_result=score_result,
    )
    explanation = assistant["analysis_summary"]

    stored_breakdown = {
        "total_score": score_result["total_score"],
        "routing_score": score_result["routing_score"],
        "interface_score": score_result["interface_score"],
        "vlan_score": score_result["vlan_score"],
        "ip_score": score_result["ip_score"],
        "deductions": score_result["deductions"],
        "category_raw": score_result.get("category_raw", {}),
        "explanation": score_result.get("explanation", ""),
        "parsed_summary": parsed_summary,
        "evidence": assistant["evidence"],
        "fix_plan": assistant["fix_plan"],
        "insights": assistant["insights"],
        "engine_mode": assistant["engine_mode"],
    }

    # Step 4: Collect fix commands
    fix_commands = "\n\n".join(
        f"! Fix for: {iss.get('failure_type', 'unknown')} on {iss.get('interface', 'N/A')}\n{iss.get('fix_command', '')}"
        for iss in issues
        if iss.get("fix_command")
    )

    # Step 5: Store in database
    analysis = Analysis(
        user_id=current_user.id,
        title=data.title,
        input_text=data.input_text,
        input_type=data.input_type,
        issues_json=issues,
        health_score=health_score,
        score_breakdown=stored_breakdown,
        explanation=explanation,
        fix_commands=fix_commands,
        status="completed",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return AnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        title=analysis.title,
        input_type=analysis.input_type,
        issues=[IssueDetail(**iss) for iss in issues],
        health_score=health_score,
        score_breakdown=score_result,
        parsed_summary=parsed_summary,
        evidence=assistant["evidence"],
        fix_plan=assistant["fix_plan"],
        insights=assistant["insights"],
        engine_mode=assistant["engine_mode"],
        explanation=explanation,
        fix_commands=fix_commands,
        status=analysis.status,
        created_at=analysis.created_at,
    )


@router.get("", response_model=list[AnalysisSummary])
def list_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all analyses for the current user."""
    query = db.query(Analysis)

    # Non-admin users see only their own
    if current_user.role != "admin":
        query = query.filter(Analysis.user_id == current_user.id)

    analyses = query.order_by(Analysis.created_at.desc()).limit(50).all()

    return [
        AnalysisSummary(
            id=a.id,
            title=a.title,
            health_score=a.health_score,
            issue_count=len(a.issues_json) if a.issues_json else 0,
            status=a.status,
            created_at=a.created_at,
        )
        for a in analyses
    ]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific analysis by ID."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Check ownership (admin can see all)
    if current_user.role != "admin" and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    issues = analysis.issues_json or []

    return AnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        title=analysis.title,
        input_type=analysis.input_type,
        issues=[IssueDetail(**iss) for iss in issues],
        health_score=analysis.health_score or 0,
        score_breakdown=analysis.score_breakdown,
        parsed_summary=(analysis.score_breakdown or {}).get("parsed_summary"),
        evidence=(analysis.score_breakdown or {}).get("evidence"),
        fix_plan=(analysis.score_breakdown or {}).get("fix_plan", []),
        insights=(analysis.score_breakdown or {}).get("insights", []),
        engine_mode=(analysis.score_breakdown or {}).get("engine_mode", "deterministic_copilot"),
        explanation=analysis.explanation or "",
        fix_commands=analysis.fix_commands,
        status=analysis.status,
        created_at=analysis.created_at,
    )


@router.get("/{analysis_id}/learning")
def get_learning_content(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get learning content for each issue in an analysis."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if current_user.role != "admin" and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    issues = analysis.issues_json or []
    ai = get_ai_provider()

    content = []
    for issue in issues:
        learning = ai.generate_learning_content(issue)
        content.append(learning)

    return {"analysis_id": analysis_id, "learning_content": content}
