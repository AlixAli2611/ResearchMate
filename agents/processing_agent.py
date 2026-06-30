from agents.llm_utils import call_groq_json
from models import Paper, ProcessedPaper, ResearchContext


VALID_PAPER_TYPES = {
    "Review / survey paper",
    "Experimental / empirical study",
    "Methodology / framework paper",
    "Application / case study",
    "Theoretical / conceptual paper",
    "Unknown / unclear from abstract",
}


def summarise_abstract(abstract: str, max_sentences: int = 2) -> str:
    """
    Create a short source-level summary from a paper abstract.

    This is the deterministic fallback summary method. Groq/Llama is used first
    when available, but this fallback keeps the system reproducible and testable.
    """
    if not abstract or not abstract.strip():
        return "No abstract available."

    sentences = [
        sentence.strip()
        for sentence in abstract.replace("\n", " ").split(".")
        if sentence.strip()
    ]

    selected_sentences = sentences[:max_sentences]

    if not selected_sentences:
        return abstract.strip()

    return ". ".join(selected_sentences) + "."


def get_context_terms(context: ResearchContext) -> list[str]:
    """
    Extract priority terms from the user's research context.

    These terms help the fallback Processing Agent identify keywords connected
    to the user's actual research goal.
    """
    context_text = f"{context.query} {context.purpose} {context.audience_level}".lower()

    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "into", "about",
        "course", "design", "literature", "review", "background", "research",
        "assignment", "personal", "study", "masters", "undergraduate", "doctoral",
        "professional", "general", "audience", "level", "effects", "effect",
    }

    terms = []

    for raw_word in context_text.split():
        cleaned = "".join(character for character in raw_word if character.isalnum())

        if len(cleaned) > 2 and cleaned not in stop_words and cleaned not in terms:
            terms.append(cleaned)

    return terms


def extract_key_terms(
    text: str,
    context: ResearchContext,
    max_terms: int = 8,
) -> list[str]:
    """
    Extract context-aware key terms as a deterministic fallback.

    The fallback prioritises terms connected to the user's query, purpose, and
    audience, then adds distinctive terms from the paper text.
    """
    if not text or not text.strip():
        return []

    text_lower = text.lower()

    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
        "into", "using", "used", "uses", "use", "can", "has", "have", "had", "but",
        "not", "our", "their", "they", "its", "these", "those", "about", "such",
        "also", "more", "than", "which", "when", "where", "how", "what", "why",
        "through", "between", "within", "without", "based", "paper", "study",
        "studies", "article", "chapter", "section", "introduces", "defines",
        "discusses", "presents", "shows", "makes", "nature", "however", "current",
        "recent", "recently", "various", "including", "during", "past", "years",
        "purpose", "range", "main", "focus", "start", "reviewing", "developed",
        "designed", "guide", "result", "results", "analysis", "method", "methods",
        "model", "models", "approach", "approaches", "system", "systems",
        "research", "findings", "important", "different", "provide", "provides",
        "provided", "across", "among", "towards", "toward", "therefore", "related",
        "new", "one", "two", "three", "first", "second", "effect", "effects",
    }

    key_terms = []

    # 1. Prioritise terms from the user's research context if they appear in the paper.
    for term in get_context_terms(context):
        if term in text_lower and term not in key_terms:
            key_terms.append(term)

        if len(key_terms) >= max_terms:
            return key_terms

    # 2. Fall back to distinctive individual words from the paper.
    words = []

    for raw_word in text_lower.split():
        cleaned = "".join(character for character in raw_word if character.isalnum())

        if (
            len(cleaned) > 4
            and cleaned not in stop_words
            and not cleaned.startswith("textit")
            and cleaned not in words
        ):
            words.append(cleaned)

    for word in words:
        if word not in key_terms:
            key_terms.append(word)

        if len(key_terms) >= max_terms:
            break

    return key_terms


def classify_paper_type(title: str, abstract: str, publication_type: str | None = None) -> str:
    """
    Classify paper type as a deterministic fallback.

    This is used if Groq/Llama is unavailable or returns invalid output.
    """
    combined_text = f"{publication_type or ''} {title} {abstract}".lower()

    if any(term in combined_text for term in ["systematic review", "literature review", "survey", "review paper"]):
        return "Review / survey paper"

    if any(term in combined_text for term in ["experiment", "experimental", "participants", "trial", "dataset", "results", "empirical", "evaluation"]):
        return "Experimental / empirical study"

    if any(term in combined_text for term in ["framework", "method", "methodology", "approach", "model", "pipeline", "architecture"]):
        return "Methodology / framework paper"

    if any(term in combined_text for term in ["case study", "implementation", "deployment", "applied", "application"]):
        return "Application / case study"

    if any(term in combined_text for term in ["conceptual", "theory", "perspective", "discussion", "ethical", "philosophy"]):
        return "Theoretical / conceptual paper"

    return "Unknown / unclear from abstract"


def process_paper_with_fallback(
    paper: Paper,
    context: ResearchContext,
) -> ProcessedPaper:
    """
    Process one paper using deterministic fallback methods.
    """
    paper_text = paper.title + " " + paper.abstract

    summary = summarise_abstract(paper.abstract)
    key_terms = extract_key_terms(paper_text, context)
    paper_type = classify_paper_type(
        title=paper.title,
        abstract=paper.abstract,
        publication_type=paper.publication_type,
    )

    return ProcessedPaper(
        title=paper.title,
        summary=summary,
        key_terms=key_terms,
        paper_type=paper_type,
        url=paper.url,
        source=paper.source,
        citation_count=paper.citation_count,
        publication_type=paper.publication_type,
    )


def validate_llm_processing_output(parsed: dict) -> tuple[str, list[str], str]:
    """
    Validate Groq/Llama processing output before using it.

    This prevents invalid or messy LLM output from breaking the system.
    """
    summary = parsed.get("summary")
    key_terms = parsed.get("key_terms")
    paper_type = parsed.get("paper_type")

    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("LLM processing output is missing a valid summary.")

    if not isinstance(key_terms, list) or not key_terms:
        raise ValueError("LLM processing output is missing valid key terms.")

    cleaned_key_terms = []

    for term in key_terms:
        cleaned_term = str(term).strip()

        if cleaned_term and cleaned_term not in cleaned_key_terms:
            cleaned_key_terms.append(cleaned_term)

    if not cleaned_key_terms:
        raise ValueError("LLM processing output returned empty key terms.")

    if not isinstance(paper_type, str) or paper_type not in VALID_PAPER_TYPES:
        paper_type = "Unknown / unclear from abstract"

    return summary.strip(), cleaned_key_terms[:8], paper_type


def process_paper_with_llm(
    paper: Paper,
    context: ResearchContext,
) -> ProcessedPaper:
    """
    Use Groq/Llama to process one retrieved paper.

    The LLM is given clear rules and must return structured JSON. It may only
    use the user context and the provided paper metadata/abstract.
    """
    system_message = (
        "You are the Processing Agent in ResearchMate, an academic research "
        "assistant. Process only the paper provided. Return only valid JSON. "
        "Do not include markdown or extra commentary. Do not invent information."
    )

    user_message = f"""
Process this retrieved academic source for the user's research goal.

User context:
- Topic/query: {context.query}
- Purpose: {context.purpose}
- Audience/level: {context.audience_level}

Paper metadata:
- Title: {paper.title}
- Authors: {", ".join(paper.authors) if paper.authors else "Not available"}
- Source: {paper.source}
- Published/year: {paper.published or "Not available"}
- Citation count: {paper.citation_count if paper.citation_count is not None else "Not available"}
- Publication type metadata: {paper.publication_type or "Not available"}
- URL: {paper.url}

Abstract:
{paper.abstract}

Rules:
- Summarise only what is supported by the title, abstract, and metadata.
- Do not invent findings, methods, samples, or claims not present in the abstract.
- Make the summary useful for the user's purpose and audience level.
- Extract 5 to 8 key terms that connect the paper to the user's query and purpose.
- Classify the paper using exactly one of these labels:
  - Review / survey paper
  - Experimental / empirical study
  - Methodology / framework paper
  - Application / case study
  - Theoretical / conceptual paper
  - Unknown / unclear from abstract
- If the abstract is missing or too vague, say this clearly in the summary and use "Unknown / unclear from abstract" when appropriate.

Return only valid JSON in this exact structure:
{{
  "summary": "2 to 3 sentence source-level summary",
  "key_terms": ["term 1", "term 2", "term 3"],
  "paper_type": "one allowed paper type label"
}}
"""

    parsed = call_groq_json(
        system_message=system_message,
        user_message=user_message,
        temperature=0.2,
    )

    summary, key_terms, paper_type = validate_llm_processing_output(parsed)

    return ProcessedPaper(
        title=paper.title,
        summary=summary,
        key_terms=key_terms,
        paper_type=paper_type,
        url=paper.url,
        source=paper.source,
        citation_count=paper.citation_count,
        publication_type=paper.publication_type,
    )


def process_papers(
    papers: list[Paper],
    context: ResearchContext,
) -> list[ProcessedPaper]:
    """
    Process retrieved papers into source-level summaries, context-aware key terms,
    and paper type labels.

    The Processing Agent first attempts Groq/Llama processing. If the LLM call
    fails or returns invalid JSON, it falls back to deterministic processing for
    that paper.
    """
    processed_papers = []

    for paper in papers:
        try:
            processed_paper = process_paper_with_llm(paper, context)
        except Exception as error:
            print(f"LLM processing unavailable for '{paper.title}': {error}")
            print("Using deterministic fallback processing for this paper.")
            processed_paper = process_paper_with_fallback(paper, context)

        processed_papers.append(processed_paper)

    return processed_papers