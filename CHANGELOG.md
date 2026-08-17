# Changelog

All notable changes to this public showcase are documented here. The showcase
describes the safety architecture of a private system; it contains no source,
prompts, credentials, or customer data.

## [0.1.1] - 2026-08-17

Conversation identity as a precondition for stateful gating.

### Changed

- Per-conversation state (purchase lifecycle, rejection memory) now requires a stable channel-and-identity key before it is written or read. A request that arrives without an identity is treated as anonymous rather than merged into a shared record.

### Fixed

- Anonymous conversations no longer collapse onto a single shared state record. A delivery confirmation on that shared record could switch the post-purchase boundary on for unrelated visitors and suppress their product recommendations — the assistant would describe products it then never sent. Stateful guards now fail open for anonymous conversations: nothing is persisted or gated for them, so they always receive recommendations, while identified conversations keep full post-purchase handling.

### Tests

- Regression coverage proving a degenerate conversation key persists no state and never suppresses recommendations, even with the post-purchase gate fully enabled, while an identified post-purchase conversation still gates correctly.

## [0.1.0] - 2026-08-16

Initial public showcase of the staged-rollout architecture for a live,
multi-channel WooCommerce sales assistant.

### Documented

- Evidence-based, read-only audit that named the causes of weak behavior before any production change.
- Deterministic safety guards deployed inert, proven not to change any live reply, then raised per feature.
- Fail-closed transaction-claim guard: no order, payment, reservation, or shipment claim ships without a matching successful tool result.
- Post-purchase boundary that closes the sales cycle after a confirmed delivery and reopens only on explicit new-purchase intent.
- Follow-up messages revalidated against current purchase state at send time.
- Persisted purchase-lifecycle state, isolated from the customer profile store.
- Consultative decision engine reaching real traffic as a conversation-sticky five-percent canary, with the model writing within a contract.
- Privacy-safe control/candidate event stream (hashed identifiers, whitelisted fields) and feature-level automatic rollback.
