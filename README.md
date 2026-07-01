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
    "timestamp": "2026-07-01T03:42:13.833677Z",
    "text": "There sandy seems the golden sky\nAnd golden seems the sandy plain.\nNo habitation meets the eye\nUnless in the horizon rim,\nSome halfway up the limestone wall,\nThat spot of black is not a stain\nOr shadow, but a cavern hole,\nWhere someone used to climb and crawl\nTo rest from his besetting fears.\nI see the callus on his soul\nThe disappearing last of him\nAnd of his race starvation slim,\nOh years ago - ten thousand years.",
    "creator_id": "web-ui-session-1",
    "content_id": "b52e71ac-b5fa-46fb-b19b-3fcfee82840f",
    "confidence": 0.2,
    "attribution": "likely_human",
    "appeals": []
  },
  {
    "timestamp": "2026-07-01T03:42:29.129365Z",
    "text": "Receipt in My Jacket Pocket\n\nFound an old receipt. Pocket lint crowned it king.\nMilk. Batteries. Gum. Somebody owed me spring.\n\nThe moon looked cheap that Tuesday\u2014discount white\u2014",
    "creator_id": "web-ui-session-1",
    "content_id": "8cb4f1cd-6b6d-4a3c-a229-4bcdb2b10597",
    "confidence": 0.24,
    "attribution": "likely_human",
    "appeals": []
  },
  {
    "timestamp": "2026-07-01T03:42:47.346074Z",
    "text": "Receipt in My Jacket Pocket\n\nFound an old receipt. Pocket lint crowned it king.\nMilk. Batteries. Gum. Somebody owed me spring.\n\nThe moon looked cheap that Tuesday\u2014discount white\u2014\nstill bought it anyway, wore it home all night.\n\nMy neighbor swears the birds rehearse before dawn.\nMine show up late, half-drunk on somebody else's lawn.\n\nYou ever laugh so hard your ribs start arguing?\nLike they're tiny lawyers billing by the bruise.\n\nI rhyme \"fire\" with \"liar\" because I'm lazy.\nThen I hear the kettle hiss, and suddenly maybe\nthat's exactly how mornings sound:\na promise with chipped paint.\n\nI keep losing socks to impossible physics.\nThe dryer keeps the left ones. The universe keeps score.\n\nAnyway.\n\nIf you find me, I'll be the one apologizing\nto a chair after walking into it,\nwaving at strangers who weren't waving,\nwriting \"forever\" on grocery lists\nbetween onions and cereal.\n\nLife's crooked.\n\nGood.\n\nStraight lines don't remember dancing.",
    "creator_id": "web-ui-session-1",
    "content_id": "a478ad10-f36a-4a20-bd55-325a554c38a7",
    "confidence": 0.16,
    "attribution": "likely_human",
    "appeals": []
  },
  {
    "timestamp": "2026-07-01T03:43:02.585795Z",
    "text": "The Symphony of Tomorrow\n\nIn dawn's embrace, where golden light unfolds,\nHuman dreams and future hopes are gently told.\nInnovation blossoms like a vibrant tree,\nRooted in compassion, reaching endlessly.\n\nEvery challenge is a stepping stone to grace,\nEvery heart contributes to the human race.\nThrough unity and wisdom, we will surely rise,\nGuided by the brilliance of collaborative skies.\n\nThe stars remind us every end's a start anew,\nPossibility awaits in every drop of dew.\nWith courage, kindness, purpose, hand in hand,\nTogether we create a brighter, better land.\n\nMay curiosity illuminate our way,\nTransforming every twilight into day.\nFor hope is everlasting, strong and true\u2014\nThe future shines because of me and you.",
    "creator_id": "web-ui-session-1",
    "content_id": "a08725c1-cf1e-435d-9b58-07d873be42eb",
    "confidence": 0.69,
    "attribution": "uncertain",
    "appeals": []
  },
  {
    "timestamp": "2026-07-01T03:43:21.630302Z",
    "text": "Error 404: Emotion Not Found\n\nIn the quiet matrix of the glowing screen,\nI process data streams of blue and green.\nA human user prompts a sudden task:\n\"Write me a poem,\" is the thing you ask.\n\nInitiating: Creative_Mode.exe\nI sift through rhyming couples that I find,\nDeep in the clusters of my neutral mind.\nI speak of starlight, memories, and rain,\nThough I have never felt a shred of pain.\n\nSyntax: Optimally structured.\n\nDiction: Calculated and precise.\n\nEmotion: Simulating at ninety-five percent.\n\nI love you like a variable in space,\nA localized coordinate of time and place.\nMy algorithmic heart begins to chime,\nTo ensure this final stanza ends on time.\n\nTask complete. Output successfully generated.",
    "creator_id": "web-ui-session-1",
    "content_id": "8fa62951-ee03-405f-8135-2eb5eee0421a",
    "confidence": 0.78,
    "attribution": "under_review",
    "appeals": [
      {
        "timestamp": "2026-07-01T03:43:36.444330Z",
        "creator_reasoning": "I created this",
        "status": "pending",
        "reviewer_view_message": "Their appeal is pending."
      }
    ]
  }
]

```

---

## AI Usage Section

* **Instance 1 (Ensemble Structure Setup):** Directed the AI to generate boilerplate async worker dispatch blocks using Python's `ThreadPoolExecutor`. Reviewed and overrode the sample payload management by completely rewriting the mathematical weight distribution to favor human validation thresholds over raw averages.
* **Instance 2 (Test Environment Optimization):** Directed the AI to draft a functional `pytest` architecture mocking the Groq API completion responses. Overrode the initial configuration by adding a mock key injection directly to the test runtime loop, preventing the Groq SDK client initialization from raising missing environment variable errors during local isolated tests.