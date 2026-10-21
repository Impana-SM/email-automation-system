# Validation & Testing Protocol

This document establishes the testing strategy, validation commands, benchmark criteria, and acceptance gates used to verify every component of the implementation.

---

## 1. Testing Hierarchy

```
                    ┌───────────────────────────┐
                    │  End-to-End Test Harness  │
                    │  (Mock Ingestion to Sent) │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     Integration Tests     │
                    │   (DB, Guardrails, LLM)   │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │      Unit Test Suite      │
                    │ (Parsers, Sanitizers, NER)│
                    └───────────────────────────┘
```

---

## 2. Validation Frameworks & Commands

- **Test Runner:** `pytest` with `pytest-asyncio` and `pytest-mock`.
- **Type Checking:** `mypy --strict`.
- **Code Style & Linting:** `ruff check` and `ruff format`.
- **Schema Validation:** `pydantic v2`.

### Standard Validation Commands
```powershell
# Run full unit & integration suite
pytest tests/ -v --tb=short

# Run test coverage report
pytest --cov=email_automation --cov-report=term-missing tests/

# Execute static type checking
mypy email_automation/

# Lint and verify code hygiene
ruff check email_automation/ tests/
```

---

## 3. Validation Checklist per Milestone

For every newly implemented module, the following criteria must pass before advancing:

| Module | Verification Criteria | Validation Method |
| :--- | :--- | :--- |
| **Ingestion** | Correct connection, TLS handshake, robust retry on connection drop, parsing RFC 822 envelopes. | Mock IMAP/OAuth server tests via `pytest-mock`. |
| **Preprocessing** | HTML stripping without losing text semantics, removal of signature blocks, exact entity extraction. | Golden fixture files testing 50+ diverse email structures. |
| **Intelligence** | Intent accuracy $\ge 90\%$ on evaluation test subset, latency within configured SLA ($<1.5\text{s}$). | Automated benchmark script comparing predictions against ground-truth labels. |
| **Guardrails** | 100% detection rate on seeded PII (credit cards, social security numbers), deterministic rejection of dangerous prompts. | Adversarial red-team test dataset with edge cases. |
| **Dispatch** | Adherence to rate limits (e.g., max 10 emails/sec), inclusion of proper RFC headers (`In-Reply-To`, `References`). | Mock SMTP sink validating dispatched header metadata. |
