import { spawn } from "node:child_process";
import * as path from "node:path";
import * as vscode from "vscode";

const DIAGNOSTIC_SOURCE = "IntentSpec";
const COMPILE_TARGETS = [
  "agents-md",
  "claude-md",
  "cursor-rules",
  "openai-structured",
  "gemini-structured",
  "mcp-plan",
  "antigravity-rules",
];

export function activate(context: vscode.ExtensionContext): void {
  const diagnostics = vscode.languages.createDiagnosticCollection(DIAGNOSTIC_SOURCE);
  const outputChannel = vscode.window.createOutputChannel("IntentSpec");

  context.subscriptions.push(diagnostics, outputChannel);
  context.subscriptions.push(
    vscode.commands.registerCommand("intentspec.validateCurrentFile", async () => {
      await validateCurrentFile(diagnostics, outputChannel);
    }),
    vscode.commands.registerCommand("intentspec.inspectCurrentFile", async () => {
      await inspectCurrentFile(outputChannel);
    }),
    vscode.commands.registerCommand("intentspec.compileCurrentFile", async () => {
      await compileCurrentFile(outputChannel);
    }),
    vscode.commands.registerCommand("intentspec.testOutput", async () => {
      await testOutput(outputChannel);
    }),
    vscode.commands.registerCommand("intentspec.showMcpSetupSnippet", async () => {
      await showMcpSetupSnippet();
    })
  );
}

export function deactivate(): void {}

async function validateCurrentFile(
  diagnostics: vscode.DiagnosticCollection,
  outputChannel: vscode.OutputChannel
): Promise<void> {
  const document = getActiveDocument();
  if (!document) {
    return;
  }
  const result = await runJsonCommand(
    ["validate", document.fileName, "--format", "json"],
    [0, 1]
  );
  applyValidationDiagnostics(document.uri, result, diagnostics);
  outputChannel.appendLine(`Validated ${document.fileName}`);
  const validationResult = result as { ok?: boolean };
  if (validationResult.ok === false) {
    vscode.window.showWarningMessage("IntentSpec validation reported issues.");
    return;
  }
  vscode.window.showInformationMessage("IntentSpec validation completed.");
}

async function inspectCurrentFile(outputChannel: vscode.OutputChannel): Promise<void> {
  const document = getActiveDocument();
  if (!document) {
    return;
  }
  const result = await runJsonCommand(["inspect", document.fileName, "--format", "json"]);
  const inspector = await vscode.workspace.openTextDocument({
    content: JSON.stringify(result, null, 2),
    language: "json",
  });
  outputChannel.appendLine(`Inspected ${document.fileName}`);
  await vscode.window.showTextDocument(inspector, { preview: false });
}

async function compileCurrentFile(outputChannel: vscode.OutputChannel): Promise<void> {
  const document = getActiveDocument();
  if (!document) {
    return;
  }
  const target = await vscode.window.showQuickPick(COMPILE_TARGETS, {
    placeHolder: "Select an IntentSpec compile target",
  });
  if (!target) {
    return;
  }

  const outputPath = defaultOutputPath(document.fileName, target);
  const result = await runTextCommand([
    "compile",
    document.fileName,
    "--target",
    target,
    "--out",
    outputPath,
  ]);
  outputChannel.appendLine(result.stdout || result.stderr);
  vscode.window.showInformationMessage(`IntentSpec compile completed: ${target}`);
}

async function testOutput(outputChannel: vscode.OutputChannel): Promise<void> {
  const document = getActiveDocument();
  if (!document) {
    return;
  }
  const selected = await vscode.window.showOpenDialog({
    canSelectMany: false,
    openLabel: "Select output file to test",
    defaultUri: vscode.Uri.file(path.dirname(document.fileName)),
  });
  if (!selected || selected.length === 0) {
    return;
  }

  const result = await runJsonCommand([
    "test",
    document.fileName,
    "--output",
    selected[0].fsPath,
    "--format",
    "json",
  ], [0, 1, 2]);
  const report = await vscode.workspace.openTextDocument({
    content: JSON.stringify(result, null, 2),
    language: "json",
  });
  outputChannel.appendLine(`Tested ${selected[0].fsPath}`);
  await vscode.window.showTextDocument(report, { preview: false });
}

async function showMcpSetupSnippet(): Promise<void> {
  const mcpCommand = getConfiguredCommand("mcpCommand", "intentspec-mcp");
  const snippet = {
    mcpServers: {
      intentspec: {
        command: mcpCommand,
      },
    },
  };
  const document = await vscode.workspace.openTextDocument({
    content: JSON.stringify(snippet, null, 2),
    language: "json",
  });
  await vscode.window.showTextDocument(document, { preview: false });
}

function getActiveDocument(): vscode.TextDocument | undefined {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    void vscode.window.showWarningMessage("Open an IntentSpec file first.");
    return undefined;
  }
  return editor.document;
}

function defaultOutputPath(filePath: string, target: string): string {
  const directory = path.dirname(filePath);
  if (target === "agents-md") {
    return path.join(directory, "AGENTS.md");
  }
  if (target === "claude-md") {
    return path.join(directory, "CLAUDE.md");
  }
  if (target === "cursor-rules" || target === "antigravity-rules") {
    return directory;
  }
  if (target === "gemini-structured") {
    return path.join(directory, "task.gemini-structured.json");
  }
  if (target === "openai-structured") {
    return path.join(directory, "task.openai-structured.json");
  }
  return path.join(directory, `task.${target}.json`);
}

function getConfiguredCommand(
  key: "intentCommand" | "mcpCommand",
  defaultValue: string
): string {
  return vscode.workspace
    .getConfiguration("intentspec")
    .get<string>(key, defaultValue);
}

async function runJsonCommand(
  args: string[],
  acceptedExitCodes: number[] = [0]
): Promise<unknown> {
  const result = await runCommand(args, acceptedExitCodes);
  const payload = result.stdout || result.stderr;
  if (!payload) {
    throw new Error("IntentSpec command returned no output.");
  }
  return JSON.parse(payload);
}

async function runTextCommand(args: string[]): Promise<{ stdout: string; stderr: string }> {
  const result = await runCommand(args);
  return { stdout: result.stdout, stderr: result.stderr };
}

async function runCommand(
  args: string[],
  acceptedExitCodes: number[] = [0]
): Promise<{ stdout: string; stderr: string }> {
  const intentCommand = getConfiguredCommand("intentCommand", "intent");
  return new Promise((resolve, reject) => {
    const child = spawn(intentCommand, args, {
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code !== null && acceptedExitCodes.includes(code)) {
        resolve({ stdout, stderr });
        return;
      }
      reject(new Error(stderr || stdout || `IntentSpec exited with code ${code}.`));
    });
  });
}

function applyValidationDiagnostics(
  uri: vscode.Uri,
  payload: unknown,
  diagnostics: vscode.DiagnosticCollection
): void {
  const report = payload as {
    errors?: string[];
    warnings?: string[];
    error?: { message?: string };
  };
  const items: vscode.Diagnostic[] = [];

  for (const message of report.errors ?? []) {
    items.push(
      new vscode.Diagnostic(
        new vscode.Range(0, 0, 0, 0),
        message,
        vscode.DiagnosticSeverity.Error
      )
    );
  }
  for (const message of report.warnings ?? []) {
    items.push(
      new vscode.Diagnostic(
        new vscode.Range(0, 0, 0, 0),
        message,
        vscode.DiagnosticSeverity.Warning
      )
    );
  }
  if (items.length === 0 && report.error?.message) {
    items.push(
      new vscode.Diagnostic(
        new vscode.Range(0, 0, 0, 0),
        report.error.message,
        vscode.DiagnosticSeverity.Error
      )
    );
  }

  diagnostics.set(uri, items);
}
