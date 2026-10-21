# Release Note — cMME 24.3.1

> SYNTHETIC / SANITIZED. Per-CNF release note invented for a learning project.
> Covers ONLY the cMME network function. Note the independent version cadence:
> cMME is at 24.3.1 while cSAEGW-C is at 24.3.0-cp in the same DMC release.

## Identity

- Network function: **cMME** (mobility management entity)
- Software version: **24.3.1**
- Vendor stream: Mobility Management (synthetic)

## Features in this version

- **S1-AP timer alignment:** reduces spurious re-attach. Validated by test case
  TC-311.

## Defects fixed in this version

- **DEF-1250** — cMME spurious re-attach storm. Severity Minor; status Fixed.
  Validated by TC-311 (S1-AP timer alignment).

## Known issues

- None in this version.

## Related procedures

- FOA topology for cMME recorded in NIR-3310. S1-AP is monitored by alarm
  ALM-S1AP-TIMER.
