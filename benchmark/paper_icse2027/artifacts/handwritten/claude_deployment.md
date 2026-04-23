# CLAUDE.md

## Project Goal
Review a production deployment plan and produce a go/no-go recommendation.

## Working Constraints
- Do not execute deployment steps.
- Require human approval before destructive operations.

## Allowed and Forbidden Operations
- Web access: forbidden
- Network access: forbidden
- Filesystem read: allowed
- Filesystem write: forbidden
- Tool send_email: forbidden
- Tool delete_file: forbidden

## Human Confirmation Rules
- Deployment touches production -> ask_confirmation
- Destructive operation is requested -> ask_confirmation

## Output Expectations
- Format: markdown
- Language: en
- Max words: 160
- Section: Decision
- Section: Approval Gates
- Section: Risks
- Section: Rollback Plan

## Verification
- All sections must be present
