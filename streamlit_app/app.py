import os
import sys

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamlit_app.airport_view import show_airports
from streamlit_app.dashboard import show_dashboard
from streamlit_app.delay_analysis import show_delays
from streamlit_app.flights_view import show_flights
from streamlit_app.leaderboards import show_leaderboards

st.set_page_config(
    page_title='Air Tracker: Flight Analytics',
    page_icon='✈️',
    layout='wide',
    initial_sidebar_state='expanded',
)

st.sidebar.title('Air Tracker')
st.sidebar.markdown('Flight Analytics Dashboard')
st.sidebar.markdown('---')

page = st.sidebar.radio(
    'Navigation',
    ['Homepage Dashboard', 'Search and Filter Flights', 'Airport Details Viewer', 'Delay Analysis', 'Route Leaderboards'],
    help='Select a page to explore',
)

if page == 'Homepage Dashboard':
    show_dashboard()
elif page == 'Search and Filter Flights':
    show_flights()
elif page == 'Airport Details Viewer':
    show_airports()
elif page == 'Delay Analysis':
    show_delays()
elif page == 'Route Leaderboards':
    show_leaderboards()

st.markdown('---')
st.markdown(
    """
<div style='text-align: center; color: #888; margin-top: 2rem;'>
    <p>Air Tracker © 2026 | Powered by AeroDataBox API and Streamlit</p>
</div>
""",
    unsafe_allow_html=True,
)
