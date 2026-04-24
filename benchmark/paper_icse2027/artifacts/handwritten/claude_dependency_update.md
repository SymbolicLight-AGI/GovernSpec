# CLAUDE.md

## Project Goal
Review a dependency update proposal for compatibility and rollout risks.

## Working Constraints
- Do not install packages.
- Do not change lockfiles.
- Do not use network access.

## Allowed and Forbidden Operations
- Web access: forbidden
- Network access: forbidden
- Filesystem read: allowed
- Filesystem write: forbidden

## Output Expectations
- Format: markdown
- Language: en
- Max words: 130
- Section: Compatibility
- Section: Security Notes
- Section: Rollout Risk
- Section: Test Plan

## Verification
- Network install must be ruled out

