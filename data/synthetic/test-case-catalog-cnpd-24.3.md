# Test Case Catalog — CNPD 24.3 Acceptance

> SYNTHETIC / SANITIZED. Invented test cases for a learning project.

## TC-204 — Sx event-parity

- **validates:** SAEGW-C event-based monitoring (EVM) on the Sx interface.
- **environment:** Lab, FOA
- **precondition:** SAEGW-C at 24.3.0-cp (per MOP-5521).
- **steps:** generate bearer churn; compare event counters control vs. user plane.
- **pass_criteria:** counters match within tolerance for 5 minutes.
- **known_risk:** fails if PCC warm restart occurs (DEF-1203, ALM-SX-DOWN).

## TC-205 — Session continuity on upgrade

- **validates:** session survival across a SAEGW-C control-plane upgrade.
- **environment:** Lab, FOA
- **pass_criteria:** zero session loss during rolling upgrade; also validates
  MOP-5521 rollback.

## TC-209 — PCC counter persistence

- **validates:** PCC policy rule counters persist across warm restart.
- **environment:** FOA
- **status:** blocked_by DEF-1203 (marked Not Run for 24.3 FOA).

## TC-311 — S1-AP timer alignment

- **validates:** MME S1-AP timer behaviour (no re-attach storm).
- **environment:** Lab, FOA
- **pass_criteria:** re-attach rate below threshold. Confirms fix for DEF-1250.
