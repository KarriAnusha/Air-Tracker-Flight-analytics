import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection
from config import airport_filter_clause


@st.cache_data(ttl=300)
def fetch_delay_percentage_by_airport():
    """Fetch percentage of delayed flights by airport."""
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
        ld.delay_date,
        ROUND(
            ((ld.delayed_flights::float / NULLIF(ld.total_flights, 0)) * 100)::numeric, 2
        ) as delay_percentage,
        ld.total_flights as total_flights,
        ld.delayed_flights as delayed_flights,
        ROUND(ld.avg_delay_min::numeric, 2) as avg_delay_min
    FROM latest_delay ld
    WHERE {airport_filter_clause(alias='ld', column='airport_iata')}
      AND ld.rn = 1
    ORDER BY delay_percentage DESC
    """
    return pd.read_sql(query, conn)


def show_delays():
    """Display a single-page delay overview."""
    st.title("Delay Analysis")
    st.markdown("Single-page overview of airport delay performance.")

    try:
        airport_delays = fetch_delay_percentage_by_airport()
        if airport_delays.empty:
            st.info("No airport delay data available")
            return

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Delay Rate by Airport")
            st.bar_chart(
                airport_delays.set_index("airport_iata")["delay_percentage"],
                use_container_width=True,
            )

        with col2:
            top = airport_delays.iloc[0]
            st.metric("Most Delayed Airport", top["airport_iata"])
            st.metric("Delay Rate", f"{top['delay_percentage']:.1f}%")
            avg_delay = top["avg_delay_min"]
            st.metric("Avg Delay (min)", f"{avg_delay:.1f}" if pd.notna(avg_delay) else "N/A")

        st.subheader("Airport Delay Details")
        display_df = airport_delays[
            ["airport_iata", "delay_percentage", "total_flights", "delayed_flights", "avg_delay_min"]
        ].copy()
        display_df.columns = ["Airport", "Delay %", "Total Flights", "Delayed Flights", "Avg Delay (min)"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading delay analysis: {str(e)}")
        st.info("Please ensure the database is connected and populated with delay data.")
