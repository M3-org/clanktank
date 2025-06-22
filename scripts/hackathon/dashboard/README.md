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

## API Endpoints

- `GET /api/submissions` - List all submissions with filtering
- `GET /api/submission/{id}` - Get detailed submission data
- `GET /api/leaderboard` - Get public leaderboard data
- `GET /api/stats` - Get dashboard statistics

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