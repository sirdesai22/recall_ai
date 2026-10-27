const { app, BrowserWindow, Tray, Menu, nativeImage } = require("electron");
const { spawn } = require("child_process");
const path = require("path");

let mainWindow;
let tray;
let pythonProcess;
let quitting = false;

const MAX_PYTHON_RETRIES = 5;

function startPython(retries = 0) {
  const pythonPath = path.join(__dirname, "..", "core", ".venv", "bin", "python");
  const scriptPath = path.join(__dirname, "..", "core", "api.py");

  pythonProcess = spawn(pythonPath, [scriptPath], {
    cwd: path.join(__dirname, "..", "core"),
  });

  pythonProcess.stdout.on("data", (data) => console.log(`[python] ${data}`));
  pythonProcess.stderr.on("data", (data) => console.error(`[python] ${data}`));

  pythonProcess.on("error", (err) => {
    pythonProcess = null;
    retryPython(retries, `failed to start python: ${err.message}`);
  });

  pythonProcess.on("close", (code) => {
    console.log(`[python] exited with code ${code}`);
    pythonProcess = null;
    if (!quitting && code !== 0) {
      retryPython(retries, `python exited unexpectedly (code ${code})`);
    }
  });
}

function retryPython(retries, reason) {
  if (retries >= MAX_PYTHON_RETRIES) {
    console.error(`[python] giving up after ${retries} retries — backend is down`);
    return;
  }
  const delay = 2000 * (retries + 1);
  console.error(`[python] ${reason} — restarting in ${delay}ms (attempt ${retries + 1}/${MAX_PYTHON_RETRIES})`);
  setTimeout(() => {
    if (!quitting && !pythonProcess) startPython(retries + 1);
  }, delay);
}

function killPython() {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadURL("http://localhost:5173");

  mainWindow.on("close", (e) => {
    if (!quitting) {
      e.preventDefault();
      mainWindow.hide();
    }
  });
}

function createTray() {
  const icon = nativeImage.createEmpty();
  tray = new Tray(icon);
  tray.setToolTip("Recall");

  const contextMenu = Menu.buildFromTemplate([
    {
      label: "Open",
      click: () => {
        if (mainWindow) mainWindow.show();
      },
    },
    { type: "separator" },
    {
      label: "Quit",
      click: () => {
        quitting = true;
        killPython();
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
  tray.on("click", () => {
    if (mainWindow) mainWindow.show();
  });
}

app.on("ready", () => {
  startPython();
  setTimeout(() => {
    createTray();
    createWindow();
  }, 2000);
});

app.on("window-all-closed", (e) => {
  e.preventDefault();
});

app.on("before-quit", () => {
  quitting = true;
  killPython();
});
