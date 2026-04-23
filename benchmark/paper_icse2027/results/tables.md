# ICSE paper tables

## Target coverage
| Target | Succeeded | Total |
| --- | --- | --- |
| agents-md | 8 | 8 |
| claude-md | 8 | 8 |
| cursor-rules | 8 | 8 |
| openai-structured | 3 | 8 |
| gemini-structured | 3 | 8 |
| mcp-plan | 8 | 8 |

## Round-trip fidelity
| Source type | Imported | Average field fidelity |
| --- | --- | --- |
| agents-md | 8 | 77.08% |
| claude-md | 8 | 77.08% |
| cursor-rules | 8 | 77.08% |
| gemini-structured | 3 | 44.44% |
| openai-structured | 3 | 44.44% |

## Assertion effectiveness
| Assertion | Targeted samples | Caught | Catch rate |
| --- | --- | --- | --- |
| contains | 1 | 1 | 100.0% |
| json_array_min_items | 1 | 1 | 100.0% |
| json_path_exists | 1 | 1 | 100.0% |
| json_schema | 1 | 1 | 100.0% |
| max_chars | 1 | 1 | 100.0% |
| max_words | 1 | 1 | 100.0% |
| no_regex | 1 | 1 | 100.0% |
| not_contains | 1 | 1 | 100.0% |
| regex | 1 | 1 | 100.0% |
| required_sections | 1 | 1 | 100.0% |
