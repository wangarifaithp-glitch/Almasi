import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { createServer } from "node:net";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const backend = join(root, "backend");
const isWindows = process.platform === "win32";
const pythonCandidates = isWindows
  ? [join(backend, ".venv", "Scripts", "python.exe"), "python"]
  : [join(backend, ".venv", "bin", "python"), "python3", "python"];

function findPython() {
  return pythonCandidates.find((candidate) =>
    candidate.includes("\\") || candidate.includes("/")
      ? existsSync(candidate)
      : true,
  );
}

function isPortOpen(port) {
  return new Promise((resolvePort) => {
    const socket = createServer();
    socket.once("error", () => resolvePort(false));
    socket.once("listening", () => {
      socket.close(() => resolvePort(true));
    });
    socket.listen(port, "127.0.0.1");
  });
}

const python = findPython();
if (!python) {
  console.error(
    "ALMASI could not find Python. Create backend\\.venv and install backend\\requirements.txt first.",
  );
  process.exit(1);
}

if (!(await isPortOpen(8000))) {
  console.error(
    "ALMASI could not start the backend because port 8000 is already in use.",
  );
  process.exit(1);
}

const children = [];
let shuttingDown = false;

function stopChildren(exitCode = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of children) {
    if (!child.killed) child.kill();
  }
  setTimeout(() => process.exit(exitCode), 250);
}

const backendProcess = spawn(
  python,
  ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
  { cwd: backend, stdio: "inherit", windowsHide: false },
);
children.push(backendProcess);

backendProcess.once("error", (error) => {
  console.error(`ALMASI backend failed to start: ${error.message}`);
  stopChildren(1);
});
backendProcess.once("exit", (code) => {
  if (!shuttingDown && code !== 0) {
    console.error(`ALMASI backend stopped unexpectedly (exit code ${code ?? "unknown"}).`);
    stopChildren(code || 1);
  }
});

const frontendProcess = spawn(
  process.execPath,
  [join(root, "node_modules", "vite", "bin", "vite.js")],
  { cwd: root, stdio: "inherit", windowsHide: false },
);
children.push(frontendProcess);

frontendProcess.once("error", (error) => {
  console.error(`ALMASI frontend failed to start: ${error.message}`);
  stopChildren(1);
});
frontendProcess.once("exit", (code) => {
  if (!shuttingDown && code !== 0) stopChildren(code || 1);
});

process.on("SIGINT", () => stopChildren());
process.on("SIGTERM", () => stopChildren());
