from models import ResearchContext, ResearchPlan, RankedPaper
from agents.storage_agent import save_markdown_report, save_json_results


def test_save_markdown_report_creates_file(tmp_path):
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=1,
    )

    plan = ResearchPlan(
        query=context.query,
        purpose=context.purpose,
        audience_level=context.audience_level,
        steps=["Retrieve papers.", "Rank papers.", "Save report."],
    )

    ranked_papers = [
        RankedPaper(
            title="AI Tutors in Higher Education",
            summary="This paper discusses AI tutors and higher education.",
            key_terms=["ai", "tutors", "higher", "education"],
            url="https://arxiv.org/example",
            source="arXiv",
            relevance_score=8,
            relevance_reason="Score based on query, purpose, audience, and source completeness.",
        )
    ]

    output_file = tmp_path / "test_report.md"

    saved_path = save_markdown_report(
        context=context,
        plan=plan,
        ranked_papers=ranked_papers,
        retrieval_note="Retrieved requested papers.",
        evidence_note="Evidence appears useful.",
        output_path=str(output_file),
    )

    assert output_file.exists()
    assert saved_path == str(output_file)

    content = output_file.read_text(encoding="utf-8")
    assert "ResearchMate Research Briefing" in content
    assert "AI tutors in higher education" in content
    assert "Evidence appears useful" in content


def test_save_json_results_creates_file(tmp_path):
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=1,
    )

    plan = ResearchPlan(
        query=context.query,
        purpose=context.purpose,
        audience_level=context.audience_level,
        steps=["Retrieve papers.", "Rank papers.", "Save report."],
    )

    ranked_papers = [
        RankedPaper(
            title="AI Tutors in Higher Education",
            summary="This paper discusses AI tutors and higher education.",
            key_terms=["ai", "tutors", "higher", "education"],
            url="https://arxiv.org/example",
            source="arXiv",
            relevance_score=8,
            relevance_reason="Score based on query, purpose, audience, and source completeness.",
        )
    ]

    output_file = tmp_path / "test_results.json"

    saved_path = save_json_results(
        context=context,
        plan=plan,
        ranked_papers=ranked_papers,
        retrieval_note="Retrieved requested papers.",
        evidence_note="Evidence appears useful.",
        output_path=str(output_file),
    )

    assert output_file.exists()
    assert saved_path == str(output_file)

    content = output_file.read_text(encoding="utf-8")
    assert "AI tutors in higher education" in content
    assert "ranked_papers" in content
    assert "Evidence appears useful" in content