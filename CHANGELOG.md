# Changelog

All notable changes to this public showcase are documented here. The showcase
describes the safety architecture of a private system; it contains no source,
prompts, credentials, or customer data.

## [0.2.8] - 2026-11-24

A message from the business account switches automated sales replies for a single private conversation. The assistant can include product links and leave the conversation with an operator. Browser tests covered the route from a simulated inbound message to a matching outgoing echo, recipient mismatch, copied commands and restart recovery. Real customer messages were excluded from these tests.

## [0.2.7] - 2026-11-24

The shopping assistant keeps an explicit watch reference and the shopper’s stated criteria when comparing alternatives. A short follow-up can call out a known difference in movement or price. Seventy regression tests covered conversation, filters and identity. The running service reported the new release after restart.

## [0.2.6] - 2026-11-24

The inbox check now opens the service’s conversations overview from a signed-in account. It distinguishes the account menu, the conversations section and the list itself. The business account remained signed in when its browser reopened. A separate operator connection confirmed visible conversation tabs and list rows. The check left individual conversations closed. Seven browser and control tests passed, including tests for a fresh login prompt and repeated checks in the same browser.

## [0.2.5] - 2026-11-24

The business inbox pilot recognizes the header and list that the web application displays for conversations. A Chromium test exercised visible navigation, hidden controls, a sign-in page and a different site. The status report contains a screen category and navigation indicators. Six browser and control tests passed.

## [0.2.4] - 2026-11-24

When the assistant presents watches, it can point out a documented difference in movement or identify the least expensive option when every displayed price is known. Follow-up replies stay with the shopper’s question. Conversation, watch comparison, account verification, marketplace and media tests exercised these paths.

A separate business inbox pilot kept its browser running between two disconnected operator sessions. Account sign-in and customer reply delivery are still pending verification.

## [0.2.3] - 2026-11-24

Shoppers can ask in Persian for a watch with a particular dial, strap or case colour, a recorded audience, and a range of case diameters. The assistant keeps these constraints together and asks which to change when the catalogue has no exact match. Checks used real catalogue attributes and included requests with no matching watch.

## [0.2.2] - 2026-11-18

Watch comparisons now include functions recorded under the store’s additional-functions and calendar attributes. A live request returned three available alternatives and showed a documented shared feature for each. The release passed 88 assistant checks and eight media checks.

## [0.2.1] - 2026-11-18

Returning customers can use a watch from their purchase history to compare available models. Verification persists within the same private chat. The installed service produced a catalogue-backed comparison and rejected unverified requests for personal order data.

## [0.2.0] - 2026-11-17

Installed verified marketplace and loyalty context; real customer message delivery remains unverified.

- Private customer reads require conversation-bound mobile verification; codes and access proofs stay outside model and profile context.
- Existing marketplace and loyalty producers supply customer facts, with distinct submission, publication, authenticity, points, wallet and tier states.
- Minimal verified commerce snapshots support management profiles without silently merging conflicting accounts.
- Failed or incomplete synchronization acknowledgements preserve the export cursor for retry.
- Local Python regressions, isolated commerce/identity integration, static analysis and packaging gates passed. Installed files, service health and live authentication boundaries were checked without sending customer messages.

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
