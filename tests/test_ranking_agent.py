from models import ResearchContext, ProcessedPaper
from agents.ranking_agent import rank_papers, assess_evidence_consistency


def test_rank_papers_scores_relevant_paper_higher():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=10,
    )

    relevant_paper = ProcessedPaper(
        title="AI Tutors and Learning Outcomes in Higher Education",
        summary="This paper discusses artificial intelligence tutors, course design, student learning, curriculum, and assessment.",
        key_terms=["tutors", "higher", "education", "course", "curriculum", "learning"],
        url="https://arxiv.org/relevant",
        source="arXiv",
    )

    less_relevant_paper = ProcessedPaper(
        title="Gamma Ray Telescope Outreach Activities",
        summary="This paper discusses public outreach activities in astronomy.",
        key_terms=["gamma", "telescope", "outreach", "astronomy"],
        url="https://arxiv.org/less-relevant",
        source="arXiv",
    )

    ranked = rank_papers(context, [less_relevant_paper, relevant_paper])

    assert ranked[0].title == "AI Tutors and Learning Outcomes in Higher Education"
    assert ranked[0].relevance_score > ranked[1].relevance_score
    assert ranked[0].relevance_score <= 10
    assert "query match" in ranked[0].relevance_reason


def test_evidence_consistency_flags_strong_evidence():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=3,
    )

    papers = [
        ProcessedPaper(
            title="AI Tutors in Higher Education",
            summary="This paper discusses AI tutors, course design, learning, curriculum, assessment, and education.",
            key_terms=["ai", "tutors", "higher", "education", "course", "curriculum", "learning"],
            url="https://arxiv.org/1",
            source="arXiv",
        ),
        ProcessedPaper(
            title="Artificial Intelligence and Student Learning",
            summary="This paper discusses education, teaching, pedagogy, learning outcomes, and students.",
            key_terms=["artificial", "intelligence", "education", "students", "learning", "outcomes"],
            url="https://arxiv.org/2",
            source="arXiv",
        ),
        ProcessedPaper(
            title="AI Literacy in Higher Education",
            summary="This paper discusses higher education, curriculum design, learning, assessment, and research.",
            key_terms=["ai", "literacy", "higher", "education", "curriculum", "assessment"],
            url="https://arxiv.org/3",
            source="arXiv",
        ),
    ]

    ranked = rank_papers(context, papers)
    evidence_note = assess_evidence_consistency(context, ranked)

    assert "Evidence appears" in evidence_note
    assert "course design" in evidence_note
    assert "masters" in evidence_note