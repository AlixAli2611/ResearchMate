from models import Paper, ProcessedPaper


def extract_key_terms(text: str, max_terms: int = 8) -> list[str]:
    """
    Extract simple keyword-style terms from the abstract.

    This prototype uses a transparent rule-based method instead of hiding the
    decision inside an LLM. This makes the processing behaviour easier to test
    and explain during demonstration.
    """
    stop_words = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "into", "using", "used", "use", "can", "has", "have", "had", "but", "not",
    "our", "their", "they", "its", "these", "those", "about", "such", "also",
    "more", "than", "which", "when", "where", "how", "what", "why", "through",
    "between", "within", "without", "based", "paper", "study", "studies",
    "article", "chapter", "section", "introduces", "defines", "discusses",
    "presents", "shows", "makes", "nature", "however", "current", "recently",
    "various", "including", "during", "past", "years", "purpose", "range",
    "main", "focus", "start", "reviewing", "developed", "designed", "guide",
    "framework", "process", "approach", "result", "results", "analysis",
    "method", "methods", "model", "models"
}

    words = text.lower().replace(".", " ").replace(",", " ").split()
    terms = []

    for word in words:
        cleaned = "".join(character for character in word if character.isalnum())

        if (
    len(cleaned) > 4
    and cleaned not in stop_words
    and not cleaned.startswith("textit")
    and cleaned not in terms
):
            terms.append(cleaned)

        if len(terms) >= max_terms:
            break

    return terms


def summarise_abstract(abstract: str, max_sentences: int = 2) -> str:
    """
    Create a short summary from the abstract.

    The summary is intentionally source-level. The system summarises each paper
    separately rather than blending findings together, which helps avoid hiding
    conflicting evidence from different sources.
    """
    sentences = [sentence.strip() for sentence in abstract.split(".") if sentence.strip()]

    if not sentences:
        return "No abstract summary available."

    return ". ".join(sentences[:max_sentences]) + "."


def process_papers(papers: list[Paper]) -> list[ProcessedPaper]:
    """
    Process retrieved papers into source-level summaries and key terms.
    """
    processed_papers = []

    for paper in papers:
        summary = summarise_abstract(paper.abstract)
        key_terms = extract_key_terms(paper.title + " " + paper.abstract)

        processed_papers.append(
            ProcessedPaper(
                title=paper.title,
                summary=summary,
                key_terms=key_terms,
                url=paper.url,
                source=paper.source,
            )
        )

    return processed_papers