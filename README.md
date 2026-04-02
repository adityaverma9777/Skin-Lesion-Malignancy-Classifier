# Skin Lesion Malignancy Classifier

Hey! This is my skin lesion classification project.

I built this as a full-stack app with a Python backend and a simple frontend so anyone can clone it, run it locally, and test predictions on their own machine.

## What I Built

- A FastAPI backend that loads a trained model once at startup.
- A frontend where you can upload an image and get:
  - predicted label (benign or malignant)
  - probability score
  - Grad-CAM style heatmap overlay

## How I Trained the Model

I trained the model using the ISIC 2019 Skin Lesion dataset.

The original dataset has multiple skin condition classes. For this project, I converted it into a binary task:

- melanoma (MEL) -> malignant
- all other classes -> benign

Training setup:

- framework: PyTorch + timm
- architecture: EfficientNet-B4 (ImageNet pretrained, then fine-tuned)
- training environment: Kaggle GPU (NVIDIA T4)
- techniques used: data augmentation, weighted sampling for class imbalance, and Focal Loss
- optimizer: AdamW
- main metric: ROC-AUC
- validation performance: around 0.94 AUC

Final model weights are saved in this repo as best_model.pth and used for inference.

## Project Structure

```text
project/
├── backend/
│   ├── app.py
│   ├── model.py
│   ├── gradcam.py
│   ├── requirements.txt
│   ├── smoke_test.py
│   └── best_model.pth
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   ├── main.js
│   └── style.css
├── run-local.ps1
└── README.md
```

## How to Start the Project

### Option 1 (Windows quick start)

Open PowerShell in project root and run:

```powershell
.\run-local.ps1
```

This starts backend and frontend in separate terminals.

If PowerShell blocks script execution, run this first in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run-local.ps1
```

### Option 2 (manual start)

Backend terminal:

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

Frontend terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open the frontend URL shown in terminal (usually http://127.0.0.1:5173).

## How to Check If It Is Working

1. Check backend health in browser:
	- http://127.0.0.1:8000/health
	- http://127.0.0.1:8000/ping

2. Open frontend and upload an image.

3. Click Predict and verify you get:
	- label
	- probability
	- Grad-CAM image

4. Optional API smoke test:

```bash
cd backend
python smoke_test.py path/to/image.jpg --base-url http://127.0.0.1:8000
```

## Notes

- Frontend is already configured to call local backend at http://127.0.0.1:8000.
- If port 5173 is occupied, frontend may run on another local port.
