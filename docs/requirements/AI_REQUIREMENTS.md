# AI Requirements

## AIR-1: Complaint Classification

### Objective
Automatically classify citizen complaint text into the correct grievance category.

### Model Specification
| Parameter | Value |
|---|---|
| Type | Multi-class text classifier |
| Algorithm (MVP) | TF-IDF vectorization + Logistic Regression with multi-class support |
| Algorithm (upgrade path) | Fine-tuned DistilBERT or similar transformer |
| Categories | 15 initial categories (expandable) |
| Input | Raw complaint text (sanitized) |
| Output | Primary category, confidence score, top-3 alternatives |

### Training Data Requirements
- Small realistic synthetic dataset for MVP demonstration
- Realistic Indian English with regional variations
- Include edge cases: multi-category complaints, vague descriptions, very short text
- Labeled with single primary category

### Acceptance Criteria
| Metric | Threshold |
|---|---|
| Overall accuracy | ≥ 85% on held-out test set |
| Per-category precision | ≥ 70% for each category |
| Per-category recall | ≥ 70% for each category |
| Weighted F1 | ≥ 0.82 |
| Inference latency | < 500ms per complaint |
| Low-confidence handling | Complaints with confidence < 0.5 flagged for manual review |

### Explainability
- Top contributing features/terms shown for each classification
- Confidence score calibrated (not just softmax output)
- Alternative categories provided for officer review

---

## AIR-2: Priority Assessment

### Objective
Determine grievance urgency from multiple signals (not just sentiment).

### Model Specification
| Parameter | Value |
|---|---|
| Type | Rule-based weighted scoring with NLP enhancement |
| Input | Complaint text, category, location context |
| Output | Priority (CRITICAL/HIGH/MEDIUM/LOW), score (0-100), factor breakdown |

### Scoring Factors
| Factor | Weight | Detection Method |
|---|---|---|
| Safety impact | 25% | Category mapping + keyword detection (danger, injury, electric, fire, children) |
| Severity | 20% | Keyword intensity analysis |
| Affected population | 15% | Entity detection (school, hospital, colony, market) |
| Time sensitivity | 15% | Temporal expressions ("since yesterday", "urgent") |
| Category baseline | 10% | Lookup table per category |
| Location context | 10% | Location keyword analysis (school, hospital) |
| Repeat complaint | 5% | Duplicate detection result |

### Acceptance Criteria
| Metric | Threshold |
|---|---|
| CRITICAL correctly identified | ≥ 90% recall for safety-related complaints |
| Priority reasonableness | Human reviewers agree with ≥ 80% of assessments |
| Factor breakdown | Every priority includes all 7 factor scores |
| Inference latency | < 200ms per complaint |

---

## AIR-3: Accountability Risk Score

### Objective
Continuously assess per-grievance failure risk to enable proactive intervention.

### Model Specification
| Parameter | Value |
|---|---|
| Type | Weighted factor model (deterministic scoring) |
| Input | Grievance data, event history, SLA state, policies |
| Output | Score (0-100), level, factor-by-factor breakdown |
| Recomputation | On events + periodic (every 5 min) |

### Acceptance Criteria
| Metric | Threshold |
|---|---|
| Score monotonicity | Score increases as SLA consumption increases (all else equal) |
| Explanation completeness | Every score shows all 10 factor contributions |
| Breach prediction | Score > 70 for ≥ 80% of cases that eventually breach SLA |
| False alarm rate | Score > 85 for < 15% of cases that resolve successfully |
| Computation latency | < 100ms per grievance |

---

## AIR-4: Semantic Duplicate Detection

### Objective
Identify complaints that may refer to the same underlying issue.

### Model Specification
| Parameter | Value |
|---|---|
| Type | Dense vector similarity search |
| Embedding model | `all-MiniLM-L6-v2` (384-dimension, ~22M params) |
| Similarity metric | Cosine similarity |
| Storage | pgvector in PostgreSQL |
| Threshold | 0.80 default (configurable) |

### Acceptance Criteria
| Metric | Threshold |
|---|---|
| True duplicate recall | ≥ 80% of known duplicates detected |
| False positive rate | < 10% of suggestions are unrelated |
| Embedding latency | < 200ms per complaint |
| Search latency | < 500ms for nearest-neighbor search |
| Scope | Same department or geographic radius |

---

## AIR-5: Complaint Summarization

### Objective
Generate concise summaries for officer and supervisor consumption.

### Model Specification
| Parameter | Value |
|---|---|
| Type | LLM-based extractive/abstractive summarization |
| Provider | Gemini API (primary) or local Ollama model |
| Fallback | First 200 characters if LLM unavailable |
| Input | Sanitized complaint text |
| Output | 2-3 sentence summary |

### Acceptance Criteria
| Metric | Threshold |
|---|---|
| Summary length | 50-300 characters |
| Content accuracy | Preserves: what, where, who affected, duration |
| Hallucination rate | 0% fabricated details |
| Safety | No executable content, URLs, or system references |
| Latency | < 3 seconds (LLM API), < 100ms (fallback) |

---

## AIR-6: Evidence Analysis

### Objective
Provide verification signals about resolution evidence quality.

### Model Specification
| Parameter | Value |
|---|---|
| Type | Rule-based signal extraction from file metadata |
| Input | Uploaded files + complaint context |
| Output | Signal report (existence, type, timestamp, location, size) |

### Acceptance Criteria
| Metric | Threshold |
|---|---|
| Signal extraction accuracy | 100% for file metadata extraction |
| EXIF timestamp extraction | When available in JPEG files |
| Location signal | GPS data extracted from EXIF when present |
| No false certainty | Output is "signals" not "verdicts" |

---

## AI Security Requirements

### AISEC-1: Input Sanitization
- All complaint text sanitized before AI processing
- HTML/script tags stripped
- Prompt injection patterns detected and logged
- Control characters removed

### AISEC-2: Output Validation
- Classification output validated against known categories
- Confidence validated as float [0, 1]
- Summary validated for length, content safety
- No AI output directly drives administrative action

### AISEC-3: Audit Logging
- Every AI inference call logged with: input (hash), output, confidence, model, latency, timestamp
- Suspected prompt injection attempts logged with full context
- AI model version tracked in logs

### AISEC-4: Separation of Concerns
- AI produces recommendations and signals only
- Governance Engine evaluates deterministic rules
- Authorization layer enforces permissions
- Application layer executes permitted actions
