# System Architecture

## 1. High-Level Architecture Overview

The Email Automation platform is designed as an event-driven, decoupled, and modular pipeline that processes incoming/outgoing emails, extracts intent and key entities, executes domain logic, and routes or generates automated responses with human-in-the-loop oversight.

```mermaid
flowchart TD
    subgraph External Sources
        Gmail[Gmail API / IMAP]
        Outlook[Outlook Graph API / Exchange]
        Webhook[Custom Webhooks / SMTP Ingestion]
    end

    subgraph Ingestion Layer
        Poller[Email Ingestion & Listener Service]
        Auth[OAuth2 / Credential Manager]
    end

    subgraph Processing Layer
        Parser[MIME & HTML Parser]
        Cleaner[Sanitization & Text Normalizer]
        EntityExtractor[NER & Metadata Extractor]
    end

    subgraph Intelligence Layer
        Classifier[Intent & Urgency Classifier]
        ModelCore[LLM / Sequence-to-Sequence Engine]
        RAG[Context & Knowledge Base Retrieval]
    end

    subgraph Execution & Dispatch Layer
        RulesEngine[Policy & Routing Engine]
        DraftGenerator[Response Synthesis Engine]
        Dispatcher[Email Dispatcher & Rate Limiter]
        HumanReview[Human-in-the-Loop Review Queue]
    end

    subgraph Persistence & Audit
        DB[(Database / State Store)]
        AuditLog[Audit & Execution Logger]
    end

    External Sources --> IngestionLayer
    Poller --> Parser
    Parser --> Cleaner
    Cleaner --> EntityExtractor
    EntityExtractor --> Classifier
    Classifier --> RAG
    RAG --> ModelCore
    ModelCore --> RulesEngine
    RulesEngine -->|Auto-approved| Dispatcher
    RulesEngine -->|High-risk / Uncertain| HumanReview
    HumanReview --> Dispatcher
    Dispatcher --> External Sources

    Poller -.-> DB
    RulesEngine -.-> DB
    Dispatcher -.-> DB
    AuditLog -.-> DB
```

---

## 2. Core Architectural Principles

1. **Decoupled Asynchronous Processing:**
   - Ingestion, parsing, inference, and dispatch operate independently. Failures in third-party email providers do not crash the pipeline.
2. **Deterministic Fallbacks:**
   - LLM/ML outputs pass through explicit deterministic guardrails (schema validation, regex verification, rate limits, PII masking).
3. **State Transparency:**
   - Every email record carries an immutable transition history (`RECEIVED` ➔ `PARSED` ➔ `CLASSIFIED` ➔ `DRAFTED` ➔ `DISPATCHED` / `FLAGGED_FOR_REVIEW`).
4. **Extensible Provider Adapters:**
   - Standard interfaces for email providers (IMAP, Gmail API, Microsoft Graph API, SendGrid, Amazon SES).
