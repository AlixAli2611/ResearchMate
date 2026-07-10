# ResearchMate

ResearchMate is an LLM-powered academic research planning agent prototype. It receives a user’s research goal, creates a structured plan, retrieves academic sources, processes and ranks the retrieved papers, assesses the usefulness of the evidence, and saves the output in multiple formats.

This project was developed as an individual implementation based on an earlier multi-agent system design proposal. The selected domain is academic research and structured information gathering.

---

## Project Purpose

Academic research can be time-consuming because users often need to search multiple academic databases, inspect abstracts, judge relevance, and organise results before they can begin writing or designing learning materials.

ResearchMate supports this process by:

- interpreting the user’s research goal;
- creating a research plan;
- retrieving academic papers from multiple sources;
- processing each source into summaries, key terms, and paper type labels;
- ranking sources against the user’s query, purpose, and audience level;
- marking papers as recommended, caution-level, or not recommended;
- producing a cautious evidence note;
- saving results as Markdown, JSON, and SQLite records.

The system is not intended to replace academic judgement. It organises and prioritises sources so the user can review them more efficiently.

---

## Implemented Architecture

ResearchMate is implemented as a cooperating multi-agent prototype.

The current implementation includes:

- **Planning Agent**
- **Retrieval Agent**
- **Processing Agent**
- **Ranking Agent**
- **Evidence Assessment Agent**
- **Storage / Persistence Agents**

The workflow is:

```text
User research goal
↓
Planning Agent
↓
Retrieval Agent
↓
Processing Agent
↓
Ranking Agent
↓
Evidence Assessment
↓
Markdown + JSON + SQLite outputs