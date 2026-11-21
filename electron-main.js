const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

let mainWindow;

function pythonExecutable() {
  if (process.platform === "win32") {
    const candidates = [
      path.join(process.resourcesPath, "python-runtime", "Scripts", "python.exe"),
      path.join(process.resourcesPath, "python-runtime", "python.exe"),
      path.join(app.getAppPath(), "python-runtime", "Scripts", "python.exe"),
    ];
    const found = candidates.find((candidate) => fs.existsSync(candidate));
    if (found) return found;
  } else {
    const candidates = [
      path.join(process.resourcesPath, "python-runtime", "bin", "python3"),
      path.join(process.resourcesPath, "python-runtime", "bin", "python"),
      path.join(app.getAppPath(), "python-runtime", "bin", "python3"),
    ];
    const found = candidates.find((candidate) => fs.existsSync(candidate));
    if (found) return found;
  }
  return process.platform === "win32" ? "python" : "python3";
}

function runWorker(args, input, onLine) {
  const script = app.isPackaged
    ? path.join(process.resourcesPath, "app.asar.unpacked", "desktop_worker.py")
    : path.join(__dirname, "desktop_worker.py");
  const cwd = app.isPackaged
    ? path.dirname(script)
    : __dirname;
  const stanzaResources = app.isPackaged
    ? path.join(process.resourcesPath, "python-runtime", "resources", "stanza")
    : path.join(app.getAppPath(), "python-runtime", "resources", "stanza");

  return new Promise((resolve, reject) => {
    const child = spawn(pythonExecutable(), [script, ...args], {
      cwd,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1",
        STANZA_RESOURCES_DIR: stanzaResources,
        TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD: "1",
      },
    });
    let stderr = "";
    let stdout = "";
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
      for (const line of chunk.split(/\r?\n/).filter(Boolean)) {
        try {
          const message = JSON.parse(line);
          if (onLine) onLine(message);
        } catch {
          if (onLine) onLine({ event: "log", message: line });
        }
      }
    });
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve({ stdout, stderr });
      else reject(new Error(stderr.trim() || `Python worker exited with code ${code}`));
    });
    if (input !== undefined) child.stdin.end(JSON.stringify(input), "utf8");
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1180,
    height: 820,
    minWidth: 820,
    minHeight: 640,
    icon: path.join(__dirname, "static", "favicon.png"),
    webPreferences: {
      preload: path.join(__dirname, "electron-preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

ipcMain.handle("catalog:get", async () => {
  let catalog;
  await runWorker(["catalog"], undefined, (message) => {
    if (message.event === "catalog") catalog = message.sources;
  });
  return catalog || [];
});

ipcMain.handle("output:choose", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "Tria el directori del corpus",
    properties: ["openDirectory", "createDirectory"],
  });
  if (result.canceled) return null;
  return result.filePaths[0];
});

ipcMain.handle("corpus:start", async (event, payload) => {
  const sender = event.sender;
  try {
    await runWorker(["run"], payload, (message) => {
      sender.send("corpus:progress", message);
    });
  } catch (error) {
    sender.send("corpus:progress", { event: "error", message: error.message });
  }
});

ipcMain.handle("folder:open", async (event, folder) => {
  if (!folder) return false;
  return await shell.openPath(folder);
});
