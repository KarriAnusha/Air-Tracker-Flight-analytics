import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection
from config import airport_filter_clause, flight_filter_clause


@st.cache_data(ttl=300)
def fetch_busiest_routes():
    conn = get_connection()
    query = f"""
    SELECT
        f.origin_iata,
        f.destination_iata,
        a_orig.name AS origin_name,
        a_dest.name AS destination_name,
        COUNT(*) AS flight_count
    FROM flights f
    LEFT JOIN airport a_orig ON f.origin_iata = a_orig.iata_code
    LEFT JOIN airport a_dest ON f.destination_iata = a_dest.iata_code
    WHERE {flight_filter_clause()}
    GROUP BY f.origin_iata, f.destination_iata, a_orig.name, a_dest.name
    ORDER BY flight_count DESC
    LIMIT 20
    """
    return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def fetch_most_delayed_airports():
    conn = get_connection()
    query = f"""
    WITH latest_delay AS (
        SELECT
            ad.*,
            ROW_NUMBER() OVER (
                PARTITION BY ad.airport_iata
                ORDER BY ad.delay_date DESC, ad.delay_id DESC
            ) AS rn
        FROM airport_delays ad
    )
    SELECT
        ld.airport_iata,
        ap.name,
        ap.city,
        ld.delay_date,
        ROUND(
            ((ld.delayed_flights::numeric / NULLIF(ld.total_flights, 0)) * 100)::numeric,
            2
        ) AS delay_percentage,
        ld.total_flights,
        ld.delayed_flights,
        ld.avg_delay_min AS avg_delay_minutes
    FROM latest_delay ld
    LEFT JOIN airport ap ON ld.airport_iata = ap.iata_code
    WHERE {airport_filter_clause('ap')}
      AND ld.rn = 1
    ORDER BY delay_percentage DESC
    LIMIT 20
    """
    return pd.read_sql(query, conn)


def show_leaderboards():
    """Display only required route leaderboard tables."""
    st.title("Route Leaderboards")
    st.markdown("Busiest routes and most delayed airports.")

    try:
        st.subheader("Busiest Routes (Most Flights)")
        busiest = fetch_busiest_routes()
        if busiest.empty:
            st.info("No route data available.")
        else:
            st.dataframe(busiest, use_container_width=True, hide_index=True)

        st.subheader("Most Delayed Airports")
        delayed = fetch_most_delayed_airports()
        if delayed.empty:
            st.info("No delay leaderboard data available.")
        else:
            st.dataframe(delayed, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading route leaderboards: {str(e)}")
        st.info("Please ensure the database is connected and populated with data.")
