# Hackathon Dashboard

A web-based admin dashboard and public leaderboard for the Clank Tank Hackathon judging system.

## Features

### Admin Dashboard
- Real-time submission tracking with status indicators
- Filterable and sortable submission table
- Detailed project views with scores and research data
- Auto-refresh for live updates
- Statistics overview

### Public Leaderboard
- Final rankings of published projects
- Clean, shareable interface
- Social sharing integration
- YouTube video links

## Architecture

- **Backend**: FastAPI (Python) serving data from `hackathon.db`
- **Frontend**: React with TypeScript, Vite, Tailwind CSS
- **Database**: SQLite (`data/hackathon.db`)

## Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- A populated `hackathon.db` database

### Backend Setup

1. Install Python dependencies:
```bash
cd scripts/hackathon/dashboard
pip install -r requirements.txt
```

2. Start the API server:
```bash
python app.py
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Frontend Setup

1. Install Node dependencies:
```bash
cd scripts/hackathon/dashboard/frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Dynamic Submission Form Schema

The submission form fields are defined by a versioned schema:
- On form load, the frontend fetches the latest schema from the backend endpoint `/api/v2/submission-schema`.
- If the backend is unavailable, the frontend falls back to a static manifest in `src/types/submission_manifest.ts`.
- The last successful schema is cached in `localStorage` for resilience.
- The form renders fields, validation, and defaults based on the loaded schema.

#### Updating the Schema
- **Backend is the source of truth:** Update the schema in `scripts/hackathon/schema.py` (`SUBMISSION_SCHEMA_V2`).
- The frontend manifest (`src/types/submission_manifest.ts`) should be kept in sync for fallback.
- After updating the backend schema, restart the backend server to serve the new schema.
- The frontend will automatically use the new schema on next load.

#### Robustness
- If the backend schema fetch fails, users will see a warning and the form will use the static fallback.
- This ensures the submission process is robust to backend downtime or schema changes.

## API Versioning Policy

- The root `/api/*` endpoints always point to the latest version of the API (currently v2).
- Older versions remain available at `/api/v1/*`, `/api/v2/*`, etc., for legacy/compatibility.
- When a new version is released, the root endpoints are updated to point to the new version, and previous versions remain accessible at their versioned paths.

## API Endpoints (Latest)

- `GET /api/submissions` - List all submissions with filtering (latest schema)
- `GET /api/submissions/{id}` - Get detailed submission data (latest schema)
- `POST /api/submissions` - Create a new submission (latest schema)
- `GET /api/leaderboard` - Get public leaderboard data (latest)
- `GET /api/stats` - Get dashboard statistics (latest)
- `GET /api/submission-schema` - Get the current submission schema (latest)

## API Endpoints (Legacy)

- `GET /api/v1/submissions`, `GET /api/v2/submissions`, etc. - Version-specific endpoints for legacy clients
- `POST /api/v1/submissions`, `POST /api/v2/submissions`, etc. - Version-specific submission creation
- `GET /api/v1/leaderboard`, `GET /api/v2/leaderboard`, etc.
- `GET /api/v1/stats`, `GET /api/v2/stats`, etc.
- `GET /api/v2/submission-schema` (for v2 schema)

## Static Deployment

For static site deployment (e.g., GitHub Pages):

1. Generate static data files:
```bash
python app.py --generate-static-data
```

2. Build the frontend with static mode:
```bash
cd frontend
VITE_USE_STATIC=true npm run build
```

- The static manifest (`src/types/submission_manifest.ts`) will be used for the submission form schema if the backend is unavailable.
- To update the static schema, edit `src/types/submission_manifest.ts` and rebuild the frontend.

3. Deploy the `dist` folder to your static host

## Development

### Environment Variables

Create a `.env` file in the dashboard directory:
```env
HACKATHON_DB_PATH=../../../data/hackathon.db
STATIC_DATA_DIR=./frontend/public/data
```

### Frontend Configuration

The frontend automatically proxies API requests to the backend in development mode.
For production, update the API base URL in `src/lib/api.ts`.

## Usage

### Viewing Submissions

1. Navigate to the dashboard homepage
2. Use filters to narrow down submissions by status or category
3. Click on any submission to view detailed information

### Checking Scores

In the detailed view, you can see:
- Individual judge scores with breakdowns
- Judge comments and reasoning
- Average weighted scores
- Research data summary

### Public Leaderboard

Navigate to `/leaderboard` to see the final rankings of all published projects.
Use the share button to post on social media.

## Troubleshooting

### Database Connection Issues
- Ensure `hackathon.db` exists in the correct path
- Check file permissions
- Verify the path in your `.env` file

### CORS Errors
- Make sure both frontend and backend are running
- Check that the proxy configuration in `vite.config.ts` is correct

### Missing Data
- Verify that submissions have been processed through all pipeline stages
- Check submission status in the database

## License

Part of the Clank Tank Hackathon system.