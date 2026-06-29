from models import Paper
from agents.processing_agent import process_papers, summarise_abstract, extract_key_terms


def test_summarise_abstract_returns_first_sentences():
    abstract = "This is the first sentence. This is the second sentence. This is the third sentence."

    summary = summarise_abstract(abstract, max_sentences=2)

    assert summary == "This is the first sentence. This is the second sentence."


def test_extract_key_terms_returns_relevant_terms():
    text = "Artificial intelligence tutors support learning and education in higher education."

    key_terms = extract_key_terms(text)

    assert "artificial" in key_terms
    assert "intelligence" in key_terms
    assert "education" in key_terms


def test_process_papers_returns_processed_papers():
    papers = [
        Paper(
            title="AI Tutors in Higher Education",
            authors=["Test Author"],
            abstract="AI tutors can support personalised learning. They may help students receive feedback.",
            url="https://arxiv.org/example",
            published="2026-01-01",
            source="arXiv",
        )
    ]

    processed = process_papers(papers)

    assert len(processed) == 1
    assert processed[0].title == "AI Tutors in Higher Education"
    assert "AI tutors can support personalised learning" in processed[0].summary
    assert len(processed[0].key_terms) > 0