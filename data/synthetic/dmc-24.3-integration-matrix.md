# DMC 24.3 — Integration & Compatibility Matrix

> SYNTHETIC / SANITIZED. Invented integration view for a learning project.
> This document is the ASSEMBLED program view. The individual network functions
> ship their own per-CNF release notes on independent version cadences; this
> matrix records which specific CNF versions are **certified together** for DMC
> Release 24.3 (paired with ECDS Release 7.2).

## 1 Certified version set (DMC 24.3 / ECDS 7.2)

The delivery team certifies the following CNF versions as an interoperable set.
DMC Release 24.3 **includes** each of these (CNF, version) pairs:

| Network Function | Certified Version | Per-CNF Release Note | Vendor cadence |
|---|---|---|---|
| cSAEGW-C | 24.3.0-cp | release-note-csaegw-c-24.3.0-cp | SAEGW 24.3.x |
| cSAEGW-U | 24.3.0-up | release-note-csaegw-u-24.3.0-up | SAEGW 24.3.x |
| cMME | 24.3.1 | release-note-cmme-24.3.1 | MME 24.3.x |
| PCC | 7.2.0 | release-note-pcc-7.2.0 | ECDS 7.2.x |
| PCG | 7.2.0 | release-note-pcg-7.2.0 | ECDS 7.2.x |

DMC Release 24.3 is paired with (supported by) **ECDS Release 7.2**.

## 2 Cross-CNF compatibility notes

- **cSAEGW-C 24.3.0-cp is certified_with cSAEGW-U 24.3.0-up** — the control and
  user planes must be upgraded as a matched pair for Sx association.
- **cSAEGW-C 24.3.0-cp is certified_with PCC 7.2.0**, but with a caveat: the
  open PCC defect DEF-1203 (counter reset on warm restart) means a PCC warm
  restart during the cSAEGW-C upgrade window can fail event-parity (TC-204). The
  certified combination is valid only when the DEF-1203 workaround is applied.
- **cMME 24.3.1 is certified_with the SAEGW/ECDS set** and has no cross-CNF
  caveats in this release.
- **PCG 7.2.0 is certified_with PCC 7.2.0** (shared ECDS 7.2 charging/policy
  baseline).

## 3 Minimum-version requirements

- cSAEGW-C 24.3.0-cp **requires** PCC at minimum 7.2.0 (policy rule evaluation
  update) and PCG at minimum 7.2.0.
- There is **no** certified mix of SAEGW 24.3.x with ECDS 7.1.x — the 24.3 set
  requires the ECDS 7.2 baseline.

## 4 Assembly provenance

Each row is sourced from the corresponding per-CNF release note. The open-defect
caveat is sourced from the PCC 7.2.0 release note (DEF-1203) and the AAT report.
Required upgrade procedure: MOP-5521 (cSAEGW-C). FOA parameters: CIQ-8807.
Implementation record: NIR-3310. Lab acceptance gates FOA; FOA precedes
Production.
