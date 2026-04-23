import { spawn } from "node:child_process";

export interface IntentCommandResult {
  code: number | null;
  stdout: string;
  stderr: string;
}

async function runIntent(args: string[]): Promise<IntentCommandResult> {
  return new Promise((resolve, reject) => {
    const child = spawn("intent", args, {
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
      resolve({ code, stdout, stderr });
    });
  });
}

function parseJsonResult(result: IntentCommandResult): unknown {
  const payload = result.stdout || result.stderr;
  if (!payload) {
    throw new Error(
      `Intent command exited with code ${result.code} and produced no output.`
    );
  }
  try {
    return JSON.parse(payload);
  } catch {
    throw new Error(
      `Intent command did not return JSON. exit=${result.code} stdout=${result.stdout} stderr=${result.stderr}`
    );
  }
}

function ensureSuccess(result: IntentCommandResult): void {
  if (result.code === 0) {
    return;
  }
  throw new Error(
    `Intent command failed. exit=${result.code} stdout=${result.stdout} stderr=${result.stderr}`
  );
}

export async function validateJson(path: string): Promise<unknown> {
  const result = await runIntent(["validate", path, "--format", "json"]);
  return parseJsonResult(result);
}

export async function inspectJson(path: string): Promise<unknown> {
  const result = await runIntent(["inspect", path, "--format", "json"]);
  return parseJsonResult(result);
}

export async function testJson(path: string, outputPath: string): Promise<unknown> {
  const result = await runIntent(["test", path, "--output", outputPath, "--format", "json"]);
  return parseJsonResult(result);
}

export async function doctorJson(): Promise<unknown> {
  const result = await runIntent(["doctor", "--format", "json"]);
  return parseJsonResult(result);
}

export async function compileText(path: string, target: string): Promise<string> {
  const result = await runIntent(["compile", path, "--target", target]);
  ensureSuccess(result);
  return result.stdout;
}

export async function compileToFile(
  path: string,
  target: string,
  outputPath: string
): Promise<IntentCommandResult> {
  const result = await runIntent(["compile", path, "--target", target, "--out", outputPath]);
  ensureSuccess(result);
  return result;
}
