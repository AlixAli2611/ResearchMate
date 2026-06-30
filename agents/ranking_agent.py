import re

from agents.llm_utils import call_groq_json
from models import ResearchContext, ProcessedPaper, RankedPaper


PURPOSE_KEYWORDS = {
    "course design": [
        "course", "curriculum", "teaching", "learning", "assessment",
        "instruction", "education", "pedagogy", "students"
    ],
    "literature review": [
        "review", "literature", "systematic", "evidence", "studies",
        "research", "findings", "synthesis"
    ],
    "background research": [
        "overview", "background", "introduction", "evidence", "research",
        "concepts", "field", "context"
    ],
    "assignment": [
        "explain", "concept", "evidence", "examples", "research",
        "argument", "analysis"
    ],
    "personal study": [
        "overview", "introduction", "learning", "concepts", "explain",
        "understanding"
    ],
}


LEVEL_KEYWORDS = {
    "undergraduate": ["introductory", "students", "education", "learning", "overview"],
    "masters": ["advanced", "graduate", "research", "framework", "analysis", "methodology"],
    "doctoral": ["theory", "methodology", "advanced", "research", "empirical", "systematic"],
    "professional": ["practice", "implementation", "applied", "professional", "workplace"],
    "general audience": ["overview", "introduction", "explain", "accessible", "general"],
}


def normalise_text(text: str) -> set[str]:
    """
    Convert text into a set of simple lowercase words.
    """
    cleaned_text = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return {word for word in cleaned_text.split() if len(word) > 2}


def get_purpose_terms(purpose: str) -> list[str]:
    """
    Return keyword terms linked to the user's research purpose.
    """
    purpose_lower = purpose.lower()

    for key, terms in PURPOSE_KEYWORDS.items():
        if key in purpose_lower:
            return terms

    return ["research", "evidence", "learning", "analysis"]


def get_level_terms(audience_level: str) -> list[str]:
    """
    Return keyword terms linked to the user's intended audience or level.
    """
    level_lower = audience_level.lower()

    for key, terms in LEVEL_KEYWORDS.items():
        if key in level_lower:
            return terms

    return ["research", "overview", "learning"]


def calculate_paper_type_score(purpose: str, paper_type: str) -> int:
    """
    Add a small relevance boost when the paper type fits the user's purpose.

    This is the deterministic fallback paper-type scoring method.
    """
    purpose_lower = purpose.lower()
    paper_type_lower = paper_type.lower()

    if "literature review" in purpose_lower and "review" in paper_type_lower:
        return 1

    if "course design" in purpose_lower and (
        "framework" in paper_type_lower
        or "application" in paper_type_lower
        or "review" in paper_type_lower
    ):
        return 1

    if "background research" in purpose_lower and (
        "review" in paper_type_lower
        or "conceptual" in paper_type_lower
    ):
        return 1

    if "assignment" in purpose_lower and (
        "review" in paper_type_lower
        or "conceptual" in paper_type_lower
        or "empirical" in paper_type_lower
    ):
        return 1

    if "personal study" in purpose_lower and (
        "review" in paper_type_lower
        or "conceptual" in paper_type_lower
    ):
        return 1

    return 0


def calculate_relevance_score_fallback(
    context: ResearchContext,
    paper: ProcessedPaper,
) -> tuple[int, str]:
    """
    Calculate a deterministic relevance score out of 10.

    This is used if Groq/Llama ranking is unavailable or returns invalid output.
    """
    query_terms = normalise_text(context.query)
    purpose_terms = set(get_purpose_terms(context.purpose))
    level_terms = set(get_level_terms(context.audience_level))

    paper_text = " ".join(
        [
            paper.title,
            paper.summary,
            " ".join(paper.key_terms),
            paper.paper_type,
        ]
    )
    paper_terms = normalise_text(paper_text)

    query_matches = query_terms.intersection(paper_terms)
    purpose_matches = purpose_terms.intersection(paper_terms)
    level_matches = level_terms.intersection(paper_terms)

    query_score = min(len(query_matches), 4)
    purpose_score = min(len(purpose_matches), 3)
    audience_score = min(len(level_matches), 1)
    paper_type_score = calculate_paper_type_score(context.purpose, paper.paper_type)
    source_score = 1 if paper.url and paper.source.lower() != "fallback" else 0

    total_score = query_score + purpose_score + audience_score + paper_type_score + source_score

    reason_parts = [
        f"query match {query_score}/4",
        f"purpose match {purpose_score}/3",
        f"audience match {audience_score}/1",
        f"paper type fit {paper_type_score}/1",
        f"source completeness {source_score}/1",
    ]

    reason = "Fallback score based on " + ", ".join(reason_parts) + "."

    return total_score, reason


def validate_llm_ranking_output(parsed: dict) -> tuple[int, str]:
    """
    Validate Groq/Llama ranking output before using it.

    The LLM must apply the scoring rubric and return a score out of 10.
    """
    required_fields = {
        "query_match": (0, 4),
        "purpose_match": (0, 3),
        "audience_match": (0, 1),
        "paper_type_fit": (0, 1),
        "source_completeness": (0, 1),
    }

    component_scores = {}

    for field, (minimum, maximum) in required_fields.items():
        value = parsed.get(field)

        if not isinstance(value, int):
            raise ValueError(f"LLM ranking output has invalid value for {field}.")

        if value < minimum or value > maximum:
            raise ValueError(f"LLM ranking output score for {field} is outside allowed range.")

        component_scores[field] = value

    calculated_total = sum(component_scores.values())
    total_score = parsed.get("total_score")

    if not isinstance(total_score, int):
        raise ValueError("LLM ranking output has invalid total_score.")

    if total_score != calculated_total:
        raise ValueError("LLM ranking total_score does not match component scores.")

    if total_score < 0 or total_score > 10:
        raise ValueError("LLM ranking total_score is outside 0-10 range.")

    explanation = parsed.get("explanation")

    if not isinstance(explanation, str) or not explanation.strip():
        raise ValueError("LLM ranking output is missing a valid explanation.")

    reason = (
        "LLM rubric score based on "
        f"query match {component_scores['query_match']}/4, "
        f"purpose match {component_scores['purpose_match']}/3, "
        f"audience match {component_scores['audience_match']}/1, "
        f"paper type fit {component_scores['paper_type_fit']}/1, "
        f"source completeness {component_scores['source_completeness']}/1. "
        f"{explanation.strip()}"
    )

    return total_score, reason


def calculate_relevance_score_with_llm(
    context: ResearchContext,
    paper: ProcessedPaper,
) -> tuple[int, str]:
    """
    Use Groq/Llama to apply the ResearchMate ranking rubric.

    The LLM does not invent a free-form score. It receives the scoring rules and
    must return a structured score breakdown that Python validates.
    """
    system_message = (
        "You are the Ranking Agent in ResearchMate, an academic research assistant. "
        "Apply the provided scoring rubric exactly. Return only valid JSON. "
        "Do not include markdown or extra commentary."
    )

    user_message = f"""
Rank this processed academic source against the user's research goal.

User context:
- Topic/query: {context.query}
- Purpose: {context.purpose}
- Audience/level: {context.audience_level}

Processed paper:
- Title: {paper.title}
- Summary: {paper.summary}
- Key terms: {", ".join(paper.key_terms)}
- Paper type: {paper.paper_type}
- Source: {paper.source}
- Citation count: {paper.citation_count if paper.citation_count is not None else "Not available"}
- Publication type metadata: {paper.publication_type or "Not available"}
- URL: {paper.url}

Scoring rubric:
- query_match: 0 to 4 points. Score how directly the paper matches the user's topic/query.
- purpose_match: 0 to 3 points. Score how useful the paper is for the user's stated purpose.
- audience_match: 0 to 1 point. Score whether the paper seems appropriate for the audience/level.
- paper_type_fit: 0 to 1 point. Score whether the paper type fits the purpose.
- source_completeness: 0 to 1 point. Give 1 if source metadata and URL are usable and this is not a fallback record; otherwise 0.
- total_score must equal the sum of the component scores and must be between 0 and 10.

Rules:
- Use only the processed paper information provided.
- Do not invent full-text findings.
- Be strict but fair.
- If information is unclear, give a lower score for the affected category.
- The explanation should be 1 to 2 sentences and should mention the user's purpose.

Return only valid JSON in this exact structure:
{{
  "query_match": 0,
  "purpose_match": 0,
  "audience_match": 0,
  "paper_type_fit": 0,
  "source_completeness": 0,
  "total_score": 0,
  "explanation": "brief explanation"
}}
"""

    parsed = call_groq_json(
        system_message=system_message,
        user_message=user_message,
        temperature=0.1,
    )

    return validate_llm_ranking_output(parsed)


def calculate_relevance_score(
    context: ResearchContext,
    paper: ProcessedPaper,
) -> tuple[int, str]:
    """
    Calculate relevance using Groq/Llama first, with deterministic fallback.

    This keeps the ranking agent LLM-powered while preserving reproducibility
    if the API key is missing, the service fails, or the JSON is invalid.
    """
    try:
        return calculate_relevance_score_with_llm(context, paper)
    except Exception as error:
        print(f"LLM ranking unavailable for '{paper.title}': {error}")
        print("Using deterministic fallback ranking for this paper.")
        return calculate_relevance_score_fallback(context, paper)


def rank_papers(
    context: ResearchContext,
    processed_papers: list[ProcessedPaper],
) -> list[RankedPaper]:
    """
    Rank processed papers using Groq/Llama rubric-based scoring where available,
    with deterministic fallback scoring.
    """
    ranked_papers = []

    for paper in processed_papers:
        score, reason = calculate_relevance_score(context, paper)

        ranked_papers.append(
            RankedPaper(
                title=paper.title,
                summary=paper.summary,
                key_terms=paper.key_terms,
                paper_type=paper.paper_type,
                url=paper.url,
                source=paper.source,
                citation_count=paper.citation_count,
                publication_type=paper.publication_type,
                relevance_score=score,
                relevance_reason=reason,
            )
        )

    return sorted(
        ranked_papers,
        key=lambda paper: paper.relevance_score,
        reverse=True,
    )


def assess_evidence_consistency_fallback(
    context: ResearchContext,
    ranked_papers: list[RankedPaper],
) -> str:
    """
    Provide a deterministic evidence note when Groq/Llama is unavailable.
    """
    if not ranked_papers:
        return (
            "No evidence could be assessed because no papers were retrieved. "
            "The user should broaden the search or try a different query."
        )

    fallback_sources = [
        paper for paper in ranked_papers
        if paper.source.lower() == "fallback"
    ]

    if fallback_sources:
        return (
            "Evidence is limited because one or more retrieved records are fallback "
            "records rather than live academic sources. The output should be treated "
            "as a demonstration of the pipeline, not as a reliable research briefing."
        )

    strong_papers = [
        paper for paper in ranked_papers
        if paper.relevance_score >= 7
    ]

    moderate_papers = [
        paper for paper in ranked_papers
        if 4 <= paper.relevance_score < 7
    ]

    if len(strong_papers) >= 3:
        return (
            f"Evidence appears strong for the purpose '{context.purpose}' at the "
            f"'{context.audience_level}' level because several retrieved papers "
            "scored highly against the query, purpose, audience, paper type, and source criteria. "
            "The user should still read the original papers before making academic claims."
        )

    if strong_papers or len(moderate_papers) >= 3:
        return (
            f"Evidence appears moderately useful for the purpose '{context.purpose}' "
            f"at the '{context.audience_level}' level. Some sources are relevant, "
            "but the user should review the original papers and consider additional "
            "searches before drawing strong conclusions."
        )

    return (
        f"Evidence appears weak or mixed for the purpose '{context.purpose}' at the "
        f"'{context.audience_level}' level. The retrieved papers may not be closely "
        "aligned with the user's research goal, so the query should be refined."
    )


def assess_evidence_consistency_with_llm(
    context: ResearchContext,
    ranked_papers: list[RankedPaper],
) -> str:
    """
    Use Groq/Llama to write a cautious evidence assessment for the source set.
    """
    system_message = (
        "You are the Evidence Assessment Agent in ResearchMate. You assess the "
        "retrieved source set cautiously. Return only valid JSON. Do not include "
        "markdown or extra commentary."
    )

    paper_summaries = []

    for index, paper in enumerate(ranked_papers, start=1):
        paper_summaries.append(
            {
                "rank": index,
                "title": paper.title,
                "score": paper.relevance_score,
                "paper_type": paper.paper_type,
                "source": paper.source,
                "summary": paper.summary,
                "key_terms": paper.key_terms,
            }
        )

    user_message = f"""
Assess the usefulness of this ranked source set for the user's research goal.

User context:
- Topic/query: {context.query}
- Purpose: {context.purpose}
- Audience/level: {context.audience_level}
- Requested papers: {context.requested_papers}

Ranked papers:
{paper_summaries}

Rules:
- Do not claim that the full papers have been read.
- Do not invent findings beyond the summaries provided.
- Be cautious and mention when evidence is limited, mixed, or based mainly on abstracts.
- Mention whether the source set seems strong, moderate, weak, limited, or mixed for the user's purpose.
- Keep the note to 2 to 4 sentences.

Return only valid JSON in this exact structure:
{{
  "evidence_note": "cautious evidence assessment"
}}
"""

    parsed = call_groq_json(
        system_message=system_message,
        user_message=user_message,
        temperature=0.2,
    )

    evidence_note = parsed.get("evidence_note")

    if not isinstance(evidence_note, str) or not evidence_note.strip():
        raise ValueError("LLM evidence assessment did not return a valid evidence_note.")

    return evidence_note.strip()


def assess_evidence_consistency(
    context: ResearchContext,
    ranked_papers: list[RankedPaper],
) -> str:
    """
    Assess the ranked source set using Groq/Llama first, with fallback.
    """
    try:
        return assess_evidence_consistency_with_llm(context, ranked_papers)
    except Exception as error:
        print(f"LLM evidence assessment unavailable: {error}")
        print("Using deterministic fallback evidence assessment.")
        return assess_evidence_consistency_fallback(context, ranked_papers)