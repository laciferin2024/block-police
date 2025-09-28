# BlockPolice Flow.md

Below is a step-by-step narrative using Mermaid sequence diagrams, illustrating a complete user flow—from starting the chat with the BlockPolice agent in Agentverse.ai, through incident investigation, report & SBT issuance, and DEX compliance.

---

## Sequence Diagram: BlockPolice Incident Response

```mermaid
sequenceDiagram
    participant User as Victim
    participant Agentverse as Agentverse.ai
    participant BPAgent as BlockPolice Agent
    participant ENSAPI as ENS MCP/Graph Protocol
    participant HederaAPI as Hedera MCP
    participant AIKG as AI Reasoning (uAgents/MeTTa KG)
    participant SBT as SBT Contract
    participant DEX as Compliant DEX/Service

    %% User starts chat interface in Agentverse.ai
    User->>Agentverse: "Open chat with block-police.eth"
    Agentverse->>BPAgent: "Connect & prompt for complaint"
    BPAgent->>User: "Describe your incident (wallet, ENS, timeline, what happened)"

    %% User files complaint
    User->>BPAgent: "My ENS is vitalik.eth, assets drained; suspected tx at 0xabc..."
    BPAgent->>AIKG: "Parse complaint, extract details, validate format"

    %% Resolve ENS, fetch on-chain history
    BPAgent->>ENSAPI: "Resolve vitalik.eth to address; get recent tx, counterparties"
    ENSAPI-->>BPAgent: "Address, tx history, counterparties"

    %% Fetch Hedera data if needed
    BPAgent->>HederaAPI: "Fetch account tx, balances, NFTs from Hedera testnet (if relevant)"
    HederaAPI-->>BPAgent: "Account info, suspicious tx"

    %% AI Evidence Analysis & Abuse Pattern Detection
    BPAgent->>AIKG: "Run heuristics, cluster attackers, trace asset transfers, assign confidence"
    AIKG-->>BPAgent: "Entity graph, timeline, flagged wallets, incident type"

    %% Market price for damage calculation
    BPAgent->>ENSAPI: "Fetch token market price from MCP/Subgraph"
    ENSAPI-->>BPAgent: "Token price (USD/ETH)"
    BPAgent->>AIKG: "Calculate total monetary loss"
    AIKG-->>BPAgent: "Damage summary"

    %% Prepare report, assign unique case number
    BPAgent->>BPAgent: "Compose incident report, assign incident ID (like BPI-2025-1234)"
    BPAgent->>SBT: "Issue SBT to implicated attacker/fraud wallets, encode case ID"
    SBT-->>BPAgent: "SBT minted & visible on-chain"

    %% Notify DEX/service for compliance
    BPAgent->>DEX: "Flagged address – Check SBT registry for red-flag status"
    DEX-->>BPAgent: "Service blocks / pauses flagged address"

    %% Incident closure and followup
    BPAgent->>User: "Report, case ID & flagged wallet summary delivered (PDF/Markdown); link for future appeals"
```

---

## Flow Summary

- **User** begins chat with BlockPolice agent via Agentverse.ai.
- The agent collects the complaint, parses details, validates incident, and uses ENS and Hedera MCPs to gather all relevant evidence.
- AI knowledge graph (MeTTa/uAgents) analyzes data—detects attack patterns, traces flows, clusters actors, and calculates financial impact.
- BlockPolice agent generates a timestamped incident report, assigns a unique incident number, and issues SBTs marking each flagged wallet.
- Compliant DEXes/services check the SBT registry and block pause flagged addresses.
- Incident closure and appeal status handled via chat and linked action.

---

**This document details the full technical and user-facing sequence for BlockPolice's AI blockchain investigator, suitable for both demos and audits.**