const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = path.resolve(__dirname, "..");
const runtime = path.join(root, "python-runtime");
const candidates = process.platform === "win32"
  ? ["py", "python", "python3"]
  : ["python3", "python"];

function findPython() {
  for (const candidate of candidates) {
    const result = spawnSync(candidate, ["--version"], { stdio: "ignore", shell: process.platform === "win32" });
    if (result.status === 0) return candidate;
  }
  throw new Error("Python 3 is required to create the bundled runtime");
}

fs.rmSync(runtime, { recursive: true, force: true });
const python = findPython();
let result = spawnSync(python, ["-m", "venv", runtime], { cwd: root, stdio: "inherit", shell: process.platform === "win32" });
if (result.status !== 0) process.exit(result.status || 1);

const runtimePython = process.platform === "win32"
  ? path.join(runtime, "Scripts", "python.exe")
  : path.join(runtime, "bin", "python3");

result = spawnSync(runtimePython, ["-m", "pip", "install", "--upgrade", "pip"], { cwd: root, stdio: "inherit" });
if (result.status !== 0) process.exit(result.status || 1);
result = spawnSync(runtimePython, ["-m", "pip", "install", "-r", path.join(root, "requirements.txt")], { cwd: root, stdio: "inherit" });
if (result.status !== 0) process.exit(result.status || 1);

const resources = path.join(runtime, "resources", "stanza");
fs.mkdirSync(resources, { recursive: true });
result = spawnSync(runtimePython, [
  "-c",
  `import stanza; stanza.download("ca", model_dir=${JSON.stringify(resources)}, verbose=False)`,
], { cwd: root, stdio: "inherit" });
process.exit(result.status || 0);
