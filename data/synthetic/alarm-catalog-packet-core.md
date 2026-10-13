# Alarm Catalog (excerpt) — Packet Core

> SYNTHETIC / SANITIZED. Invented alarm definitions for a learning project.

## ALM-SX-DOWN

- **Interface:** Sx (cSAEGW-C ↔ cSAEGW-U)
- **Severity:** Major
- **Meaning:** Sx association degraded or event-parity counters diverging.
- **observed_on:** cSAEGW-C
- **Common cause:** warm restart of a dependent policy component (see DEF-1203).
- **Correlates_with:** test case TC-204 failure during event-parity checks.
- **First action:** consult runbook RUN-77.

## ALM-S1AP-TIMER

- **Interface:** S1-AP (cMME)
- **Severity:** Minor
- **Meaning:** S1-AP timer threshold exceeded; possible re-attach storm.
- **observed_on:** cMME
- **Resolved_by:** cMME 24.3.1 (DEF-1250). Validated by TC-311.

## ALM-PCG-CHG

- **Interface:** charging (PCG)
- **Severity:** Warning
- **Meaning:** charging gateway record lag.
- **observed_on:** PCG
