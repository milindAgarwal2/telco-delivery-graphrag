# CIQ-8807 — Customer Information Questionnaire (FOA parameters, DMC 24.3)

> SYNTHETIC / SANITIZED. All values invented for a learning project. No real
> addresses, node names, or customer data.

## Overview

This CIQ provides environment-specific parameters for the FOA rollout of DMC
Release 24.3. It **describes** the configuration consumed by MOP-5521.

## Environment: FOA

| Parameter | Value (synthetic) | Notes |
|---|---|---|
| Environment name | FOA-SITE-A | first office application |
| cSAEGW-C pool size | 3 | control-plane pods |
| Sx heartbeat interval | 5 s | aligns with event-parity |
| PCC policy profile | PROF-24.3-default | from PCC 7.2.0 |
| Charging gateway (PCG) endpoint | pcg-foa.example.invalid | placeholder only |

## Dependencies

- Requires the certified software versions from the DMC 24.3 Integration & Compatibility Matrix.
- cSAEGW-C must be at 24.3.0-cp (see MOP-5521).
- FOA is **gated_by** lab acceptance results.

## Validation

Parameters are validated by test cases TC-204 (event-parity) and TC-311 (S1-AP
timer). A blocked parameter path is tracked under DEF-1203.
