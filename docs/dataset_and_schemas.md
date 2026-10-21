# Datasets & Data Schemas

This document outlines the datasets utilized for training, evaluation, and benchmarking, alongside data cleaning protocols and schema specifications.

---

## 1. Datasets Overview

The system leverages a blend of established open-source benchmarks and domain-tailored synthetic/curated email corpuses:

| Dataset | Type / Source | Volume | Primary Use |
| :--- | :--- | :--- | :--- |
| **Enron Email Corpus (Cleaned)** | Real-world corporate emails | ~500,000 raw messages | Unsupervised language adaptation, header parsing benchmarks, thread separation tests. |
| **Banking77 / CLINC150** | Curated customer intent queries | 13,088 queries (77 classes) | High-precision baseline benchmark for fine-grained intent classification. |
| **Customer Support Ticket Corpus** | Kaggle / Hugging Face Support records | ~50,000 email tickets | Supervised training for urgency, sentiment, and resolution routing. |
| **Domain Synthetic Dataset** | Generated via synthetic LLM workflows | ~5,000 pairs | Specific domain test cases (custom billing workflows, return policies, edge cases). |

---

## 2. Data Preparation & Curation Pipeline

```
Raw Email Data 
      │
      ▼
[1. MIME & RFC 822 Normalization]  ──> Standardizes encodings (UTF-8, ISO-8859)
      │
      ▼
[2. Thread & Signature Separation] ──> Extracts the novel text; strips email signatures & prior quotes
      │
      ▼
[3. PII De-identification]         ──> Replaces credit cards, SSNs, phone numbers with tokens (<CARD>, <PHONE>)
      │
      ▼
[4. Semantic Deduplication]        ──> MinHash LSH removes duplicate notification spam
      │
      ▼
[5. Stratified Splitting]          ──> 70% Train / 15% Validation / 15% Test (balanced across intent labels)
```

---

## 3. Core Schema Contracts (Pydantic / JSON Schema)

### 3.1 Training Record Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EmailTrainingSample",
  "type": "object",
  "properties": {
    "sample_id": { "type": "string" },
    "source_dataset": { "type": "string" },
    "subject": { "type": "string" },
    "body": { "type": "string" },
    "intent_label": {
      "type": "string",
      "enum": [
        "billing_inquiry",
        "technical_support",
        "order_tracking",
        "cancellation_request",
        "product_feedback",
        "general_inquiry"
      ]
    },
    "urgency_level": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"]
    },
    "entities": {
      "type": "object",
      "properties": {
        "account_id": { "type": "string" },
        "invoice_number": { "type": "string" }
      }
    },
    "gold_response": { "type": "string" }
  },
  "required": ["sample_id", "body", "intent_label", "urgency_level"]
}
```

### 3.2 Live Inbound Message Contract
```json
{
  "message_id": "str (UUID v4)",
  "sender": "user@domain.com",
  "recipients": ["inbox@company.com"],
  "subject": "string",
  "body_plaintext": "string",
  "body_html": "string | null",
  "headers": "dict",
  "timestamp": "ISO 8601 UTC timestamp",
  "attachments_meta": [
    {
      "filename": "invoice.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 1048576
    }
  ]
}
```
