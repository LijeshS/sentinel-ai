# Sentinel AI — Real-Time Vendor Risk Intelligence

Enterprise security dashboard for continuous third-party vendor risk monitoring.

## Architecture

```
sentinel-ai/
├── backend/         FastAPI + SQLAlchemy + APScheduler
│   ├── main.py      API routes and app lifecycle
│   ├── scheduler.py Monitoring engine (every 5 min)
│   ├── brightdata.py SERP + Web Access + MCP clients
│   ├── ai_service.py OpenAI GPT-4o-mini risk analysis
│   ├── models.py    SQLAlchemy ORM models
│   ├── schemas.py   Pydantic schemas
│   └── config.py   Environment configuration
└── frontend/        Next.js 14 App Router
    ├── app/page.tsx          SOC dashboard
    ├── app/vendors/[id]/     Vendor detail + alert timeline
    └── components/           VendorTable, AlertCard, LoadingPulse
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Bright Data account with SERP API and Web Access API
- OpenAI API key

## Environment Variables

Create `backend/.env`:

```env
BRIGHTDATA_API_KEY=your_brightdata_api_key
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=sqlite:///sentinel.db
```

Optionally create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Installation

### Backend

```bash
cd sentinel-ai/backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Frontend

```bash
cd sentinel-ai/frontend
npm install
```

## Running

### Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

The backend will:
1. Initialize the SQLite database
2. Seed 7 default vendors (AWS, Stripe, Okta, Cloudflare, GitHub, MongoDB, Twilio)
3. Start the APScheduler monitoring engine (every 5 minutes)
4. Serve the FastAPI REST API on port 8000

### Frontend

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check + DB status |
| GET | /vendors | List all vendors with status |
| GET | /vendors/{id} | Vendor detail + all alerts |
| GET | /alerts | All alerts (filterable) |
| GET | /stats | Dashboard statistics |
| POST | /scan | Trigger immediate scan |

## Monitoring Flow

```
Every 5 minutes:
  For each vendor (AWS, Stripe, Okta, ...):
    1. SERP API → search 6 queries (outage, breach, security incident, etc.)
    2. Extract top URLs from Google search results
    3. Web Access API → scrape article content
    4. OpenAI GPT-4o-mini → analyze risk (returns JSON or null)
    5. Store RiskAlert to SQLite (dedup by URL)
    6. Update vendor status: LOW→Healthy, MEDIUM→Warning, HIGH→High Alert, CRITICAL→Critical
```

## Bright Data Integration

### SERP API

Searches Google via Bright Data's SERP zone (`serp_api1`). Six query templates per vendor:
- `{vendor} outage`
- `{vendor} breach`
- `{vendor} security incident`
- `{vendor} phishing`
- `{vendor} lawsuit`
- `{vendor} compliance issue`

### Web Access API

Scrapes full article content using dataset ID `gd_lvz8ah06191smkebj4`. Includes retry logic (3 attempts) with exponential backoff and a direct HTTP fallback.

### MCP

Bright Data MCP endpoint at `mcp.brightdata.com/mcp` for advanced scraping scenarios.

## OpenAI Integration

Uses GPT-4o-mini for cost-effective, fast risk analysis. The system prompt instructs the model to:
- Return strict JSON or `null` (irrelevant articles)
- Score risk as LOW / MEDIUM / HIGH / CRITICAL
- Provide incident_type, summary, business_impact, recommended_action

If `OPENAI_API_KEY` is not set, a keyword-based mock analyzer runs instead (useful for demo/testing).

## Demo Instructions

1. Start backend: `uvicorn main:app --reload --port 8000`
2. Start frontend: `npm run dev`
3. Open `http://localhost:3000`
4. Click **Scan Now** to trigger an immediate monitoring cycle
5. Click any vendor row to see detailed alert timeline
6. Dashboard auto-refreshes every 30 seconds

## Risk Level Color Coding

| Level | Status | Color |
|-------|--------|-------|
| LOW | Healthy | Green |
| MEDIUM | Warning | Amber |
| HIGH | High Alert | Orange |
| CRITICAL | Critical | Red |
