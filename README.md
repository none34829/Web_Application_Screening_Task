# Chemical Equipment Parameter Visualizer

Hybrid analytics stack that pairs a Django REST backend with a React web dashboard and a PyQt5 desktop client. Both front-ends speak to the same API to upload chemical equipment CSV files, inspect calculated summaries, visualize equipment type distributions, download PDF reports, and revisit the most recent five uploads.

## Project Layout

```
.
├── backend/        # Django + DRF backend
├── web/            # React + Chart.js SPA (Vite)
├── desktop/        # PyQt5 + Matplotlib desktop app
├── sample_equipment_data.csv
└── README.md
```

## Features

- **CSV ingestion + analytics** via pandas with validation for flowrate, pressure, and temperature columns.
- **Summary API** reporting total equipment, averages, and equipment type distribution.
- **History retention** that automatically trims uploads to the five most recent datasets.
- **PDF reporting** powered by ReportLab for quick stakeholder exports.
- **Basic authentication** (DRF BasicAuth + session) – ship a demo `demo/demo123` account for local testing.
- **Chart.js web dashboard** with upload helper, Chart.js bar chart, data table, and PDF downloads.
- **PyQt5 desktop application** offering the same workflow with Matplotlib visualization and CSV uploads.

## Prerequisites

- Python 3.11+
- Node.js 18+ (tested with 20.19)
- npm

> **Tip:** Use isolated virtual environments for both the backend and the desktop client if you prefer to keep dependencies separate.

## Backend Setup (Django + DRF)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py create_demo_user  # creates demo/demo123 for quick logins
python manage.py runserver
```

Environment knobs:

- `DJANGO_SECRET_KEY` – override the default dev key.
- `DJANGO_ALLOWED_HOSTS` – comma-separated list if you need to expose beyond localhost.

### API Endpoints

All endpoints require Basic Auth (`demo/demo123` after running the management command above).

| Method | Endpoint                       | Description                               |
|--------|--------------------------------|-------------------------------------------|
| POST   | `/api/upload/`                 | Upload CSV, triggers analytics + history. |
| GET    | `/api/datasets/latest/`        | Latest dataset data + summary.            |
| GET    | `/api/datasets/history/`       | Summaries for the last 5 uploads.         |
| GET    | `/api/datasets/<uuid>/pdf/`    | Download PDF report for a dataset.        |
| GET    | `/api/health/`                 | Unauthenticated health check.             |

Sample upload call:

```bash
curl -u demo:demo123 -F "file=@sample_equipment_data.csv" http://127.0.0.1:8000/api/upload/
```

### Tests

```bash
cd backend
.venv\Scripts\activate
python manage.py test
```

## Web Dashboard (React + Vite + Chart.js)

```bash
cd web
npm install
# Optional: configure a custom backend URL
echo VITE_API_BASE_URL=http://127.0.0.1:8000/api > .env
npm run dev        # starts Vite dev server on http://127.0.0.1:5173
```

Highlights:

- In-browser CSV upload with progress + bundled `sample_equipment_data.csv` shortcut (`Load bundled sample` button).
- Summary cards, live Chart.js bar visualization, sortable data table, and PDF download buttons per history entry.
- Basic Auth handled client-side; credentials default to the demo user for convenience.

Build for production with `npm run build` (already verified).

## Desktop Client (PyQt5 + Matplotlib)

```bash
cd desktop
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

What you get:

- Connect panel for API URL + credentials, mirroring the web client defaults.
- CSV upload dialog, latest dataset table (capped at 500 rows), summary tiles, Matplotlib bar chart, and history list.
- PDF download button uses the selected history entry (or latest dataset when none selected).

## Sample Data

- `sample_equipment_data.csv` at the repo root is the reference dataset.
- The same file is bundled inside `web/public` so the web dashboard can preload it without browsing the filesystem.

## Suggested Workflow

1. **Start backend** (`python manage.py runserver`) and create the demo auth user.
2. **Run tests** (`python manage.py test`) if you change backend logic.
3. **Launch frontends**:
   - Web: `npm run dev` → http://127.0.0.1:5173
   - Desktop: `python main.py`
4. **Upload CSV** (use the bundled sample for instant visuals) and explore summaries, histories, and PDF downloads.
