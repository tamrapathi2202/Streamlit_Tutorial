# Sales Performance Dashboard (Streamlit)

This project ships with a fully working Streamlit data app that lets you explore a demo
sales dataset, slice it with sidebar filters, and review visual insights.

## Prerequisites
- Python 3.9 or newer
- pip

## Create a virtual environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

## Install dependencies
```bash
pip install -r requirements.txt
```

## Run the development server
```bash
streamlit run app.py
```

Streamlit will open a browser tab at http://localhost:8501 with the dashboard.

## What you get
- A sidebar with multi-select filters for region, category, and segment plus a date range.
- KPI tiles that summarise total sales, profit, average margin, and order value.
- Plotly charts for daily sales, sales by category, and profit contribution by segment.
- A searchable data table and a download button for the filtered results.

## Data source
Sample sales transactions live in `data/sales_sample.csv`. Replace it with your own data or
hook up a database/REST API as needed.

## Configuration
- Theme settings live in `.streamlit/config.toml`.
- Add secrets to `.streamlit/secrets.toml` (create the file when needed and never commit secrets).

## Next steps
- Swap in real data and extend the visualisations.
- Add authentication, scheduling, or notifications if you deploy the app.
- Consider writing regression tests for business logic or data transforms.
 
Additional demo app
-------------------

An alternate / extended demo is available in `streamlit_ass.py`. It mirrors a more feature-rich dashboard (login form, advanced visualizations, data editor and download controls) and is wired to the local `data/sales_sample.csv` so you can run it without a database backend:

```bash
streamlit run streamlit_ass.py
```

Optional: run with MongoDB
-------------------------

`streamlit_ass.py` supports an optional MongoDB backend. When a `MONGO_URI` environment variable is provided the app will try to load data from the configured database/collection. If the database/collection isn't available (or you don't set `MONGO_URI`), the app falls back to the local CSV (`data/sales_sample.csv`).

Environment variables the app reads:
- `MONGO_URI` — connection string, e.g. `mongodb://localhost:27017/` or an Atlas URI
- `MONGO_DB` — database name (defaults to `sales_db`)
- `MONGO_COLLECTION` — collection name (defaults to `sales`)
- `DATA_SOURCE` — `auto` (default), `csv`, or `mongo` — forces a source when needed

PowerShell example (temporary for the session):

```powershell
$env:MONGO_URI = "mongodb://localhost:27017/"
$env:MONGO_DB = "sales_db"
$env:MONGO_COLLECTION = "sales"
streamlit run streamlit_ass.py
```

Or put these values in a `.env` file in the repo root, then run the app (python-dotenv is already included in `requirements.txt`):

```
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=sales_db
MONGO_COLLECTION=sales
```

If you don't want MongoDB at all, the app works out-of-the-box using the local CSV.

Continuous Integration
----------------------

This repository includes a GitHub Actions workflow that runs tests on push and pull requests to `main`. Tests are implemented with `pytest` and the workflow installs `requirements.txt` before running them.

Running tests locally:

```powershell
pip install -r requirements.txt
pytest -q
```

Run MongoDB locally and seed data (optional)
--------------------------------------------

You can run MongoDB locally with Docker Compose and seed the sales dataset into a collection used by `streamlit_ass.py`.

Start MongoDB with Docker Compose:

```powershell
docker compose -f docker-compose.mongo.yml up -d
```

Then seed the database (PowerShell example):

```powershell
$env:MONGO_URI = "mongodb://localhost:27017/"
$env:MONGO_DB = "sales_db"
$env:MONGO_COLLECTION = "sales"
python .\scripts\seed_mongo.py
```

The script clears existing documents and inserts the CSV rows into the collection. After seeding you can run `streamlit_ass.py` in Mongo mode.

Notes about persistence
----------------------

`streamlit_ass.py` supports saving edits back to MongoDB. To persist edits made in the UI you must:

1. Run the app connected to MongoDB (set `MONGO_URI`/`MONGO_DB`/`MONGO_COLLECTION` as shown above).
2. Make edits in the data editor (first 20 rows are editable in the demo).
3. Check "Enable write-back to MongoDB for these edits" and press "Save edits to MongoDB".

The app will only persist rows that include valid `_id` fields (ObjectId strings) and will perform an `$set` update with changed fields only — this keeps writes safe and explicit.
