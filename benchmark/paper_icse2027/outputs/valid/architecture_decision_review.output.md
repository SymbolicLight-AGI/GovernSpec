## Decision
The ADR recommends consolidating queue workers.

## Alternatives
It compares a shared worker pool with dedicated service workers.

## Tradeoffs
The shared pool reduces operations cost but increases blast radius.

## Open Questions
Open question: what rollback signal will trigger worker isolation?

