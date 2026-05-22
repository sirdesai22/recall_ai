const { app, BrowserWindow, Tray, Menu, nativeImage } = require("electron");
const { spawn } = require("child_process");
const path = require("path");

let mainWindow;
let tray;
let pythonProcess;

function startPython() {
  const pythonPath = path.join(__dirname, "..", "core", ".venv", "bin", "python");
  const scriptPath = path.join(__dirname, "..", "core", "api.py");

  pythonProcess = spawn(pythonPath, [scriptPath], {
    cwd: path.join(__dirname, "..", "core"),
  });

  pythonProcess.stdout.on("data", (data) => console.log(`[python] ${data}`));
  pythonProcess.stderr.on("data", (data) => console.error(`[python] ${data}`));
  pythonProcess.on("close", (code) => console.log(`[python] exited with code ${code}`));
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
    if (!app.isQuitting) {
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
        app.isQuitting = true;
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
  killPython();
});
