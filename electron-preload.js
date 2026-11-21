const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("cocopress", {
  getCatalog: () => ipcRenderer.invoke("catalog:get"),
  chooseOutputDirectory: () => ipcRenderer.invoke("output:choose"),
  startCorpus: (payload) => ipcRenderer.invoke("corpus:start", payload),
  openFolder: (folder) => ipcRenderer.invoke("folder:open", folder),
  onProgress: (callback) => {
    const listener = (_event, message) => callback(message);
    ipcRenderer.on("corpus:progress", listener);
    return () => ipcRenderer.removeListener("corpus:progress", listener);
  },
});
