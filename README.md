# CoreChain: Securing Federated Learning Data Using Blockchain Technology

**Final Year Project**  
**Institution:** Ghulam Ishaq Khan Institute of Engineering Sciences and Technology (GIKI)

### Group Members
- Saad Hanif Taj
- Aiza Azeem
- Dua E Zahra
- Mahad Ali

---

## Project Overview

CoreChain is a distributed enterprise architecture that resolves the critical privacy and security vulnerabilities surrounding collaborative machine learning, specifically for healthcare data. By integrating **Federated Machine Learning**, **Paillier Homomorphic Encryption**, and **Blockchain Smart Contracts**, this system enables multiple institutions (e.g., hospitals) to collaboratively train robust AI models without ever exposing raw proprietary datasets or vulnerable parameters.

### Core Features

1. **Federated Learning (Flower):** Decentralized ML paradigm where hospital nodes compute exact parameter gradients locally rather than centralizing patient data.
2. **Homomorphic Encryption (Paillier):** Complete mathematical array obfuscation of model weights. The global aggregator performs `FedAvg` integrations strictly on encrypted matrices.
3. **Immutable Auditing (Blockchain):** Custom Python Proof-of-Work distributed ledger that immutably logs Node Registrations, Model Updates, Aggregations, and exact Accuracy hashes per round.
4. **Smart Contracts:** Deterministic code that validates model integrity and accurately distributes reward tokens proportional to the data quantity and contribution quality of each connected hospital.
5. **Real-time Analytics Web Dashboard:** A `Chart.js` tracking interface fully authenticated via standard RBAC JWTs displaying Leaderboards, Training Metrics, and Audit Trails live over web-proxied sockets.

## System Architecture

- **AWS Central Aggregator Node:** Houses the FastAPI REST gateways, the global Flower orchestration server, and the CoreChain blockchain backend securely routed inside `supervisord` + `NGINX` Docker containers.
- **Client Hospital Nodes:** Python edge processes that handle local `TensorFlow` datasets efficiently while handling secure two-way gRPC handshakes.

---

*This repository contains the full architecture implementation code.*
