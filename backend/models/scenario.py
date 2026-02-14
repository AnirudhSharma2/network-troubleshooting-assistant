"""Scenario database model – stores practice / generated scenarios."""

from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON
from database import Base


class Scenario(Base):
    """A generated or curated network troubleshooting scenario."""

    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    scenario_type = Column(String(50), nullable=False)  # routing | vlan | interface | ip
    difficulty = Column(String(20), default="medium")  # easy | medium | hard
    description = Column(Text, nullable=False)
    network_config = Column(Text, nullable=True)  # The "broken" config to troubleshoot
    expected_issues = Column(JSON, nullable=True)  # What students should find
    instructions = Column(Text, nullable=True)  # Steps for Packet Tracer lab
    created_by = Column(Integer, nullable=True)  # user_id or null for system
    created_at = Column(DateTime, server_default=func.now())
