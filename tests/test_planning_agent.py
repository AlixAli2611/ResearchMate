import pytest

from models import ResearchContext, ResearchPlan
from agents.planning_agent import create_plan, create_fallback_plan


def test_create_plan_returns_research_plan():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=10,
    )

    plan = create_plan(context)

    assert isinstance(plan, ResearchPlan)
    assert plan.query == "AI tutors in higher education"
    assert plan.purpose == "course design"
    assert plan.audience_level == "masters"
    assert len(plan.steps) > 0
    assert "Planning mode:" in plan.steps[0]


def test_fallback_plan_contains_core_pipeline_steps():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=10,
    )

    steps = create_fallback_plan(context)
    joined_steps = " ".join(steps).lower()

    assert "retrieve" in joined_steps
    assert "process" in joined_steps
    assert "rank" in joined_steps
    assert "save" in joined_steps
    assert "semantic scholar" in joined_steps


def test_create_plan_rejects_empty_query():
    context = ResearchContext(
        query="",
        purpose="course design",
        audience_level="masters",
        requested_papers=10,
    )

    with pytest.raises(ValueError):
        create_plan(context)