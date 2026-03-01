CREATE TABLE IF NOT EXISTS airport (
    airport_id SERIAL PRIMARY KEY,
    icao_code TEXT UNIQUE,
    iata_code TEXT UNIQUE,
    name TEXT,
    city TEXT,
    country TEXT,
    continent TEXT,
    latitude REAL,
    longitude REAL,
    timezone TEXT
);

CREATE TABLE IF NOT EXISTS aircraft (
    aircraft_id SERIAL PRIMARY KEY,
    registration TEXT UNIQUE,
    model TEXT,
    manufacturer TEXT,
    icao_type_code TEXT,
    owner TEXT
);

CREATE TABLE IF NOT EXISTS flights (
    flight_id TEXT PRIMARY KEY,
    flight_number TEXT,
    aircraft_registration TEXT,
    origin_iata TEXT,
    destination_iata TEXT,
    scheduled_departure TIMESTAMP,
    actual_departure TIMESTAMP,
    scheduled_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,
    status TEXT,
    airline_code TEXT,
    UNIQUE (flight_number, origin_iata, destination_iata, scheduled_departure)
);

CREATE TABLE IF NOT EXISTS airport_delays (
    delay_id SERIAL PRIMARY KEY,
    airport_iata TEXT,
    delay_date DATE,
    total_flights INTEGER,
    delayed_flights INTEGER,
    avg_delay_min INTEGER,
    median_delay_min INTEGER,
    canceled_flights INTEGER,
    UNIQUE (airport_iata, delay_date)
);
