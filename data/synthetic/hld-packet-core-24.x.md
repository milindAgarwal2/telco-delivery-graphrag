# HLD — High-Level Design: CNPD Packet Core (Release 24.x)

> SYNTHETIC / SANITIZED. Invented design for a learning project.

## 1 Overview

High-level design of the cloud-native packet core delivered under the CNPD
program. Describes the network functions, their interfaces, and the environment
progression used for acceptance.

## 2 Network functions

- **SAEGW-C** — control plane of the combined SAE gateway. Runs software
  versions per release (24.3.0-cp in Release 24.3).
- **SAEGW-U** — user plane of the combined SAE gateway.
- **MME** — mobility management entity.
- **PCC** — policy control component.
- **PCG** — charging gateway.

## 3 Interfaces

| Interface | Between | Monitored by |
|---|---|---|
| Sx | SAEGW-C ↔ SAEGW-U | ALM-SX-DOWN |
| S1-AP | MME ↔ access | ALM-S1AP-TIMER |
| charging | PCG | ALM-PCG-CHG |

## 4 Environment model

Lab, FOA, and Production. Each network function is deployed_on a CaaS cluster per
environment. Lab results gate FOA; FOA precedes Production.

## 5 Delivery lifecycle

Requirements → Design (this HLD) → Deployment (MOP/CIQ) → Upgrade → Acceptance
Testing (AAT) → Incident Resolution (runbooks/defects) → Handover (NIR).
