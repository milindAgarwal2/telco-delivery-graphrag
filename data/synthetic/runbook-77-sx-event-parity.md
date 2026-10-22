# RUN-77 — Troubleshooting Runbook: Sx event-parity failures

> SYNTHETIC / SANITIZED. Invented runbook for a learning project.

## When to use

Use when test case TC-204 (Sx event-parity) fails or alarm ALM-SX-DOWN is raised
on the SAEGW-C after an upgrade.

## Diagnosis steps

1. Confirm ALM-SX-DOWN is active on the Sx interface (SAEGW-C ↔ SAEGW-U).
2. Check whether a warm restart of the PCC policy engine occurred recently.
3. Compare event-parity counters between control and user plane.
4. If counters reset coincides with a warm restart, this is defect DEF-1203.

## Recommended fix

- Apply the DEF-1203 workaround: avoid warm restart of PCC during the upgrade
  window (see MOP-5521 step 3).
- Re-run TC-204 to confirm counters converge.
- If the failure persists without a warm restart, escalate — it is NOT DEF-1203.

## Related

- MOP-5521 (upgrade), DEF-1203 (defect), ALM-SX-DOWN (alarm), TC-204 (test case),
  AAT report (evidence).
