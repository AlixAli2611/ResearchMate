import sqlite3
from pathlib import Path

from models import ResearchContext, ResearchPlan, RankedPaper


def initialise_database(db_path: str = "outputs/researchmate.db") -> str:
    """
    Create the SQLite database and required tables if they do not already exist.
    """
    database_file = Path(db_path)
    database_file.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_file)
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS research_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            purpose TEXT NOT NULL,
            audience_level TEXT NOT NULL,
            requested_papers INTEGER NOT NULL,
            retrieval_note TEXT,
            evidence_note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS research_plan_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            step_text TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES research_runs(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ranked_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            rank_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            key_terms TEXT,
            paper_type TEXT,
            source TEXT,
            url TEXT,
            citation_count INTEGER,
            publication_type TEXT,
            relevance_score INTEGER,
            relevance_reason TEXT,
            recommendation_status TEXT,
            FOREIGN KEY (run_id) REFERENCES research_runs(id)
        )
        """
    )

    connection.commit()
    connection.close()

    return str(database_file)


def save_run_to_database(
    context: ResearchContext,
    plan: ResearchPlan,
    ranked_papers: list[RankedPaper],
    retrieval_note: str,
    evidence_note: str,
    db_path: str = "outputs/researchmate.db",
) -> str:
    """
    Save a complete ResearchMate run to SQLite.

    This provides persistent structured storage in addition to Markdown and JSON
    exports.
    """
    database_file = initialise_database(db_path)

    connection = sqlite3.connect(database_file)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO research_runs (
            query,
            purpose,
            audience_level,
            requested_papers,
            retrieval_note,
            evidence_note
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            context.query,
            context.purpose,
            context.audience_level,
            context.requested_papers,
            retrieval_note,
            evidence_note,
        ),
    )

    run_id = cursor.lastrowid

    for step_number, step_text in enumerate(plan.steps, start=1):
        cursor.execute(
            """
            INSERT INTO research_plan_steps (
                run_id,
                step_number,
                step_text
            )
            VALUES (?, ?, ?)
            """,
            (
                run_id,
                step_number,
                step_text,
            ),
        )

    for rank_number, paper in enumerate(ranked_papers, start=1):
        cursor.execute(
            """
            INSERT INTO ranked_papers (
                run_id,
                rank_number,
                title,
                summary,
                key_terms,
                paper_type,
                source,
                url,
                citation_count,
                publication_type,
                relevance_score,
                relevance_reason,
                recommendation_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank_number,
                paper.title,
                paper.summary,
                ", ".join(paper.key_terms),
                paper.paper_type,
                paper.source,
                paper.url,
                paper.citation_count,
                paper.publication_type,
                paper.relevance_score,
                paper.relevance_reason,
                paper.recommendation_status,
            ),
        )

    connection.commit()
    connection.close()

    return database_file