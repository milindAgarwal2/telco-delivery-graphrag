# Release Note — PCC 7.2.0

> SYNTHETIC / SANITIZED. Per-CNF release note invented for a learning project.
> Covers ONLY the PCC (policy control) network function. Note PCC uses the PCS
> 7.2.x numbering, independent of the SAEGW 24.3.x cadence — a real cross-vendor
> version-skew example.

## Identity

- Network function: **PCC** (policy control component)
- Software version: **7.2.0**
- Vendor stream: PCS Policy (synthetic)

## Features in this version

- Policy rule evaluation update aligned to PCS Release 7.2.

## Defects fixed in this version

- None fixed in this version.

## Known issues (open defects)

- **DEF-1203** — PCC policy rule counter resets on warm restart. Severity Major;
  status Open (workaround available). This defect **blocks** test case TC-209
  (PCC counter persistence) and **contributes to** the TC-204 failure when a
  warm restart coincides with the SAEGW-C event-parity check (alarm
  ALM-SX-DOWN is observed). Workaround: avoid warm restart of the PCC policy
  engine during the upgrade window (see MOP-5521). Permanent fix targeted for
  **CNPD Release 24.4**.

## Related procedures

- FOA policy profile (PROF-24.3-default) parameters are in CIQ-8807.
