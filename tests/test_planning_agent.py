from models import ResearchContext
from agents.planning_agent import create_plan


def test_create_plan_returns_research_plan():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=10,
    )

    plan = create_plan(context)

    assert plan.query == "AI tutors in higher education"
    assert plan.purpose == "course design"
    assert plan.audience_level == "masters"
    assert len(plan.steps) > 0
    assert "Retrieve academic papers" in " ".join(plan.steps)


def test_create_plan_rejects_empty_query():
    context = ResearchContext(
        query="",
        purpose="course design",
        audience_level="masters",
        requested_papers=10,
    )

    try:
        create_plan(context)
        assert False, "Expected ValueError for empty query"
    except ValueError:
        assert True