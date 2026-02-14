"""Scenario Generator API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.scenario import Scenario
from schemas import ScenarioGenerateRequest, ScenarioResponse
from services.auth import get_current_user
from services.ai.factory import get_ai_provider

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


@router.post("/generate", response_model=ScenarioResponse)
def generate_scenario(
    data: ScenarioGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a practice troubleshooting scenario."""
    ai = get_ai_provider()
    result = ai.generate_scenario(data.scenario_type, data.difficulty)

    # Store in database
    scenario = Scenario(
        title=result.get("title", "Generated Scenario"),
        scenario_type=data.scenario_type,
        difficulty=data.difficulty,
        description=result.get("description", ""),
        network_config=result.get("network_config", ""),
        expected_issues=result.get("expected_issues", []),
        instructions=result.get("instructions", ""),
        created_by=current_user.id,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    return ScenarioResponse.model_validate(scenario)


@router.get("", response_model=list[ScenarioResponse])
def list_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all available scenarios."""
    scenarios = db.query(Scenario).order_by(Scenario.created_at.desc()).limit(50).all()
    return [ScenarioResponse.model_validate(s) for s in scenarios]


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific scenario by ID."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return ScenarioResponse.model_validate(scenario)
