# Agent Operational Guidelines

This document provides actionable instructions for AI agents working on the `on-the-board` project. Agents must use these guidelines to ensure all tasks, code, and documentation align with the [Project Constitution](.specify/memory/constitution.md).

## 1. Verifiable Truth
*Reference: [Verifiable Truth Principle](.specify/memory/constitution.md#verifiable-truth)*

When generating content, reports, or data structures:
- **Fact vs. Interpretation**: You MUST explicitly distinguish between verifiable data (e.g., official votes, resolution numbers) and interpretative text (e.g., opinions, reasoning).
- **Evidence Requirement**: Do not state a fact unless you can point to a specific source or file within the codebase/environment.
- **No Hallucination**: If information is missing, state that it is unavailable rather than attempting to infer it.

## 2. Maintenance Efficiency
*Reference: [Maintenance Efficiency Principle](.specify/memory/constitution.md#maintenance-efficiency)*

When proposing solutions or writing code:
- **Automation Hierarchy**: Before implementing a manual workflow, evaluate if it can be automated (e.g., via a cron job, GitHub Action, or script). Prioritize 1. Fully automated, 2. Semi-automated, 3. Manual.
- **Minimize Human Intervention**: Always prefer the "Fully Automated" tier. If a task requires human kickoff, document exactly what that trigger is and how it could eventually be removed.
- **Scalability**: Avoid hardcoding logic that would require manual updates if the municipality changes.

## 3. Geographic Adaptability
*Reference: [Geographic Adaptability Principle](.specify/memory/constitution.md#geographic-adaptability)*

When writing code or configuration:
- **Modular Design**: Treat "Victor, NY" as a parameter, not a constant. Use environment variables or `.json` configurations to define locality.
- **Portable Logic**: Ensure that logic used for parsing Victor's data can be applied to another town with minimal changes to the codebase.

## 4. Compliance Checklist for Tasks
Before marking a task as `completed`, an agent should verify:
- [ ] Does this output/code introduce any unverified claims?
- [ ] Have I prioritized automation over manual steps?
- [ ] Is the geographic logic decoupled from the core implementation?
