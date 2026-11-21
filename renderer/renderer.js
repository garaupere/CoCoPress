const search = document.querySelector("#source-search");
const territories = document.querySelector("#territories");
const selectedList = document.querySelector("#selected-list");
const selectedCount = document.querySelector("#selected-count");
const start = document.querySelector("#start");
const output = document.querySelector("#output");
const progressCard = document.querySelector("#progress-card");
const bar = document.querySelector("#bar");
const status = document.querySelector("#status");
const message = document.querySelector("#message");
const counter = document.querySelector("#counter");
const sourceProgress = document.querySelector("#source-progress");
const openFolder = document.querySelector("#open-folder");
const taggingSection = document.querySelector("#tagging-section");
const taggingBar = document.querySelector("#tagging-bar");
const taggingCounter = document.querySelector("#tagging-counter");
const taggingMessage = document.querySelector("#tagging-message");

let catalog = [];
let selectedOutput = "";

function isoDate(offset) {
  const date = new Date();
  date.setDate(date.getDate() - offset);
  return date.toISOString().slice(0, 10);
}
document.querySelector("#from").value = isoDate(30);
document.querySelector("#to").value = isoDate(0);

function updateSelected() {
  const checked = [...document.querySelectorAll('.source-option input:checked')];
  selectedCount.textContent = String(checked.length);
  selectedList.replaceChildren();
  checked.forEach((input) => {
    const item = document.createElement("div");
    item.className = "selected-source";
    item.textContent = input.dataset.name;
    selectedList.append(item);
  });
  start.disabled = checked.length === 0 || !selectedOutput;
}

function renderCatalog() {
  const groups = {};
  catalog.forEach((source) => {
    (groups[source.territory] ||= []).push(source);
  });
  territories.replaceChildren();
  Object.entries(groups).forEach(([territory, sources]) => {
    const details = document.createElement("details");
    details.open = true;
    details.innerHTML = `<summary>${territory} <span class="territory-count">${sources.length}</span></summary>`;
    sources.sort((a, b) => a.name.localeCompare(b.name, "ca"));
    sources.forEach((source) => {
      const label = document.createElement("label");
      label.className = "source-option";
      label.dataset.name = `${source.name} ${territory}`.toLocaleLowerCase("ca");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = source.id;
      input.dataset.name = source.name;
      input.addEventListener("change", updateSelected);
      const name = document.createElement("span");
      name.textContent = source.name;
      label.append(input, name);
      details.append(label);
    });
    territories.append(details);
  });
}

search.addEventListener("input", () => {
  const query = search.value.trim().toLocaleLowerCase("ca");
  document.querySelectorAll(".source-option").forEach((option) => {
    option.classList.toggle("hidden", !option.dataset.name.includes(query));
  });
  document.querySelectorAll("details").forEach((details) => {
    details.hidden = [...details.querySelectorAll(".source-option")].every((option) => option.classList.contains("hidden"));
  });
});

document.querySelector("#choose-output").addEventListener("click", async () => {
  selectedOutput = await window.cocopress.chooseOutputDirectory();
  output.value = selectedOutput || "";
  updateSelected();
});

cocopress.onProgress((data) => {
  progressCard.hidden = false;
  if (data.event === "started") {
    status.textContent = "Processant";
    counter.textContent = `0/${data.total}`;
    bar.style.width = "5%";
  } else if (data.event === "progress") {
    message.textContent = data.message || "";
    if (data.tagging_status && data.tagging_status !== "disabled") {
      taggingSection.hidden = false;
      const taggingCurrent = Number(data.tagging_current || 0);
      const taggingTotal = Number(data.tagging_total || 0);
      taggingCounter.textContent = `${taggingCurrent}/${taggingTotal}`;
      const taggingPercent = data.tagging_status === "done"
        ? 100
        : taggingTotal > 0
          ? Math.round((taggingCurrent / taggingTotal) * 100)
          : 8;
      taggingBar.style.width = `${taggingPercent}%`;
      taggingMessage.textContent = data.tagging_status === "done"
        ? "Etiquetatge i lematització completats"
        : data.tagging_status === "preparing"
          ? "Preparant el model de Stanza..."
          : `Etiquetant notícies: ${taggingCurrent}/${taggingTotal}`;
    }
  } else if (data.event === "source") {
    const percent = data.total ? Math.round((data.index / data.total) * 100) : 0;
    counter.textContent = `${data.index || 0}/${data.total || 0}`;
    bar.style.width = `${percent}%`;
    status.textContent = data.status === "error" ? "Error en un mitjà" : data.name;
    message.textContent = data.message || "";
  } else if (data.event === "done") {
    status.textContent = "Corpus preparat";
    message.textContent = `${data.downloaded} notícies guardades; ${data.skipped} omeses.`;
    counter.textContent = "Complet";
    bar.style.width = "100%";
    openFolder.hidden = false;
    start.disabled = false;
  } else if (data.event === "error") {
    status.textContent = "Error";
    message.textContent = data.message;
    bar.style.width = "100%";
    start.disabled = false;
  }
});

start.addEventListener("click", async () => {
  const sources = [...document.querySelectorAll('.source-option input:checked')].map((input) => input.value);
  const lemmatize = document.querySelector("#lemmatize").checked;
  start.disabled = true;
  openFolder.hidden = true;
  sourceProgress.replaceChildren();
  progressCard.hidden = false;
  if (lemmatize) {
    taggingSection.hidden = false;
    taggingBar.style.width = "8%";
    taggingCounter.textContent = "0/0";
    taggingMessage.textContent = "Preparant el model de Stanza...";
  } else {
    taggingSection.hidden = true;
  }
  status.textContent = "Preparant";
  message.textContent = "Iniciant el procés local...";
  bar.style.width = "5%";
  await window.cocopress.startCorpus({
    sources,
    from: document.querySelector("#from").value,
    to: document.querySelector("#to").value,
    lemmatize,
    outputDir: selectedOutput,
  });
});

openFolder.addEventListener("click", () => window.cocopress.openFolder(selectedOutput));

window.cocopress.getCatalog().then((sources) => {
  catalog = sources;
  renderCatalog();
}).catch((error) => {
  document.querySelector("#catalog-error").hidden = false;
  document.querySelector("#catalog-error").textContent = error.message;
});
