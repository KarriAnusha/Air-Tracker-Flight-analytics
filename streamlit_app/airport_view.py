import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection
from config import airport_filter_clause


@st.cache_data(ttl=300)
def fetch_all_airports():
    conn = get_connection()
    query = f"""
    SELECT iata_code, icao_code, name, city, country, latitude, longitude, timezone
    FROM airport
    WHERE {airport_filter_clause()}
    ORDER BY name
    """
    return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def fetch_airport_details(iata_code):
    conn = get_connection()
    query = """
    SELECT iata_code, icao_code, name, city, country, latitude, longitude, timezone
    FROM airport
    WHERE iata_code = %s
    """
    return pd.read_sql(query, conn, params=[iata_code])


@st.cache_data(ttl=300)
def fetch_linked_flights(iata_code):
    conn = get_connection()
    query = """
    (
        SELECT
            flight_number,
            airline_code,
            origin_iata,
            destination_iata,
            'Departure' AS flight_type,
            scheduled_departure AS scheduled_time,
            actual_departure AS actual_time,
            status
        FROM flights
        WHERE origin_iata = %s
    )
    UNION ALL
    (
        SELECT
            flight_number,
            airline_code,
            origin_iata,
            destination_iata,
            'Arrival' AS flight_type,
            COALESCE(scheduled_arrival, scheduled_departure) AS scheduled_time,
            COALESCE(actual_arrival, actual_departure) AS actual_time,
            status
        FROM flights
        WHERE destination_iata = %s
    )
    ORDER BY scheduled_time DESC
    LIMIT 100
    """
    return pd.read_sql(query, conn, params=[iata_code, iata_code])


def show_airports():
    """Display required airport details: location, timezone, linked flights."""
    st.title("Airport Details Viewer")
    st.markdown("View airport location/timezone and linked flights.")

    try:
        airports_df = fetch_all_airports()
        if airports_df.empty:
            st.info("No airport data available in database")
            return

        options = [f"{row['iata_code']} - {row['name']}" for _, row in airports_df.iterrows()]
        selected = st.selectbox("Select Airport", options)
        selected_iata = selected.split(" - ")[0]

        details_df = fetch_airport_details(selected_iata)
        if details_df.empty:
            st.info("No airport details found.")
            return

        details = details_df.iloc[0]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Airport", details["name"])
            st.metric("IATA", details["iata_code"])
        with c2:
            st.metric("Location", f"{details['city']}, {details['country']}")
            st.metric("Timezone", details["timezone"])
        with c3:
            st.metric("Latitude", f"{details['latitude']:.4f}")
            st.metric("Longitude", f"{details['longitude']:.4f}")

        st.subheader("Linked Flights")
        flights = fetch_linked_flights(selected_iata)
        if flights.empty:
            st.info("No linked flights available for this airport.")
            return

        st.dataframe(flights, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading airport details: {str(e)}")
        st.info("Please ensure the database is connected and populated with airport data.")
