# MOP-5521 — Upgrade Procedure: SAEGW-C to 24.3.0-cp

> SYNTHETIC / SANITIZED. Invented procedure for a learning project.

## Purpose

Method of Procedure to upgrade the SAEGW-C network function to software version
24.3.0-cp as part of CNPD Release 24.3. This MOP is **required_by** Release 24.3
and **describes** the control-plane upgrade configuration.

## Scope and prerequisites

- Applies to: SAEGW-C instances in Lab and FOA environments.
- Prerequisite: CIQ-8807 parameters loaded; backup snapshot taken.
- Related defect fixed by this version: DEF-1187.

## Procedure steps

1. Drain control-plane sessions gracefully (max 15 minutes).
2. Snapshot current configuration and persist to the backup store.
3. Apply software version 24.3.0-cp to the SAEGW-C control-plane pods.
4. Verify Sx association re-establishes with SAEGW-U.
5. Run smoke test TC-204 (Sx event-parity) and TC-205 (session continuity).
6. If TC-204 fails, consult the troubleshooting runbook RUN-77 and roll back.

## Rollback

Restore the pre-upgrade snapshot and revert pods to the prior version. Rollback
is validated by TC-205.

## Post-checks

- No new alarms of type ALM-SX-DOWN on the Sx interface.
- Event-parity counters match between control and user plane (TC-204 pass).
