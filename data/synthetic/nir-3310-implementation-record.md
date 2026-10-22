# NIR-3310 — Network Implementation Record: CNPD 24.3

> SYNTHETIC / SANITIZED. Invented record for a learning project.

## Scope

Network Implementation Record capturing the deployment topology and environment
progression for CNPD Release 24.3.

## Environments and progression

- **Lab** → **FOA** → **Production** (FOA precedes Production).
- Lab acceptance results gate FOA. FOA sign-off gates Production.

## Deployed network functions (FOA)

| NF | Version | deployed_on |
|---|---|---|
| SAEGW-C | 24.3.0-cp | CaaS cluster FOA-A |
| SAEGW-U | 24.3.0-up | CaaS cluster FOA-A |
| MME | 24.3.1 | CaaS cluster FOA-A |
| PCC | 7.2.0 | CaaS cluster FOA-A |
| PCG | 7.2.0 | CaaS cluster FOA-A |

## Interfaces

- Sx between SAEGW-C and SAEGW-U (monitored by ALM-SX-DOWN).
- S1-AP on MME (monitored by ALM-S1AP-TIMER).

## References

- CNPD 24.3 Integration & Compatibility Matrix, per-CNF release notes, MOP-5521, CIQ-8807, AAT report, Defect Register.
