# State-Path Stabilization

Quadro includes an input-cohesion pass before the agent chain runs.

The pass records:

- the stabilized review request;
- source document count and titles;
- consent, approval, financial, disclosure, and policy-blocker signals;
- correction markers such as updated, revised, revoked, or do not proceed;
- required evidence scopes;
- open questions;
- the next review gate.

This gives the agents a shared starting state before any evidence, policy, or
decision handoff. It helps Quadro keep long-running reviews coherent without
depending on hidden model internals or a single model provider.

The stabilized packet is stored in `state_path.cohesion_state`, then the normal
review chain continues:

```text
input cohesion
-> customer intake
-> evidence spine
-> policy/risk
-> decision packet
```

The public product framing is simple:

```text
Quadro keeps the request, source scope, consent state, blockers, and next gate
stable across the agent handoff chain.
```
