# Release Note — SAEGW-C 24.3.0-cp

> SYNTHETIC / SANITIZED. Per-CNF release note invented for a learning project.
> This note covers ONLY the SAEGW-C control-plane network function. The
> assembled program view (which CNF versions are certified together for CNPD
> Release 24.3) lives in the integration matrix, not here.

## Identity

- Network function: **SAEGW-C** (control plane of the combined SAE gateway)
- Software version: **24.3.0-cp**
- Vendor stream: Packet Core Control (synthetic)

## Features in this version

- **Sx event-parity (EVM):** event-based monitoring records on the Sx interface
  now match between control and user plane. Validated by test case TC-204.
- **Control-plane session-handling fix** for rapid bearer churn.

## Defects fixed in this version

- **DEF-1187** — SAEGW-C session drop under rapid bearer churn. Resolved by the
  24.3.0-cp control-plane fix. Severity Major; status Fixed.

## Known issues

- Event-parity (TC-204) can fail if a dependent policy component (PCC) performs
  a warm restart during the upgrade window. The root cause is a PCC defect
  (DEF-1203) tracked in the PCC release note — not a SAEGW-C defect. Avoid PCC
  warm restart during the SAEGW-C upgrade.

## Related procedures

- Upgrade is performed via **MOP-5521**.
- FOA parameters for SAEGW-C are in **CIQ-8807**.
