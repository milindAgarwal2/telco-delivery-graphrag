# Release Note — DMC Release 24.3 (ECDS 7.2)

> SYNTHETIC / SANITIZED. All releases, network functions, versions, test cases,
> and defects below are invented for a learning project. No real customer,
> subscriber, node, or confidential information is present.

## 1 Summary

DMC Release 24.3 pairs with ECDS Release 7.2 and targets the quarterly delivery
window for the cloud-native packet core. It introduces EBM event-parity for the
Sx interface and updates the cSAEGW-C control-plane handling. This release is
gated by lab acceptance before FOA.

- DMC Release: 24.3
- ECDS Release: 7.2 (supports DMC 24.3)
- Target environments: Lab → FOA → Production
- Delivery owner: Core Delivery Team (synthetic)

## 2 Network functions and versions

| Network Function | Software Version | Change |
|---|---|---|
| cSAEGW-C | 24.3.0-cp | Sx event-parity, control-plane fix |
| cSAEGW-U | 24.3.0-up | no functional change |
| cMME | 24.3.1 | S1-AP timer alignment |
| PCC | 7.2.0 | policy rule evaluation update |
| PCG | 7.2.0 | charging gateway alignment |

## 3 Key features

- **Sx event-parity (EBM):** event-based monitoring records on the Sx interface
  now match between control and user plane. Validated by test case TC-204.
- **cSAEGW-C control-plane fix:** resolves defect DEF-1187 (session drop under
  rapid bearer churn).
- **S1-AP timer alignment on cMME:** reduces spurious re-attach, test case TC-311.

## 4 Known issues

- DEF-1203 — PCC policy rule counter resets on warm restart. Workaround: avoid
  warm restart during peak. Fix targeted for DMC 24.4.
- TC-209 is **blocked_by** DEF-1203 and is marked Not Run for 24.3 FOA.

## 5 Required procedures

- MOP-5521 (upgrade cSAEGW-C) is **required** for this release.
- CIQ-8807 provides the environment-specific parameters for FOA.
- See NIR-3310 for the network implementation record.

## 6 Rollout gating

Lab acceptance results **gate** FOA readiness. FOA **precedes** Production. The
acceptance-test summary for 24.3 is in the AAT report (see test-results doc).
