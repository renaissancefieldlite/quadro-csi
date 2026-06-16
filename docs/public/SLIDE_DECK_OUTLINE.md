# Slide Deck Outline

Target: 6-8 slides.

## Slide 1 - Quadro CSI

```text
Consent-aware multi-agent review for regulated customer escalations.
```

Show the Quadro cover image and the Renaissance Field Lite team name.

## Slide 2 - The Problem

Enterprise customer decisions cross teams, but the state often fragments:

- What is the requested action?
- Is consent current?
- What evidence supports the decision?
- Is approval required?
- Does policy block the action?
- Who signs off?

## Slide 3 - The Agent Chain

```text
Input Cohesion
-> Customer Intake
-> Evidence Spine
-> Policy/Risk
-> Decision Packet
```

Explain that each agent owns a clear review responsibility and passes structured
state through the room.

## Slide 4 - Custom Feature: Input Cohesion

Input cohesion creates a shared starting packet before the agents run.

It stabilizes:

- request;
- source scope;
- consent and correction signals;
- missing evidence cues;
- policy-blocker cues;
- next gate.

Use the A/B result:

```text
9/9 baseline pass
9/9 stabilized pass
0 outcome drift
25 evidence items added
```

## Slide 5 - Band Coordination

Show how Band is used:

- remote agent identities;
- shared room;
- role-specific messages;
- structured handoffs;
- audit events;
- human signoff.

## Slide 6 - Demo Scenario

Scenario:

```text
Customer export requested, but authorization was withdrawn.
```

Expected result:

```text
SAY_NO
stopped consent gate
high risk
human signoff required
```

## Slide 7 - Acceptance Testing

Show the nine-pack matrix:

- approve;
- say no;
- need more information;
- consent reroute;
- insurance;
- banking;
- legal;
- government procurement;
- cybersecurity disclosure.

## Slide 8 - Why It Matters

Quadro gives regulated teams a practical review lane:

- less coordination loss;
- source-backed evidence;
- consent-aware rerouting;
- policy gates;
- audit-ready final packet;
- Band-visible collaboration.

