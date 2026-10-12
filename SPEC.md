# Product specification — customer-support-agent

> Status: draft. A coding agent must not implement product code until this specification is approved through Genesis.

## Problem

Customer support inquiries (including order tracking, return/refund policies, shipping questions, and general inquiries) require timely, accurate, and safe responses. Automated responses must rely strictly on verified knowledge base evidence, request missing customer information when needed, and escalate to human agents when evidence is insufficient or unavailable, preventing hallucinations.

## Users

- **End Customers**: Users seeking support for order tracking, policy details, shipping questions, and general inquiries.
- **Customer Support Representatives**: Human agents receiving structured escalations when queries cannot be autonomously resolved.

## Functional requirements

- FR-1: The agent shall classify customer query intents into defined categories (`ORDER_STATUS`, `KNOWLEDGE_QUERY`, `OTHER`).
- FR-2: The agent shall detect missing required parameters (such as missing order numbers for `ORDER_STATUS`) and ask the customer for the missing details.
- FR-3: The agent shall retrieve relevant policy and support documents from ChromaDB vector storage for `KNOWLEDGE_QUERY` intents.
- FR-4: The agent shall reason over retrieved context using an evidence-based decision framework (`SUFFICIENT`, `INSUFFICIENT`, `CUSTOMER_INFO_MISSING`, `ESCALATED`).
- FR-5: The agent shall escalate to human support whenever evidence is insufficient after retries (up to max attempts) or when the query cannot be safely resolved.

## Non-functional requirements

- NFR-1: The agent must adhere to the invariant that no confident answer is produced without verified, non-empty supporting evidence.
- NFR-2: Intent classification, retrieval, and reasoning decisions must execute in under 3 seconds per customer turn.
- NFR-3: The system must provide reproducible structured evaluation metrics and logs across benchmark datasets.

## Constraints

- Runtime environment: Python 3.10+.
- Local LLM inference supported via Ollama (`qwen2.5:3b`) with sentence transformer embeddings.
- Vector database: ChromaDB local vector storage.
- Local repository trust boundary.

## Non-goals

- Direct payment processing or automatic order cancellations/refunds in V1 (information and escalation only).
- Multi-lingual support beyond English in the initial release.

## Acceptance criteria

- AC-1: Goal classification accuracy must reach at least 95% across the standard 50-case benchmark evaluation suite.
- AC-2: The agent must correctly prompt for order numbers when an order query lacks an identifier, and process status when provided.
- AC-3: Zero unhandled runtime exceptions during automated evaluation with clean escalation on unsupported queries.

## Risks

- Low retrieval relevance for edge-case knowledge queries leading to unhelpful answers -> Mitigated by multi-attempt retrieval retries and escalation.
- Empty evidence reasoning failures -> Mitigated by state-level assertions preventing `SUFFICIENT` decision when evidence text is empty.

## Open questions

- None.
