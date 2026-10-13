# HLD — High-Level Design: DMC Packet Core (Release 24.x)

> SYNTHETIC / SANITIZED. Invented design for a learning project.

## 1 Overview

High-level design of the cloud-native packet core delivered under the DMC
program. Describes the network functions, their interfaces, and the environment
progression used for acceptance.

## 2 Network functions

- **cSAEGW-C** — control plane of the combined SAE gateway. Runs software
  versions per release (24.3.0-cp in Release 24.3).
- **cSAEGW-U** — user plane of the combined SAE gateway.
- **cMME** — mobility management entity.
- **PCC** — policy control component.
- **PCG** — charging gateway.

## 3 Interfaces

| Interface | Between | Monitored by |
|---|---|---|
| Sx | cSAEGW-C ↔ cSAEGW-U | ALM-SX-DOWN |
| S1-AP | cMME ↔ access | ALM-S1AP-TIMER |
| charging | PCG | ALM-PCG-CHG |

## 4 Environment model

Lab, FOA, and Production. Each network function is deployed_on a CNIS cluster per
environment. Lab results gate FOA; FOA precedes Production.

## 5 Delivery lifecycle

Requirements → Design (this HLD) → Deployment (MOP/CIQ) → Upgrade → Acceptance
Testing (AAT) → Incident Resolution (runbooks/defects) → Handover (NIR).
