from models import ResearchContext, ProcessedPaper
from agents.ranking_agent import (
    rank_papers,
    assess_evidence_consistency,
    validate_llm_ranking_output,
    calculate_relevance_score_fallback,
)


def test_rank_papers_scores_relevant_paper_higher():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=10,
    )

    relevant_paper = ProcessedPaper(
        title="AI Tutors and Learning Outcomes in Higher Education",
        summary=(
            "This paper discusses artificial intelligence tutors, course design, "
            "student learning, curriculum, and assessment."
        ),
        key_terms=["tutors", "higher", "education", "course", "curriculum", "learning"],
        paper_type="Methodology / framework paper",
        url="https://arxiv.org/relevant",
        source="arXiv",
        citation_count=None,
        publication_type=None,
    )

    less_relevant_paper = ProcessedPaper(
        title="Gamma Ray Telescope Outreach Activities",
        summary="This paper discusses public outreach activities in astronomy.",
        key_terms=["gamma", "telescope", "outreach", "astronomy"],
        paper_type="Unknown / unclear from abstract",
        url="https://arxiv.org/less-relevant",
        source="arXiv",
        citation_count=None,
        publication_type=None,
    )

    ranked = rank_papers(context, [less_relevant_paper, relevant_paper])

    assert len(ranked) == 2
    assert ranked[0].relevance_score >= ranked[1].relevance_score
    assert 0 <= ranked[0].relevance_score <= 10
    assert ranked[0].relevance_reason


def test_validate_llm_ranking_output_accepts_valid_score_breakdown():
    parsed = {
        "query_match": 3,
        "purpose_match": 2,
        "audience_match": 1,
        "paper_type_fit": 1,
        "source_completeness": 1,
        "total_score": 8,
        "explanation": (
            "This paper is useful for course design because it discusses "
            "AI tutors and learning outcomes."
        ),
    }

    score, reason = validate_llm_ranking_output(parsed)

    assert score == 8
    assert "query match 3/4" in reason
    assert "purpose match 2/3" in reason
    assert "course design" in reason


def test_validate_llm_ranking_output_rejects_invalid_total():
    parsed = {
        "query_match": 3,
        "purpose_match": 2,
        "audience_match": 1,
        "paper_type_fit": 1,
        "source_completeness": 1,
        "total_score": 10,
        "explanation": "This score total is incorrect.",
    }

    try:
        validate_llm_ranking_output(parsed)
        assert False, "Expected ValueError for invalid total score."
    except ValueError:
        assert True


def test_validate_llm_ranking_output_rejects_out_of_range_component():
    parsed = {
        "query_match": 5,
        "purpose_match": 2,
        "audience_match": 1,
        "paper_type_fit": 1,
        "source_completeness": 1,
        "total_score": 10,
        "explanation": "The query score is outside the allowed range.",
    }

    try:
        validate_llm_ranking_output(parsed)
        assert False, "Expected ValueError for out-of-range component score."
    except ValueError:
        assert True


def test_fallback_score_returns_valid_score_and_reason():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=10,
    )

    paper = ProcessedPaper(
        title="AI Tutors and Learning Outcomes in Higher Education",
        summary=(
            "This paper discusses artificial intelligence tutors, course design, "
            "student learning, curriculum, and assessment."
        ),
        key_terms=["tutors", "higher", "education", "course", "curriculum", "learning"],
        paper_type="Methodology / framework paper",
        url="https://arxiv.org/relevant",
        source="arXiv",
        citation_count=None,
        publication_type=None,
    )

    score, reason = calculate_relevance_score_fallback(context, paper)

    assert 0 <= score <= 10
    assert "Fallback score" in reason
    assert "query match" in reason
    assert "purpose match" in reason


def test_evidence_consistency_returns_contextual_note():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=3,
    )

    papers = [
        ProcessedPaper(
            title="AI Tutors in Higher Education",
            summary=(
                "This paper discusses AI tutors, course design, learning, "
                "curriculum, assessment, and education."
            ),
            key_terms=["ai", "tutors", "higher", "education", "course", "curriculum", "learning"],
            paper_type="Methodology / framework paper",
            url="https://arxiv.org/1",
            source="arXiv",
            citation_count=None,
            publication_type=None,
        ),
        ProcessedPaper(
            title="Artificial Intelligence and Student Learning",
            summary=(
                "This paper discusses education, teaching, pedagogy, "
                "learning outcomes, and students."
            ),
            key_terms=["artificial", "intelligence", "education", "students", "learning", "outcomes"],
            paper_type="Review / survey paper",
            url="https://arxiv.org/2",
            source="arXiv",
            citation_count=None,
            publication_type=None,
        ),
        ProcessedPaper(
            title="AI Literacy in Higher Education",
            summary=(
                "This paper discusses higher education, curriculum design, "
                "learning, assessment, and research."
            ),
            key_terms=["ai", "literacy", "higher", "education", "curriculum", "assessment"],
            paper_type="Methodology / framework paper",
            url="https://arxiv.org/3",
            source="arXiv",
            citation_count=None,
            publication_type=None,
        ),
    ]

    ranked = rank_papers(context, papers)
    evidence_note = assess_evidence_consistency(context, ranked)

    assert isinstance(evidence_note, str)
    assert len(evidence_note) > 20
    assert any(
        word in evidence_note.lower()
        for word in ["strong", "moderate", "weak", "limited", "mixed"]
    )


def test_fallback_sources_are_flagged_in_evidence_note():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=2,
    )

    fallback_paper = ProcessedPaper(
        title="Fallback result",
        summary="This is a fallback record used only for demonstration.",
        key_terms=["fallback", "demonstration"],
        paper_type="Unknown / unclear from abstract",
        url="https://arxiv.org/",
        source="Fallback",
        citation_count=None,
        publication_type="Fallback",
    )

    ranked = rank_papers(context, [fallback_paper])
    evidence_note = assess_evidence_consistency(context, ranked)

    assert isinstance(evidence_note, str)
    assert len(evidence_note) > 20
    assert any(
        word in evidence_note.lower()
        for word in ["fallback", "limited", "weak", "insufficient"]
    )