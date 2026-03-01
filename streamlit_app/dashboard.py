import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection
from config import airport_filter_clause, flight_filter_clause


@st.cache_data(ttl=300)
def fetch_dashboard_metrics():
    """Return required homepage summary stats."""
    conn = get_connection()

    total_flights = pd.read_sql(
        f"SELECT COUNT(*) AS count FROM flights WHERE {flight_filter_clause()}", conn
    ).iloc[0, 0]

    total_airports = pd.read_sql(
        f"SELECT COUNT(*) AS count FROM airport WHERE {airport_filter_clause()}", conn
    ).iloc[0, 0]

    avg_delay = pd.read_sql(
        "SELECT COALESCE(AVG(avg_delay_min), 0) AS avg_delay FROM airport_delays", conn
    ).iloc[0, 0]

    return total_airports, total_flights, avg_delay


def show_dashboard():
    """Display only the required homepage summary statistics."""
    st.markdown(
        """
        <style>
        .dash-hero {
            background: linear-gradient(135deg, #0f3d63 0%, #1f77b4 100%);
            border-radius: 14px;
            padding: 20px 24px;
            color: #ffffff;
            margin-bottom: 14px;
        }
        .dash-sub {
            opacity: 0.9;
            margin-top: 6px;
            font-size: 0.98rem;
        }
        .metric-card {
            border: 1px solid #d9e2ec;
            border-radius: 12px;
            padding: 16px 18px;
            background: #ffffff;
            box-shadow: 0 3px 14px rgba(16, 24, 40, 0.06);
        }
        .metric-label {
            font-size: 0.9rem;
            color: #5b6b7a;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #102a43;
            line-height: 1.1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="dash-hero">
            <h2 style="margin:0;">Homepage Dashboard</h2>
            <div class="dash-sub">Live summary statistics from your SQL aviation dataset.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        total_airports, total_flights, avg_delay = fetch_dashboard_metrics()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Total Airports</div>
                    <div class="metric-value">{int(total_airports):,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Total Flights Fetched</div>
                    <div class="metric-value">{int(total_flights):,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Average Delay Across Airports (min)</div>
                    <div class="metric-value">{float(avg_delay):.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        st.info("Please ensure the database is connected and populated with data.")
