---

```markdown
# BlockPolice Incident Response Workflow

## Mermaid Sequence Diagram
```

sequenceDiagram
participant User
participant Agentverse
participant BlockPolice Agent
participant MCP Servers (ENS/Hedera/Graph)
participant MeTTa Knowledge Graph
participant Supabase DB
participant SBT Registry
participant DEX/Service

    User->>Agentverse: Start chat with block-police.eth agent
    Agentverse->>BlockPolice Agent: Initiate conversation context
    User->>BlockPolice Agent: Submit incident complaint (natural language)
    BlockPolice Agent->>MCP Servers (ENS/Hedera/Graph): Retrieve all relevant on-chain evidence
    MCP Servers (ENS/Hedera/Graph)-->>BlockPolice Agent: Transmit addresses, transactions, tokens, NFTs data
    BlockPolice Agent->>MeTTa Knowledge Graph: Entity/relationship reasoning, cluster wallets, parse attacker behaviors
    BlockPolice Agent->>Supabase DB: Log complaint, investigation runs, build incident case file
    BlockPolice Agent->>BlockPolice Agent: Generate summary, assign unique incident ID
    BlockPolice Agent->>SBT Registry: Issue SBT (flags marked wallets, embeds incident ID)
    SBT Registry-->>DEX/Service: Publicly exposes flagged status for attacker wallets
    DEX/Service->>SBT Registry: Lookup/join registry, block/flag marked wallets
    BlockPolice Agent->>User: Return case report, incident status, next steps via chat

```

---

### Notes

- The user communicates with BlockPolice via chat at Agentverse.ai, providing complaint details.
- The BlockPolice Agent orchestrates data requests with multiple MCP servers—resolving ENS, fetching Hedera testnet data, and pricing tokens.
- MeTTa Knowledge Graph clusters wallets, reasons over relationships, and identifies suspicious activity.
- Supabase database stores all logs, reports, and the incident file.
- SBT Registry issues soulbound incident tokens to implicated wallets, recognized by multiple services for blocking.
- DEX/services continuously sync with SBT Registry—new SBTs trigger wallet blocklisting as part of compliance.
- The user receives an actionable report and status updates in the chat interface.

---
```
