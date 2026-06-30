# ai201-project4-provenance-guard

### Signal Captures

- explain what each signal captures and why you chose them
- default:
    - **LLM-based classification (Groq):** ask the model to assess whether text reads as human or AI-generated. Captures semantic and stylistic coherence holistically. - semantic

    - **Stylometric heuristics:** measurable statistical properties that differ between human and AI writing — sentence length variance, type-token ratio (vocabulary diversity), punctuation density, or average sentence complexity. AI text tends to be more uniform; human writing is more variable. Computable in pure Python. - structural

    - **potential:** word patterns?

### Cofidence Score

- must explain how you approached this:
  - return a confidence score, not just a binary label. The score should reflect genuine uncertainty — a 0.51 confidence should produce a meaningfully different transparency label than a 0.95
  - and how you tested whether your scores are meaningful

### Transparency Labels

- a typed description of all three label variants (high-confidence AI, high-confidence human, uncertain)
  - write out the exact text each one displays.
  - elcome to include a screenshot or mockup as well, but the written description is what's required

### Appeals Workflow (minimum)

- capture the creator's reasoning,
- log the appeal alongside the original decision,
- and update the content's status to "under review."
  - automated re-classification is not required

### Rate Limiting

- implement rate limiting on your submission endpoint
- document the limits you chose
  - and your reasoning for those specific values.

### Audit Log

- every attribution decision — including:
  - confidence score,
  - signals used,
  - and any appeals
- must be captured in a structured audit log
- document the log in your README (or via the GET /log output)
  - with at least 3 entries visible
