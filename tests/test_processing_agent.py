from models import Paper, ResearchContext
from agents.processing_agent import (
    summarise_abstract,
    extract_key_terms,
    classify_paper_type,
    process_paper_with_fallback,
    validate_llm_processing_output,
    process_papers,
)


def test_summarise_abstract_returns_first_sentences():
    abstract = (
        "This paper studies AI tutors in higher education. "
        "It focuses on student learning and course design. "
        "It also discusses future research."
    )

    summary = summarise_abstract(abstract)

    assert summary == (
        "This paper studies AI tutors in higher education. "
        "It focuses on student learning and course design."
    )


def test_extract_key_terms_returns_context_aware_terms():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=5,
    )

    text = (
        "AI Tutors and Learning Outcomes in Higher Education. "
        "This paper discusses artificial intelligence, student learning, "
        "course design, curriculum design, and educational technology."
    )

    key_terms = extract_key_terms(text, context)

    assert "tutors" in key_terms
    assert "education" in key_terms


def test_classify_paper_type_identifies_review():
    paper_type = classify_paper_type(
        title="A Systematic Review of AI Tutors in Higher Education",
        abstract="This systematic review synthesises studies on AI tutoring.",
        publication_type=None,
    )

    assert paper_type == "Review / survey paper"


def test_process_paper_with_fallback_returns_processed_paper():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=5,
    )

    paper = Paper(
        title="AI Tutors in Higher Education",
        authors=["Example Author"],
        abstract=(
            "This paper explores artificial intelligence tutors, "
            "student learning, and curriculum design."
        ),
        url="https://arxiv.org/example",
        published="2024-01-01",
        source="arXiv",
        citation_count=None,
        publication_type=None,
    )

    processed = process_paper_with_fallback(paper, context)

    assert processed.title == "AI Tutors in Higher Education"
    assert processed.summary
    assert len(processed.key_terms) > 0
    assert processed.paper_type


def test_validate_llm_processing_output_accepts_valid_json():
    parsed = {
        "summary": "This paper discusses AI tutors in higher education.",
        "key_terms": ["AI tutors", "higher education", "student learning"],
        "paper_type": "Review / survey paper",
    }

    summary, key_terms, paper_type = validate_llm_processing_output(parsed)

    assert summary == "This paper discusses AI tutors in higher education."
    assert key_terms == ["AI tutors", "higher education", "student learning"]
    assert paper_type == "Review / survey paper"


def test_validate_llm_processing_output_handles_invalid_paper_type():
    parsed = {
        "summary": "This paper discusses AI tutors in higher education.",
        "key_terms": ["AI tutors", "higher education", "student learning"],
        "paper_type": "Random invalid label",
    }

    summary, key_terms, paper_type = validate_llm_processing_output(parsed)

    assert summary
    assert key_terms
    assert paper_type == "Unknown / unclear from abstract"


def test_process_papers_returns_processed_papers():
    context = ResearchContext(
        query="AI tutors in higher education",
        purpose="course design",
        audience_level="masters",
        requested_papers=5,
    )

    papers = [
        Paper(
            title="AI Tutors in Higher Education",
            authors=["Example Author"],
            abstract=(
                "This paper explores artificial intelligence tutors, "
                "student learning, and curriculum design."
            ),
            url="https://arxiv.org/example",
            published="2024-01-01",
            source="arXiv",
            citation_count=None,
            publication_type=None,
        )
    ]

    processed = process_papers(papers, context)

    assert len(processed) == 1
    assert processed[0].title == "AI Tutors in Higher Education"
    assert processed[0].summary
    assert len(processed[0].key_terms) > 0
    assert processed[0].paper_type