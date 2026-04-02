const baseUrlMeta = document.querySelector('meta[name="api-base-url"]');
const preferredBaseUrl = (baseUrlMeta?.content || "http://127.0.0.1:8000").replace(/\/$/, "");
const CANDIDATE_BASE_URLS = [
  preferredBaseUrl,
  "http://127.0.0.1:8000",
  "http://localhost:8000",
  "http://127.0.0.1:8001",
  "http://localhost:8001",
].filter((value, index, self) => value && self.indexOf(value) === index);

let activeBaseUrl = preferredBaseUrl;

const form = document.getElementById("predict-form");
const imageInput = document.getElementById("image-input");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const labelValueEl = document.getElementById("label-value");
const probabilityValueEl = document.getElementById("probability-value");
const gradcamImageEl = document.getElementById("gradcam-image");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

async function probeBackend(baseUrl, timeoutMs = 2500) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${baseUrl}/ping`, {
      method: "GET",
      signal: controller.signal,
    });
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function resolveBackendBaseUrl() {
  for (const candidate of CANDIDATE_BASE_URLS) {
    const ok = await probeBackend(candidate);
    if (ok) {
      activeBaseUrl = candidate;
      return candidate;
    }
  }
  activeBaseUrl = preferredBaseUrl;
  return null;
}

async function wakeBackendSilently() {
  await resolveBackendBaseUrl();
}

async function handlePredict(event) {
  event.preventDefault();

  if (!imageInput.files || imageInput.files.length === 0) {
    setStatus("Please select an image first.", true);
    return;
  }

  const file = imageInput.files[0];
  const formData = new FormData();
  formData.append("image", file);

  submitBtn.disabled = true;
  setStatus("Running inference...");
  resultEl.classList.add("hidden");

  try {
    await resolveBackendBaseUrl();

    const response = await fetch(`${activeBaseUrl}/predict`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new Error(errorPayload.detail || "Prediction request failed.");
    }

    const data = await response.json();
    labelValueEl.textContent = data.label;
    probabilityValueEl.textContent = `${(Number(data.probability) * 100).toFixed(2)}%`;
    gradcamImageEl.src = data.gradcam;

    resultEl.classList.remove("hidden");
    setStatus("Prediction complete.");
  } catch (error) {
    const message = error?.message || "Something went wrong.";
    if (message === "Failed to fetch") {
      if (window.location.protocol === "file:") {
        setStatus(
          "Cannot reach backend from file:// origin. Open the frontend from the dev server URL (for example http://127.0.0.1:5173).",
          true,
        );
      } else {
        setStatus(
          `Cannot reach backend. Make sure backend is running and reachable at ${activeBaseUrl}.`,
          true,
        );
      }
    } else {
      setStatus(message, true);
    }
  } finally {
    submitBtn.disabled = false;
  }
}

wakeBackendSilently();
form.addEventListener("submit", handlePredict);
