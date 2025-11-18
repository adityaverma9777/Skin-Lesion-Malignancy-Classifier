const baseUrlMeta = document.querySelector('meta[name="api-base-url"]');
const BASE_URL = (baseUrlMeta?.content || "https://skin-lesion-malignancy-classifier.onrender.com").replace(/\/$/, "");

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

function wakeBackendSilently() {
  fetch(`${BASE_URL}/ping`, { method: "GET" }).catch(() => {
    // Silence wake-up failures to avoid impacting the UI.
  });
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
    const response = await fetch(`${BASE_URL}/predict`, {
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
    setStatus(error.message || "Something went wrong.", true);
  } finally {
    submitBtn.disabled = false;
  }
}

wakeBackendSilently();
form.addEventListener("submit", handlePredict);
