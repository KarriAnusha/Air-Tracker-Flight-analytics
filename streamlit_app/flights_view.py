import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection
from config import flight_filter_clause


@st.cache_data(ttl=300)
def fetch_unique_values(column_name):
    """Fetch unique values for filter dropdowns."""
    conn = get_connection()

    base = f"FROM flights WHERE {flight_filter_clause()}"
    if column_name == "status":
        query = f"SELECT DISTINCT status {base} AND status IS NOT NULL ORDER BY status"
    elif column_name == "origin":
        query = f"SELECT DISTINCT origin_iata {base} AND origin_iata IS NOT NULL ORDER BY origin_iata"
    else:
        return ["All"]

    result = pd.read_sql(query, conn)
    return ["All"] + result.iloc[:, 0].tolist()


def fetch_flights_with_filters(search_text=None, status=None, origin=None, start_date=None, end_date=None):
    """Search by flight number or airline; filter by status, origin, and date range."""
    conn = get_connection()

    query = f"""
    SELECT
        f.flight_number,
        f.airline_code,
        f.origin_iata,
        f.destination_iata,
        COALESCE(f.aircraft_registration, 'Not Yet Assigned') AS aircraft_registration,
        f.scheduled_departure,
        f.actual_departure,
        f.scheduled_arrival,
        f.actual_arrival,
        f.status
    FROM flights f
    WHERE {flight_filter_clause()}
    """

    params = []

    if search_text:
        query += " AND (f.flight_number ILIKE %s OR f.airline_code ILIKE %s)"
        like = f"%{search_text}%"
        params.extend([like, like])

    if status and status != "All":
        query += " AND f.status = %s"
        params.append(status)

    if origin and origin != "All":
        query += " AND f.origin_iata = %s"
        params.append(origin)

    if start_date:
        query += " AND DATE(f.scheduled_departure) >= %s"
        params.append(start_date)

    if end_date:
        query += " AND DATE(f.scheduled_departure) <= %s"
        params.append(end_date)

    query += " ORDER BY f.scheduled_departure DESC LIMIT 500"
    return pd.read_sql(query, conn, params=params)


def show_flights():
    """Display the required search and filter flights section."""
    st.title("Search and Filter Flights")
    st.markdown("Search flights by number or airline, then filter by status, origin, or date range.")
    st.markdown(
        """
        <style>
        /* Ensure dropdown widgets show pointer cursor in this page */
        div[data-baseweb="select"] * {
            cursor: pointer !important;
        }
        div[data-baseweb="select"] svg {
            cursor: pointer !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        c1, c2, c3 = st.columns(3)

        with c1:
            search_text = st.text_input(
                "Search by Flight Number or Airline",
                placeholder="e.g., AI202 or AI",
            )

        with c2:
            status_options = fetch_unique_values("status")
            selected_status = st.selectbox("Status", status_options)

        with c3:
            origin_options = fetch_unique_values("origin")
            selected_origin = st.selectbox("Origin", origin_options)

        d1, d2 = st.columns(2)
        with d1:
            start_date = st.date_input("Start Date", value=None)
        with d2:
            end_date = st.date_input("End Date", value=None)

        if start_date and end_date and start_date > end_date:
            st.warning("Start Date cannot be after End Date.")
            return

        df = fetch_flights_with_filters(
            search_text=search_text.strip() if search_text else None,
            status=selected_status,
            origin=selected_origin,
            start_date=start_date,
            end_date=end_date,
        )

        st.metric("Matching Flights", len(df))

        if df.empty:
            st.info("No flights found for the selected criteria.")
            return

        st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading flights: {str(e)}")
        st.info("Please ensure the database is connected and populated with flight data.")
