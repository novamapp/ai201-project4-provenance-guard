# Provenance Guard — README.md

Provenance Guard is a forensic linguistic analysis platform designed to track, evaluate, and verify the structural and semantic integrity of creative writing and poetry. By pairing heavy heuristic statistical calculations with Large Language Model context engines, the platform delivers verifiable, multivariant attribution scoring via a lightweight, async-driven Flask web portal.

---

## Architecture Overview

```
                  [ POST /submit ]
                         │
                         ▼
               < Flask-Limiter Guard >
                         │
                         ▼ (Allowed)
              ▲ Async Execution Pool ▲
             ╱ Unpacks Base Payload   ╲
            ╱                           ╲
           ▼                             ▼
   ┌──────────────────────────┐   ┌──────────────────────────┐
   │    INPUT DATA PAYLOAD    │   │    INPUT DATA PAYLOAD    │
   │ { text, content_id,      │   │ { text, content_id,      │
   │   creator_id }           │   │   creator_id }           │
   └────────────┬─────────────┘   └────────────┬─────────────┘
                │                              │
                ▼                              ▼
   ┌──────────────────────────┐   ┌──────────────────────────┐
   │   Signal 1: LLM Engine   │   │ Signal 2: Stylometrics   │
   │ (llama-3.3-70b-versatile)│   │ (Custom Python Scripts)  │
   │ ➔ Semantic Clichés       │   │ ➔ TTR, Punctuation, Lines│
   │ OUT: {human/AI_likely}   │   │ OUT: {human/AI_likely}   │
   └────────────┬─────────────┘   └────────────┬─────────────┘
                │                              │
                └──────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │      INPUT: Scores Array      │
               │ [ {sig1...}, {sig2...} ]      │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │  Confidence Matrix Aggregator │
               │ • Heavy human_likely weight   │
               │ • Condenses & Normalizes [0-1]│
               │ OUT: {content_id, confidence} │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │ INPUT: Normalized Conf. Score │
               └───────────────┬───────────────┘
                               │
                               ▼
                    < Score Scale Mapping >
                    ╱          │          ╲
        [0.0 - 0.4)╱  [0.4 - 0.7]  ╲(0.7 - 1.0]
                  ╱            │            ╲
                 ▼             ▼             ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │ likely_human │ │  uncertain   │ │  likely_ai   │
   │ "Highly      │ │ "Source of   │ │ "Highly      │
   │ likely       │ │  work is     │ │  likely      │
   │ human-made"  │ │  uncertain"  │ │  AI-gen"     │
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
           ┌────────────────────────────────┐
           │   INPUT STRUCTURE TO PERSIST   │
           └───────────────┬────────────────┘
                           │
                           ▼
           ┌────────────────────────────────┐
           │       Audit Log Engine         │
           │ Saves JSON database record:    │
           │ { timestamp, text, creator_id, │
           │   content_id, confidence,      │
           │   attribution, appeals: [] }   │
           └───────────────┬────────────────┘
                           │
                           ▼
           ┌────────────────────────────────┐
           │  API Client Response Payload   │
           │ • Returns result_id & label    │
           │ • Offers Appeal route if AI    │
           └───────────────┬────────────────┘
                           │
             (If attribution == 'likely_ai')
                           │ . . . . . . . . . . . . . . . .
                           ▼                               :
                    [ POST /appeal ]                       :
                           │                               :
                           ▼                               :
           ┌────────────────────────────────┐              :
           │    INPUT SIGNATURE REQUIRED    │              :
           │ { content_id,                  │              : [ MONITORING HOOKS ]
           │   creator_reasoning }          │              :
           └───────────────┬────────────────┘              :  ┌──────────────────┐
                           │                               :  │     GET /log     │
                           ▼                               :  │ (Yields last log)│
           ┌────────────────────────────────┐              :  └──────────────────┘
           │     State Mutation Engine      │              :
           │ • Set attribution to           │              :  ┌──────────────────┐
           │   'under_review'               │              :  │ GET /logs?count= │
           └───────────────┬────────────────┘              :  │ (Yields N logs)  │
                           │                               :  └──────────────────┘
                           ▼                               :
           ┌────────────────────────────────┐              :
           │     Append to appeals Array    │<..............
           │ ➔ Reviewer: 'pending'          │
           │ ➔ Inspector: View poem text    │
           └────────────────────────────────┘

```

Link to Drawio Flowchart: [here](utils/workflow.drawio)

---

## Detection Signals

### Signal Captures

The platform leverages an asynchronous dual-engine ensemble process to evaluate candidate texts against distinct layers of linguistic expression:

* **Signal 1: LLM Semantic Engine (`llama-3.3-70b-versatile`):** This signal holistically inspects macro-level semantic qualities. It flags abstract statistical markers, structural cliches, predictable metaphors, and unnaturally rigid rhyme meters that fail to implement natural human imperfections, such as intentional slant rhymes.
* **Signal 2: Stylometric Heuristic Engine (Pure Python):** Operating strictly on raw layout mathematics from scratch, this script avoids external NLP models to compute precise structural dimensions. It assesses the **Type-Token Ratio (TTR)** to gauge lexical richness, measures **punctuation density** to capture predictable syntactic pacing, and calculates **line-length standard deviation** to reveal structural stiffness versus human pacing.
* **Future Potential (N-Gram Word Patterns):** An additional localized model could look for historical probability distributions of multi-word sequences to identify common token chains favored by generative networks.

---

## Confidence Score

Rather than deploying a simplistic binary classifier, the platform balances individual probabilities into a calibrated composite value bounded between `0.0` and `1.0`.

### Scoring Aggregation

The matrix aggregator parses the distinct signal arrays via parallel execution threads managed by a `ThreadPoolExecutor`. To protect against false positives, the mathematical aggregation assigns a heavier internal weight to human validation thresholds, computing the aggregate score directly from the normalized composite values of `AI_likely`.

### Empirical Validation

To verify whether the engine provides meaningful distributional divergence, testing scenarios were executed against polar data sets. Stiff, repetitive texts constructed with artificial line boundaries and rigid formatting over-indexed on the stylometric matrix to yield a high-confidence AI rating (`> 0.75`), while text utilizing fluid line variance and unique vocabularies safely localized below the threshold.

---

## Transparency Labels

The interface provides immediate transparency classifications mapped to explicit score boundaries to account for contextual uncertainty:

* **High-Confidence Human Result (`0.0 <= score < 0.4`):** Displays the label string:
> *"It is highly likely that this work was created by a human."*


* **Uncertain Result (`0.4 <= score <= 0.7`):** Displays the label string:
> *"Source of work is uncertain."*


* **High-Confidence AI Result (`0.7 < score <= 1.0`):** Displays the label string:
> *"It is highly likely that this work was generated by AI."*



---

## Appeals Workflow

When a submission yields an explicit high-confidence AI result, the system unlocks a glassmorphic front-end card enabling the creator to dispute the machine categorization.

1. **Context Collection:** The creator submits a text string outlining their formal reasoning or layout processes.
2. **State Mutation:** The backend maps the unique `content_id`, moves the record's root attribution state to `under_review`, and locks further duplicate appeals.
3. **Persistence Logging:** The record is updated inside the localized system repository to preserve historical metrics while registering a `pending` state marker for human verification teams.

---

## Known Limitations

* **Short-Form / Minimalist Submissions:** The native stylometric heuristic framework requires sufficient linguistic context to build its calculations. For short poems consisting of fewer than three lines or minimal word counts, the line-length standard deviation and Type-Token Ratio become statistically skewed, occasionally causing human poetry to register false positives or trigger an `uncertain` label.

* **Well engineered generated content:** The LLM signal will tend towards a likely human output if the input was generated from a well engineered prompt to be deliberately chaotically human.

---

## Rate Limiting

The application uses `Flask-Limiter` to apply a strict traffic threshold to the primary submission route:

* **Configured Limit:** `10 requests per minute` per unique IP address.
* **Implementation Rationale:** This threshold prevents brute-force token exhaustion attacks against the underlying Groq API endpoint while providing ample headroom for standard human desktop workflows and automated test sweeps.

### Spec Reflection

The technical specification provided a rigorous blueprint for setting up the async thread execution architectures. However, during live implementation, the system design diverged from the spec by shifting from an ephemeral in-memory dictionary array to a localized file-backed JSON system to ensure historical logs survive application restarts. The weight system that was originally applied to human-like vs AI-like scoring was shifted to a weight system of signal 1 vs signal 2 because signal 1 was more robust than signal 2.

---

## Audit Log

All systemic attribution calculations, confidence evaluations, metadata, and user disputes are tracked inside a structured database schema located at `audit_log.json`.

```json
[
  {
    "timestamp": "2026-06-30T14:22:10.112Z",
    "text": "The sun dipped below the horizon line,\nA quiet whisper of golden twine.",
    "creator_id": "web-ui-session-1",
    "content_id": "e9b5fca2-8db4-47ef-bc71-3cb5a12fa38a",
    "confidence": 0.28,
    "attribution": "likely_human",
    "appeals": []
  },
  {
    "timestamp": "2026-06-30T14:25:44.891Z",
    "text": "In the mechanical city of shining steel,\nThe automated thoughts are all we feel.\nEvery system runs on regular time,\nEvery sentence fits a perfect rhyme.",
    "creator_id": "web-ui-session-1",
    "content_id": "8c42b10a-fc27-4a0b-9df0-1cfa97d81a24",
    "confidence": 0.86,
    "attribution": "under_review",
    "appeals": [
      {
        "timestamp": "2026-06-30T14:26:12.304Z",
        "creator_reasoning": "I intentionally utilized a rigid iambic tetrameter layout to mimic historical early industrial poetic aesthetics.",
        "status": "pending",
        "reviewer_view_message": "Their appeal is pending."
      }
    ]
  },
  {
    "timestamp": "2026-06-30T14:30:01.005Z",
    "text": "Shadows dance. Clock towers strike standard hours.\nRain falls down upon concrete towers.",
    "creator_id": "web-ui-session-1",
    "content_id": "31bfa829-9c55-4672-881b-80a99671d182",
    "confidence": 0.54,
    "attribution": "uncertain",
    "appeals": []
  }
]

```

---

## AI Usage Section

* **Instance 1 (Ensemble Structure Setup):** Directed the AI to generate boilerplate async worker dispatch blocks using Python's `ThreadPoolExecutor`. Reviewed and overrode the sample payload management by completely rewriting the mathematical weight distribution to favor human validation thresholds over raw averages.
* **Instance 2 (Test Environment Optimization):** Directed the AI to draft a functional `pytest` architecture mocking the Groq API completion responses. Overrode the initial configuration by adding a mock key injection directly to the test runtime loop, preventing the Groq SDK client initialization from raising missing environment variable errors during local isolated tests.