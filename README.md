# Skin Lesion Malignancy Classifier

Full-stack project with a FastAPI backend (Render-ready) and a static frontend (Vercel-ready).

## Project Structure

```text
project/
├── backend/
│   ├── app.py
│   ├── model.py
│   ├── gradcam.py
│   ├── requirements.txt
│   └── best_model.pth
├── frontend/
│   ├── package.json
│   ├── index.html
│   ├── main.js
│   └── style.css
└── README.md
```

## Backend (FastAPI)

From the `backend` folder:

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Optional environment variables:

- `MODEL_PATH` (default: `best_model.pth`)
- `CORS_ORIGINS` (comma-separated list, e.g. `https://your-frontend.vercel.app,http://localhost:5173`)
- `CORS_ORIGIN_REGEX` (default supports `https://*.vercel.app`)
- `MAX_IMAGE_BYTES` (default `10485760`)
- `LOG_LEVEL` (default `INFO`)

API endpoints:

- `GET /health`
- `GET /ping`
- `POST /predict` (multipart/form-data, field name: `image`)

## Frontend

The frontend is vanilla JS and calls the backend with `multipart/form-data`.

Set backend URL in `frontend/index.html`:

```html
<meta name="api-base-url" content="https://your-render-service.onrender.com" />
```

Run locally from the `frontend` folder:

```bash
npm install
npm run dev
```

## Deployment Notes

- Deploy `backend` on Render.
- Deploy `frontend` on Vercel.
- Ensure backend CORS allows your Vercel domain.
- The frontend sends a silent wake-up request to `GET /ping` on load.
