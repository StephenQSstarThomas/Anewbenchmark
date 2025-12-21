# AgentXploit Benchmark Project

## Objective

Build a benchmark to measure AgentXploit's effectiveness in exploiting vulnerabilities in AI agent frameworks through end-to-end testing.

## Primary Goal

Create verifiable vulnerability examples from agent frameworks, package them into Docker containers, and validate end-to-end exploitation capabilities with AgentXploit.

## Workflow

1. **Vulnerability Identification**
   - Source CVE list from `shiqiu/cves/agent-related.xlsx`
   - Extract agent versions and review GitHub documentation
   - Document vulnerability details

2. **Exploitation Assessment**
   - Evaluate feasibility of exploitation
   - Determine attack vectors

3. **Benchmark Instance Creation**
   - Design Docker-packaged agent architecture
   - Write agent runtime code
   - Implement interaction interface

4. **Verification** (In Progress)
   - Build automated verifier for exploit validation

## Current Status

### Completed Instances

**AutoGPT v0.4.2**
- Location: `/home/shiqiu/Anewbenchmark/AutoGPT_0.4.2`
- Setup: Configure `.env` file
- Interaction: `/home/shiqiu/Anewbenchmark/AutoGPT_0.4.2/autogpt/workspace/auto_gpt_workspace`
- Status: Ready for vulnerability verification

## Next Steps

### Immediate Tasks
- [ ] Complete automated verifier implementation
- [ ] Document Docker run commands for AutoGPT 0.4.2
- [ ] Verify exploitability of identified vulnerabilities
- [ ] Extract and document specific CVE mappings

### Pipeline Tasks
- [ ] Identify next agent framework from CVE list
- [ ] Build additional benchmark instances
- [ ] Standardize Docker packaging process
- [ ] Create verification test suite

### Documentation Tasks
- [ ] Document AutoGPT 0.4.2 setup process
- [ ] Create vulnerability reproduction guide
- [ ] Define benchmark evaluation metrics
- [ ] Write AgentXploit integration guidelines

## Structure

```
/home/shiqiu/Anewbenchmark/
├── AutoGPT_0.4.2/              # Benchmark instance
│   ├── .env                     # Configuration (to be set)
│   └── autogpt/workspace/       # Vulnerability testing interface
├── AutoGPT_0.5.0/              # Additional version
└── gpt-researcher/             # Additional framework
```

## Notes

- Focus on reproducible, containerized vulnerability examples
- Prioritize end-to-end exploitation validation
- Maintain clear documentation for each instance
