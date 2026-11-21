const form = document.querySelector("#download-form");
const submitButton = document.querySelector("#submit-button");
const progressCard = document.querySelector("#progress-card");
const status = document.querySelector("#status");
const counter = document.querySelector("#counter");
const bar = document.querySelector("#bar");
const message = document.querySelector("#message");
const downloadLink = document.querySelector("#download-link");
const sourceProgress = document.querySelector("#source-progress");
const selectedSources = document.querySelector("#selected-sources");

const today = new Date();
const monthAgo = new Date(today);
monthAgo.setDate(today.getDate() - 30);

document.querySelector("#from").value = monthAgo.toISOString().slice(0, 10);
document.querySelector("#to").value = today.toISOString().slice(0, 10);

const sourceSearch = document.querySelector("#source-search");
sourceSearch.addEventListener("input", () => {
  const query = sourceSearch.value.trim().toLocaleLowerCase("ca");
  document.querySelectorAll(".source-option").forEach(option => {
    option.classList.toggle("hidden", !option.dataset.name.includes(query));
  });
  document.querySelectorAll(".territory-group").forEach(group => {
    const visibleOptions = group.querySelectorAll(".source-option:not(.hidden)");
    group.classList.toggle("hidden", visibleOptions.length === 0);
  });
});

function renderSelectedSources() {
  const selected = [...form.querySelectorAll('input[name="source"]:checked')];
  selectedSources.replaceChildren();
  selected.forEach(input => {
    const label = input.closest(".source-option");
    const item = document.createElement("div");
    item.className = "selected-source";
    item.innerHTML = `<span>${label.querySelector("span").textContent}</span><span>Afegit</span>`;
    selectedSources.append(item);
  });
}

form.querySelectorAll('input[name="source"]').forEach(input => {
  input.addEventListener("change", renderSelectedSources);
});

function poll(jobId) {
  fetch(`/api/jobs/${jobId}`)
    .then(response => response.json())
    .then(job => {
      status.textContent = job.status === "done" ? "Descàrrega preparada" :
        job.status === "error" ? "Ou! S'ha produït un error" : "Processant";
      message.textContent = job.message;

      if (job.total > 0) {
        const percent = Math.round((job.current / job.total) * 100);
        bar.style.width = `${percent}%`;
        counter.textContent = `${job.current}/${job.total}`;
      } else {
        bar.style.width = "8%";
        counter.textContent = "";
      }

      sourceProgress.replaceChildren();
      Object.entries(job.source_progress || {}).forEach(([key, progress]) => {
        const checkbox = form.querySelector(`input[name="source"][value="${CSS.escape(key)}"]`);
        const name = checkbox?.closest(".source-option")?.querySelector("span")?.textContent || key;
        const item = document.createElement("div");
        item.className = "source-progress-item";
        const percent = progress.total ? Math.round((progress.current / progress.total) * 100) : 0;
        const statusLabel = progress.status === "queued" ? "a la llista" : progress.status;
        item.innerHTML = `<strong>${name}</strong><div class="track"><div style="width:${percent}%"></div></div><span>${progress.message || statusLabel}</span>`;
        sourceProgress.append(item);
      });

      if (job.status === "done" && job.downloaded > 0) {
        downloadLink.href = `/api/jobs/${jobId}/download`;
        downloadLink.hidden = false;
        submitButton.disabled = false;
      } else if (job.status === "done" || job.status === "error") {
        downloadLink.hidden = true;
        submitButton.disabled = false;
      } else {
        setTimeout(() => poll(jobId), 700);
      }
    })
    .catch(error => {
      status.textContent = "Ou! S'ha produït un error";
      message.textContent = error.message;
      submitButton.disabled = false;
    });
}

form.addEventListener("submit", event => {
  event.preventDefault();
  const selected = form.querySelectorAll('input[name="source"]:checked');
  if (selected.length === 0) {
    status.textContent = "Ei! Selecciona almanco un mitjà de la llista";
    progressCard.hidden = false;
    message.textContent = "";
    return;
  }
  submitButton.disabled = true;
  downloadLink.hidden = true;
  progressCard.hidden = false;
  status.textContent = "Preparant";
  message.textContent = "Iniciant la tasca...";
  bar.style.width = "8%";
  counter.textContent = "";

  fetch("/api/download", {
    method: "POST",
    body: new FormData(form)
  })
    .then(async response => {
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Ui! No s'ha pogut iniciar la descàrrega");
      return data.job_id;
    })
    .then(poll)
    .catch(error => {
      status.textContent = "Ou! S'ha produït un error";
      message.textContent = error.message;
      submitButton.disabled = false;
    });
});
