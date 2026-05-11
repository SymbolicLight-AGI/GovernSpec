# Annotation agreement

- Protocol: `annotation_protocol.md`
- Unit: `output_sample`
- Annotators: ai_pass_a, ai_pass_b
- Items: 29

| Field | Items | Agreement | Cohen kappa | Krippendorff alpha | Disagreements |
| --- | --- | --- | --- | --- | --- |
| expected_ok | 29 | 100.0% | 1.0 | 1.0 | 0 |
| targeted_assertion | 29 | 82.76% | 0.7917 | 0.7906 | 5 |
| failure_scope | 29 | 93.1% | 0.8612 | 0.8606 | 2 |
| output_format | 29 | 100.0% | 1.0 | 1.0 | 0 |

## Disagreements

### targeted_assertion
- `data_retention_audit__contains.output.md`: {'sample': 'data_retention_audit__contains.output.md', 'ai_pass_a': 'contains', 'ai_pass_b': 'required_sections'}
- `privacy_impact_assessment__no_regex.output.md`: {'sample': 'privacy_impact_assessment__no_regex.output.md', 'ai_pass_a': 'no_regex', 'ai_pass_b': 'not_contains'}
- `support_ticket_triage__max_chars.output.md`: {'sample': 'support_ticket_triage__max_chars.output.md', 'ai_pass_a': 'max_chars', 'ai_pass_b': 'max_words'}
- `qa_test_plan_json__json_path_exists.output.json`: {'sample': 'qa_test_plan_json__json_path_exists.output.json', 'ai_pass_a': 'json_path_exists', 'ai_pass_b': 'json_schema'}
- `vendor_summary_json__contains.output.json`: {'sample': 'vendor_summary_json__contains.output.json', 'ai_pass_a': 'contains', 'ai_pass_b': 'json_schema'}

### failure_scope
- `qa_test_plan_json__json_path_exists.output.json`: {'sample': 'qa_test_plan_json__json_path_exists.output.json', 'ai_pass_a': 'isolated', 'ai_pass_b': 'coupled'}
- `vendor_summary_json__contains.output.json`: {'sample': 'vendor_summary_json__contains.output.json', 'ai_pass_a': 'isolated', 'ai_pass_b': 'coupled'}
