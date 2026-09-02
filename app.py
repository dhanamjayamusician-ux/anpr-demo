"""
City-Wide ANPR Trajectory Tracking & Traffic Analytics -- Demo Dashboard

Run:
    streamlit run app.py

Tabs:
    1. Trajectory Tracking -- search a plate, see its path on a map + timeline
    2. Traffic Analytics    -- city-wide heatmap, density, avg speed trends
    3. Alerts               -- blacklist match simulation
"""
import os
import datetime as dt
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="City ANPR Command Center", layout="wide")

CAMERAS_CSV = "data/cameras.csv"
DETECTIONS_CSV = "data/db/detections.csv"
TRAFFIC_CSV = "data/db/traffic_stats.csv"
BLACKLIST_CSV = "data/blacklist.csv"


@st.cache_data
def load_data():
    cameras = pd.read_csv(CAMERAS_CSV)
    detections = pd.DataFrame()
    traffic = pd.DataFrame()
    blacklist = pd.DataFrame()

    if os.path.exists(DETECTIONS_CSV):
        detections = pd.read_csv(DETECTIONS_CSV, parse_dates=["timestamp"])
        detections = detections.merge(cameras, on="camera_id", how="left")

    if os.path.exists(TRAFFIC_CSV):
        traffic = pd.read_csv(TRAFFIC_CSV, parse_dates=["timestamp"])

    if os.path.exists(BLACKLIST_CSV):
        blacklist = pd.read_csv(BLACKLIST_CSV)

    return cameras, detections, traffic, blacklist


cameras, detections, traffic, blacklist = load_data()

st.title("🚦 City-Wide ANPR Command Center")
st.caption("Multi-camera trajectory tracking & traffic analytics platform")

tab1, tab2, tab3 = st.tabs(["🔍 Plate Trajectory", "📊 Traffic Analytics", "🚨 Alerts"])

# ---------------------------------------------------------------------------
# TAB 1: Trajectory Tracking
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Single Plate Trajectory Reconstruction")

    if detections.empty:
        st.warning("No detections yet. Run `python run_ocr.py` after adding images to data/images/.")
    else:
        plate_options = sorted(detections["plate_number"].unique())
        selected_plate = st.selectbox("Search plate number", plate_options)

        plate_df = detections[detections["plate_number"] == selected_plate].sort_values("timestamp")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Route for `{selected_plate}`** — {len(plate_df)} sighting(s)")

            if not plate_df.empty:
                center_lat = plate_df["latitude"].mean()
                center_lon = plate_df["longitude"].mean()
                m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

                coords = []
                for i, row in plate_df.reset_index(drop=True).iterrows():
                    coords.append((row["latitude"], row["longitude"]))
                    folium.Marker(
                        location=[row["latitude"], row["longitude"]],
                        popup=f"{row['name']}<br>{row['timestamp']}",
                        tooltip=f"Stop {i+1}: {row['name']}",
                        icon=folium.Icon(color="blue" if i > 0 else "green", icon="camera"),
                    ).add_to(m)

                if len(coords) > 1:
                    folium.PolyLine(coords, color="red", weight=3, opacity=0.7).add_to(m)

                st_folium(m, width=700, height=450)

        with col2:
            st.markdown("**Timeline**")
            for _, row in plate_df.iterrows():
                st.markdown(
                    f"🕒 **{row['timestamp'].strftime('%H:%M:%S')}**  \n"
                    f"📍 {row['name']} ({row['camera_id']})  \n"
                    f"Confidence: {row['confidence']*100:.1f}%"
                )
                st.divider()

# ---------------------------------------------------------------------------
# TAB 2: Traffic Analytics
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("City-Wide Traffic Flow Analytics")

    if traffic.empty:
        st.warning("No traffic data yet. Run `python generate_traffic_data.py` first.")
    else:
        latest = traffic.sort_values("timestamp").groupby("camera_id").last().reset_index()

        c1, c2, c3 = st.columns(3)
        c1.metric("Avg City Speed", f"{latest['avg_speed_kmph'].mean():.1f} km/h")
        c2.metric("Avg Density", f"{latest['density_pct'].mean():.1f}%")
        c3.metric("High Congestion Zones", int((latest["congestion_level"] == "High").sum()))

        st.markdown("**Live Congestion Heatmap**")
        m2 = folium.Map(
            location=[latest["latitude"].mean(), latest["longitude"].mean()], zoom_start=11
        )
        color_map = {"High": "red", "Medium": "orange", "Low": "green"}
        for _, row in latest.iterrows():
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=8 + row["density_pct"] / 8,
                color=color_map[row["congestion_level"]],
                fill=True,
                fill_opacity=0.7,
                popup=(
                    f"{row['camera_name']}<br>Density: {row['density_pct']}%"
                    f"<br>Avg Speed: {row['avg_speed_kmph']} km/h"
                    f"<br>Status: {row['congestion_level']}"
                ),
            ).add_to(m2)
        st_folium(m2, width=900, height=450)

        st.markdown("**24-Hour Density Trend by Camera**")
        pivot = traffic.pivot_table(index="timestamp", columns="camera_name", values="density_pct")
        st.line_chart(pivot)

        st.markdown("**Camera-wise Snapshot**")
        st.dataframe(
            latest[["camera_name", "vehicle_count", "density_pct", "avg_speed_kmph", "congestion_level"]]
            .sort_values("density_pct", ascending=False),
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# TAB 3: Alerts
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Blacklisted Vehicle Alerts")

    if blacklist.empty:
        st.info("No blacklist file found at data/blacklist.csv. Add plate numbers to test alerts.")
    elif detections.empty:
        st.warning("No detections to check against the blacklist yet.")
    else:
        flagged = detections[detections["plate_number"].isin(blacklist["plate_number"])]

        if flagged.empty:
            st.success("✅ No blacklisted vehicles detected in current feed.")
        else:
            st.error(f"🚨 {len(flagged)} blacklist match(es) found!")
            for _, row in flagged.sort_values("timestamp", ascending=False).iterrows():
                reason = blacklist.loc[
                    blacklist["plate_number"] == row["plate_number"], "reason"
                ].values
                reason_text = reason[0] if len(reason) else "Flagged vehicle"
                st.markdown(
                    f"**{row['plate_number']}** spotted at **{row['name']}** "
                    f"on {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}  \n"
                    f"Reason: _{reason_text}_"
                )
                st.divider()

        st.markdown("**Current Blacklist**")
        st.dataframe(blacklist, use_container_width=True)
