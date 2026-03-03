# Air Tracker: Flight Analytics

End-to-end aviation analytics project using AeroDataBox API, PostgreSQL (Supabase-compatible), and Streamlit.

## Overview

This project fetches airport, flight, aircraft, and airport-delay data from AeroDataBox, stores it in a relational SQL schema, and exposes interactive analytics through Streamlit.

Primary goals:
- Collect aviation data reliably from API endpoints.
- Normalize and store data in SQL tables for querying.
- Provide dashboard-style insights for airport and flight operations.

## Skills Demonstrated

- Python scripting
- API integration and JSON transformation
- SQL database design and query analysis
- Streamlit dashboard development

## Core Architecture

1. `api_scripts/`: API fetch layer (airports, flights, aircraft, delays).
2. `database/`: connection utilities, schema, insert/upsert logic, analysis queries.
3. `run_pipeline.py`: orchestrates extraction and loading phases.
4. `streamlit_app/`: interactive UI pages backed by real SQL queries.

Data flow:
- AeroDataBox API -> Python fetch scripts -> transform/normalize -> PostgreSQL tables -> Streamlit pages.

## Implemented App Pages

1. Homepage Dashboard
- Total airports
- Total flights fetched
- Average delay across airports

2. Search and Filter Flights
- Search by flight number or airline
- Filter by status, origin, and date range
- Tabular results sorted by scheduled departure

3. Airport Details Viewer
- Airport identity and location
- Timezone and coordinates
- Linked departures/arrivals

4. Delay Analysis
- Delay percentage by airport (latest delay snapshot per airport)
- Average delay metric
- Delay detail table

5. Route Leaderboards
- Busiest routes (most flights)
- Most delayed airports

## API Endpoints Used

- Airport details: `/airports/iata/{iataCode}`
- Flights by airport: `/flights/airports/iata/{iataCode}` (departures + arrivals)
- Aircraft details: aircraft endpoints via registration/model lookups
- Airport delays/statistics: delay/statistical endpoint used by `api_scripts/fetch_delays.py`

Notes:
- Data is real API data.
- Pipeline includes normalization for timestamp rollover anomalies around midnight.
- Delay data is stored as dated snapshots, not continuous streaming.

## Database Schema

### `airport`
- `airport_id` (PK)
- `icao_code` (UNIQUE)
- `iata_code` (UNIQUE)
- `name`, `city`, `country`, `continent`
- `latitude`, `longitude`, `timezone`

### `aircraft`
- `aircraft_id` (PK)
- `registration` (UNIQUE)
- `model`, `manufacturer`, `icao_type_code`, `owner`

### `flights`
- `flight_id` (PK)
- `flight_number`
- `aircraft_registration`
- `origin_iata`, `destination_iata`
- `scheduled_departure`, `actual_departure`
- `scheduled_arrival`, `actual_arrival`
- `status`, `airline_code`

### `airport_delays`
- `delay_id` (PK)
- `airport_iata`
- `delay_date`
- `total_flights`, `delayed_flights`
- `avg_delay_min`, `median_delay_min`, `canceled_flights`

## Required SQL Analytics Covered

Implemented in `database/queries.sql` and executable with `scripts/execute_queries.py`:

1. Total flights per aircraft model
2. Aircraft assigned to more than 5 flights
3. Airports with more than 5 outbound flights
4. Top 3 destination airports by arrivals
5. Domestic vs International classification (CASE WHEN)
6. 5 most recent arrivals at DEL
7. Airports with no arriving flights
8. Flights by airline and status (CASE WHEN)
9. Cancelled flights with airports and aircraft
10. City pairs with more than 2 aircraft models
11. Delayed-arrival percentage by destination airport

## Setup

### Prerequisites
- Python 3.9+
- PostgreSQL 12+ (Supabase supported)
- AeroDataBox RapidAPI key

### Environment
Create your environment file from the template:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Then edit `.env` in project root:

```env
RAPIDAPI_KEY=your_rapidapi_key_here
DB_HOST=your_db_host
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_PORT=5432
DELAY_AIRPORTS=DEL,BOM,BLR
DELAY_DAYS=1
```

Note: `.env` is intentionally git-ignored. Commit `.env.example`, never commit real credentials.

### Install

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Initialize Schema

```bash
psql -h <host> -U <user> -d <db_name> -f database/schema.sql
```

## Run

### Pipeline

```bash
python run_pipeline.py
```

### Streamlit App

```bash
streamlit run streamlit_app/app.py
```

App URL: `http://localhost:8501`

## Operational Notes

- Refresh model: rerun pipeline to fetch latest snapshots.
- API quota affects freshness and airport coverage.
- Delay metrics are based on stored delay snapshots per airport/date.
- For live demos, run pipeline shortly before presentation.

## Troubleshooting

1. API rate limit (`429`)
- Reduce airport/day scope.
- Retry later or upgrade API plan.

2. Stale UI data
- Rerun `python run_pipeline.py`.
- Clear Streamlit cache and refresh page.

3. DB connection errors
- Recheck `.env` credentials.
- Verify DB host/firewall/network access.

4. Port in use

```bash
streamlit run streamlit_app/app.py --server.port 8502
```

## Project Structure

```text
Air-Tracker-Flight-Analytics/
  api_scripts/         # API fetch and normalization
  database/            # schema, queries, inserts, DB utilities
  scripts/             # utility scripts (query runner, aircraft enrichment)
  streamlit_app/       # Streamlit pages
  tests/               # API inspection test scripts
  run_pipeline.py      # orchestration script
  config.py            # shared airport/filter config
  requirements.txt
  README.md
```

## Deliverables

- SQL database populated from AeroDataBox data
- API scripts for extraction and transformation
- Streamlit analytics application
- Consolidated project documentation (this README)

