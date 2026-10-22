# AAT Acceptance Test Report — CNPD 24.3 FOA

> SYNTHETIC / SANITIZED. Invented test outcomes for a learning project.

## Summary

Acceptance Acceptance Testing (AAT) results for CNPD Release 24.3 in the FOA
environment. Results **gate** FOA readiness. One test regressed after the
SAEGW-C upgrade; root cause and recommended fix are below.

| Test Case | Validates | Environment | Result | Linked |
|---|---|---|---|---|
| TC-204 | Sx event-parity (SAEGW-C) | FOA | FAIL | DEF-1203, ALM-SX-DOWN |
| TC-205 | Session continuity on upgrade | FOA | PASS | MOP-5521 |
| TC-311 | S1-AP timer (MME) | FOA | PASS | — |
| TC-209 | PCC counter persistence | FOA | NOT RUN | blocked_by DEF-1203 |

## TC-204 failure analysis

After upgrading SAEGW-C to 24.3.0-cp per MOP-5521, test case TC-204
(Sx event-parity) **failed** in FOA. The event-parity counters diverged between
control and user plane within 30 seconds of session churn.

### Evidence

- Alarm **ALM-SX-DOWN** was raised on the Sx interface at the time of failure.
- The divergence pattern matches defect **DEF-1203** (counter reset on warm
  restart) — the upgrade triggered a warm restart of the PCC policy engine.
- TC-205 (session continuity) PASSED, so the control-plane upgrade itself is
  sound; the failure is isolated to the event-parity counter path.

### Recommended fix

Apply the DEF-1203 workaround from the PCC 7.2.0 release note (avoid warm restart of PCC
during the upgrade window) and re-run TC-204. Permanent fix is targeted for CNPD
24.4. Until then, TC-204 is a known FOA risk and TC-209 remains blocked.

## FOA readiness

FOA readiness is **blocked** pending TC-204 re-run with the DEF-1203 workaround.
FOA **precedes** Production, so Production rollout is held.
