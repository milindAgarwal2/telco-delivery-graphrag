# Defect Register — DMC 24.3

> SYNTHETIC / SANITIZED. Invented defects for a learning project.

## DEF-1187

- **Title:** cSAEGW-C session drop under rapid bearer churn
- **Severity:** Major
- **Status:** Fixed
- **fixed_in:** cSAEGW-C 24.3.0-cp (DMC Release 24.3)
- **Description:** Under rapid bearer add/remove churn, the control plane
  dropped a small percentage of sessions. Resolved by the 24.3 control-plane fix.

## DEF-1203

- **Title:** PCC policy rule counter resets on warm restart
- **Severity:** Major
- **Status:** Open (workaround available)
- **affects:** PCC 7.2.0
- **blocks:** TC-209 (PCC counter persistence), contributes to TC-204 failure
- **observed_alarm:** ALM-SX-DOWN during event-parity divergence
- **Workaround:** Avoid warm restart of the PCC policy engine during the upgrade
  window (see MOP-5521 and the AAT report).
- **target_fix:** DMC Release 24.4

## DEF-1250

- **Title:** cMME spurious re-attach storm
- **Severity:** Minor
- **Status:** Fixed
- **fixed_in:** cMME 24.3.1
- **validated_by:** TC-311 (S1-AP timer alignment)
