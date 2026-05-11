from __future__ import annotations

import json
from pathlib import Path

from governspec_mcp.server import handle_message

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def test_initialize_returns_server_info() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert response is not None
    assert response["result"]["serverInfo"]["name"] == "governspec-mcp"


def test_tools_list_returns_four_tools() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    assert response is not None
    assert len(response["result"]["tools"]) == 4


def test_validate_tool_returns_report() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "governspec.validate",
                "arguments": {"path": str(EXAMPLES / "customer_brief.govern.yaml")},
            },
        }
    )
    assert response is not None
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["ok"] is True


def test_validate_tool_supports_govern_pack() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "governspec.validate",
                "arguments": {"path": str(EXAMPLES / "packs" / "privacy.govern.yaml")},
            },
        }
    )
    assert response is not None
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["ok"] is True


def test_spec_resource_returns_yaml_for_workspace_govern_file() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": f"govern://spec/{EXAMPLES / 'customer_brief.govern.yaml'}"},
        }
    )
    assert response is not None
    content = response["result"]["contents"][0]
    assert content["mimeType"] == "application/yaml"
    assert 'kind: "GovernSpec"' in content["text"]


def test_resource_read_returns_iir_json() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": f"govern://iir/{EXAMPLES / 'customer_brief.govern.yaml'}"},
        }
    )
    assert response is not None
    payload = json.loads(response["result"]["contents"][0]["text"])
    assert payload["normalized_goal"]


def test_spec_resource_rejects_non_govern_files() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": f"govern://spec/{ROOT / 'README.md'}"},
        }
    )
    assert response is not None
    assert "error" in response
    assert "invalid yaml" in response["error"]["message"].lower()


def test_spec_resource_rejects_paths_outside_workspace(tmp_path: Path) -> None:
    outside_file = tmp_path / "outside.govern.yaml"
    outside_file.write_text(
        (EXAMPLES / "customer_brief.govern.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": f"govern://spec/{outside_file}"},
        }
    )
    assert response is not None
    assert "error" in response
    assert "current working directory" in response["error"]["message"]


def test_inspect_tool_rejects_semantically_invalid_spec() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "governspec.inspect",
                "arguments": {
                    "path": str(EXAMPLES / "invalid_dangerous_permission.govern.yaml")
                },
            },
        }
    )
    assert response is not None
    assert "error" in response
    assert "High-risk tool permissions" in response["error"]["message"]


def test_compile_tool_rejects_semantically_invalid_spec() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "governspec.compile",
                "arguments": {
                    "path": str(EXAMPLES / "invalid_dangerous_permission.govern.yaml"),
                    "target": "agents-md",
                },
            },
        }
    )
    assert response is not None
    assert "error" in response
    assert "High-risk tool permissions" in response["error"]["message"]


def test_compiled_resource_returns_text_artifact() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {
                "uri": f"govern://compiled/claude-md/{EXAMPLES / 'code_review.govern.yaml'}"
            },
        }
    )
    assert response is not None
    content = response["result"]["contents"][0]
    assert content["mimeType"] == "text/markdown"
    assert "# CLAUDE.md" in content["text"]


def test_compiled_resource_returns_bundle_artifact() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {
                "uri": f"govern://compiled/cursor-rules/{EXAMPLES / 'code_review.govern.yaml'}"
            },
        }
    )
    assert response is not None
    payload = json.loads(response["result"]["contents"][0]["text"])
    assert payload["kind"] == "bundle"
    assert ".cursor/rules/governspec.mdc" in payload["files"]


def test_iir_resource_rejects_semantically_invalid_spec() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {
                "uri": (
                    f"govern://iir/{EXAMPLES / 'invalid_dangerous_permission.govern.yaml'}"
                )
            },
        }
    )
    assert response is not None
    assert "error" in response
    assert "High-risk tool permissions" in response["error"]["message"]


def test_compiled_resource_rejects_semantically_invalid_spec() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {
                "uri": (
                    "govern://compiled/agents-md/"
                    f"{EXAMPLES / 'invalid_dangerous_permission.govern.yaml'}"
                )
            },
        }
    )
    assert response is not None
    assert "error" in response
    assert "High-risk tool permissions" in response["error"]["message"]


def test_tool_errors_return_json_rpc_error() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "governspec.test",
                "arguments": {
                    "path": str(EXAMPLES / "report_json.govern.yaml"),
                    "output_path": str(EXAMPLES / "missing.output.json"),
                },
            },
        }
    )
    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == -32000


def test_test_tool_rejects_semantically_invalid_spec(tmp_path: Path) -> None:
    output_file = tmp_path / "invalid.output.md"
    output_file.write_text("# Summary\n\nHello\n", encoding="utf-8")
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "governspec.test",
                "arguments": {
                    "path": str(EXAMPLES / "invalid_dangerous_permission.govern.yaml"),
                    "output_path": str(output_file),
                },
            },
        }
    )
    assert response is not None
    assert "error" in response
    assert "High-risk tool permissions" in response["error"]["message"]


def test_test_tool_rejects_output_paths_outside_workspace(tmp_path: Path) -> None:
    outside_output = tmp_path / "outside.output.json"
    outside_output.write_text(
        (EXAMPLES / "report_json.output.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "governspec.test",
                "arguments": {
                    "path": str(EXAMPLES / "report_json.govern.yaml"),
                    "output_path": str(outside_output),
                },
            },
        }
    )
    assert response is not None
    assert "error" in response
    assert "current working directory" in response["error"]["message"]


def test_compiled_resource_errors_return_json_rpc_error() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {
                "uri": f"govern://compiled/unknown-target/{EXAMPLES / 'code_review.govern.yaml'}"
            },
        }
    )
    assert response is not None
    assert response["error"]["code"] == -32000
