<!-- 
<sync_impact_report>
Version change: N/A → 1.0.0
Modified principles: None (initial population)
Added sections: Implementation Scope, Maintenance & Automation
Removed sections: None
Templates requiring updates: 
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
Follow-up TODOs: None
</sync_impact_report>
-->
# on-the-board Constitution

## Core Principles

### Verifiable Truth
Distinguish clearly between verifiable facts (e.g., official votes, resolutions) and less verifiable information (e.g., interpretations, opinions). Do not fabricate or imputually represent facts not supported by evidence.

### Maintenance Efficiency
Prioritize the lowest reasonable amount of human effort for data maintenance. The hierarchy of implementation preference is: 1. Fully automated (no intervention), 2. Semi-automated (human kickoff or minor oversight), 3. Manual effort (last resort).

### Geographic Adaptability
While currently focused on the local municipality of Victor, NY, all components must be designed to allow for easy forking and adaptation to other localities.

## Implementation Scope

The current scope is limited to Victor, NY. Data collection pipelines and reporting mechanisms should be modular and decoupled from specific geographic identifiers to facilitate expansion.

## Maintenance & Automation

Development efforts shall focus on creating autonomous data ingestion jobs. The roadmap for any new feature must include an assessment of its maintenance overhead and a plan to move it up the automation hierarchy (from manual to semi-automated to fully automated).

## Governance

All information presented must be audited for compliance with the principle of Verifiable Truth. Automated validation/linting should be implemented to check for clearly distinguishable truth claims in data outputs. Any amendment to a Core Principle MUST be accompanied by a corresponding update to the operational instructions in `AGENTS.md` to ensure agent compliance.

**Version**: 1.0.0 | **Ratified**: 2026-08-02 | **Last Amended**: 2026-08-02
