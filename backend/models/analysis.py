"""Analysis database model – stores troubleshooting results."""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from database import Base


class Analysis(Base):
    """Stores a single network troubleshooting analysis run."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False, default="Untitled Analysis")
    input_text = Column(Text, nullable=False)  # Raw CLI / config input
    input_type = Column(String(50), default="cli_output")  # cli_output | running_config | mixed
    issues_json = Column(JSON, nullable=True)  # List of detected issues
    health_score = Column(Float, nullable=True)  # 0–100
    score_breakdown = Column(JSON, nullable=True)  # Detailed scoring breakdown
    explanation = Column(Text, nullable=True)  # AI-generated explanation
    fix_commands = Column(Text, nullable=True)  # Recommended CLI commands
    status = Column(String(20), default="completed")  # pending | completed | error
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="analyses")
