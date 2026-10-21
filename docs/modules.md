# Module Architecture & Specifications

This document defines the individual software modules, their boundaries, responsibilities, and key interfaces.

---

## 1. Modular Directory Layout (Target Structure)

```
email_automation/
├── core/
│   ├── config.py           # Environment variables, secrets, runtime configurations
│   ├── exceptions.py       # Custom exception hierarchy
│   └── logging.py          # Structured JSON logging and tracing
│
├── ingestion/
│   ├── base.py             # Abstract Base Class for Ingestion Providers
│   ├── imap_client.py      # Generic IMAP4/SSL connection and mailbox listener
│   ├── gmail_adapter.py    # Google Workspace API integration (OAuth2)
│   └── outlook_adapter.py  # Microsoft Graph API integration
│
├── preprocessing/
│   ├── mime_parser.py      # Raw MIME & RFC 822 decoding, attachment isolation
│   ├── cleaner.py          # HTML stripping, quote/signature removal, sanitization
│   └── entity_extractor.py # Regex + NER for tracking IDs, dates, contact info
│
├── intelligence/
│   ├── classifier.py       # Multi-class intent and urgency classification
│   ├── context_engine.py   # RAG retrieval for company FAQs, policies, user records
│   ├── prompt_manager.py   # Prompt engineering templates with schema enforcement
│   └── generator.py        # LLM/Model orchestrator for personalized response drafting
│
├── guardrails/
│   ├── pii_scrubber.py     # Redaction of sensitive customer PII (credit cards, passwords)
│   ├── confidence_gate.py  # Validation of classification probabilities and confidence bounds
│   └── policy_checker.py   # Business rule enforcement (e.g. refunds > $100 require approval)
│
├── dispatch/
│   ├── sender.py           # Outbound mail dispatch (SMTP/API) with retry backoff
│   └── rate_limiter.py     # Token bucket / leaky bucket per-domain rate limiting
│
└── storage/
    ├── database.py         # SQLAlchemy engine and session lifecycle
    ├── models.py           # Relational or document schemas
    └── repositories.py     # Data access layer for email states and audit entries
```

---

## 2. Module Specifications

### 2.1 Ingestion Module (`ingestion/`)
- **Primary Class:** `BaseEmailIngestor`
- **Responsibilities:**
  - Connect securely via TLS/OAuth2.
  - Listen for new emails (idle command or periodic poller).
  - Handle transient network errors and disconnection events gracefully.
  - Return standardized raw email envelopes.

### 2.2 Preprocessing Module (`preprocessing/`)
- **Primary Classes:** `MimeParser`, `EmailCleaner`, `EntityExtractor`
- **Responsibilities:**
  - Strip HTML and CSS styling safely.
  - Identify and separate thread histories (replies vs original queries).
  - Extract key deterministic metadata (e.g., ticket references, tracking numbers).

### 2.3 Intelligence Module (`intelligence/`)
- **Primary Classes:** `IntentClassifier`, `ContextEngine`, `ResponseGenerator`
- **Responsibilities:**
  - Classify user queries into canonical categories (e.g., billing, tech support, general inquiry).
  - Retrieve relevant business policies or historical knowledge context.
  - Synthesize coherent, polite, and accurate draft responses.

### 2.4 Guardrails Module (`guardrails/`)
- **Primary Classes:** `PiiScrubber`, `ConfidenceGate`, `PolicyChecker`
- **Responsibilities:**
  - Enforce zero data leakage by masking credit cards, passwords, and sensitive identifiers.
  - Gate low-confidence predictions to human-review queues.
  - Prevent out-of-scope automated actions.

### 2.5 Dispatch Module (`dispatch/`)
- **Primary Classes:** `EmailDispatcher`, `RateLimiter`
- **Responsibilities:**
  - Deliver outbound emails with appropriate threading headers (`In-Reply-To`, `References`).
  - Throttle requests to respect provider quotas and prevent domain blacklisting.
