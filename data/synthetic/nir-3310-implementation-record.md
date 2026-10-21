# NIR-3310 — Network Implementation Record: DMC 24.3

> SYNTHETIC / SANITIZED. Invented record for a learning project.

## Scope

Network Implementation Record capturing the deployment topology and environment
progression for DMC Release 24.3.

## Environments and progression

- **Lab** → **FOA** → **Production** (FOA precedes Production).
- Lab acceptance results gate FOA. FOA sign-off gates Production.

## Deployed network functions (FOA)

| NF | Version | deployed_on |
|---|---|---|
| cSAEGW-C | 24.3.0-cp | CNIS cluster FOA-A |
| cSAEGW-U | 24.3.0-up | CNIS cluster FOA-A |
| cMME | 24.3.1 | CNIS cluster FOA-A |
| PCC | 7.2.0 | CNIS cluster FOA-A |
| PCG | 7.2.0 | CNIS cluster FOA-A |

## Interfaces

- Sx between cSAEGW-C and cSAEGW-U (monitored by ALM-SX-DOWN).
- S1-AP on cMME (monitored by ALM-S1AP-TIMER).

## References

- DMC 24.3 Integration & Compatibility Matrix, per-CNF release notes, MOP-5521, CIQ-8807, AAT report, Defect Register.
