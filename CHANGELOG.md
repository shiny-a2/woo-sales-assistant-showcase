# Changelog

All notable changes to this public showcase are documented here. The showcase
describes the safety architecture of a private system; it contains no source,
prompts, credentials, or customer data.

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
