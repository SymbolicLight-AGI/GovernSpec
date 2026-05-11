# reproducibility tables

## Target coverage
| Target | Succeeded | Total |
| --- | --- | --- |
| agents-md | 20 | 20 |
| claude-md | 20 | 20 |
| cursor-rules | 20 | 20 |
| openai-structured | 7 | 20 |
| gemini-structured | 7 | 20 |
| mcp-plan | 20 | 20 |

## Round-trip fidelity
| Source type | Imported | Average field fidelity |
| --- | --- | --- |
| agents-md | 20 | 77.5% |
| claude-md | 20 | 77.5% |
| cursor-rules | 20 | 77.5% |
| gemini-structured | 7 | 47.62% |
| openai-structured | 7 | 47.62% |

## Assertion effectiveness
| Assertion | Targeted samples | Caught | Catch rate |
| --- | --- | --- | --- |
| contains | 6 | 6 | 100.0% |
| json_array_min_items | 2 | 2 | 100.0% |
| json_path_exists | 2 | 2 | 100.0% |
| json_schema | 2 | 2 | 100.0% |
| max_chars | 2 | 2 | 100.0% |
| max_words | 3 | 3 | 100.0% |
| no_regex | 4 | 4 | 100.0% |
| not_contains | 4 | 4 | 100.0% |
| regex | 3 | 3 | 100.0% |
| required_sections | 4 | 4 | 100.0% |

## Assisted annotation agreement
| Field | Items | Agreement | Cohen kappa | Krippendorff alpha |
| --- | --- | --- | --- | --- |
| expected_ok | 29 | 100.0% | 1.0 | 1.0 |
| targeted_assertion | 29 | 82.76% | 0.7917 | 0.7906 |
| failure_scope | 29 | 93.1% | 0.8612 | 0.8606 |
| output_format | 29 | 100.0% | 1.0 | 1.0 |
