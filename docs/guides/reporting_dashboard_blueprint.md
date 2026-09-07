# Technical Blueprint: SafeHaven & IX1 Sentinel Joint Reporting Dashboard

This architectural blueprint outlines how to build and deploy an interactive, high-performance reporting dashboard using **FastAPI**, **Pandas**, **Plotly / Matplotlib**, and **MoviePy**. 

It is designed to aggregate clinical metrics from the **SafeHaven TAY Database** (`recovery-app.db`) and zoning infractions from the **IX1 Sentinel Watchdog** (`sro-housing.db`) into a unified, secure reporting system for municipal directors and community advocates.

---

## 🏗️ System Architecture & Data Flow

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     SafeHaven Care Database     │       │     IX1 Sentinel SRO Database   │
│        (recovery-app.db)        │       │        (sro-housing.db)         │
└────────────────┬────────────────┘       └────────────────┬────────────────┘
                 │                                         │
                 └───────────────────┬─────────────────────┘
                                     │ (SQL Queries)
                                     ▼
                      ┌─────────────────────────────┐
                      │    Pandas Data Processor    │
                      │ • Data Cleanup & Pivoting   │
                      │ • Real-time Aggregation     │
                      └──────────────┬──────────────┘
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │      FastAPI Backend        │
                      │ • Secure REST JSON Endpoints│
                      │ • API Key Authentication    │
                      └──────────────┬──────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼ (REST JSON API)                       ▼ (REST JSON API)
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     Streamlit Front-End UI      │       │     MoviePy Briefing Engine     │
│ • Plotly Interactive Charts     │       │ • Weekly Video Summaries (.mp4) │
│ • Caseworker Override Buttons   │       │ • Automated Voiceover Stitching │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

---

## 1. Data Aggregation Pipeline (`Pandas` & `SQLite3`)

The reporting dashboard relies on loading data from SQLite3 and leveraging Pandas to perform real-time analytical aggregations, pivots, and trend calculations.

```python
import sqlite3
import pandas as pd

def get_dashboard_metrics():
    # 1. Connect to SafeHaven database
    conn = sqlite3.connect("recovery-app.db")
    
    # 2. Extract active medication-assisted treatment (MAT) counts
    mat_query = """
        SELECT medication_name, COUNT(id) as total_active 
        FROM mat_prescriptions 
        WHERE status = 'Active' 
        GROUP BY medication_name
    """
    df_mat = pd.read_sql_query(mat_query, conn)
    
    # 3. Extract bed occupancy and availability metrics
    bed_query = """
        SELECT name, facility_type, capacity, available_beds,
               (capacity - available_beds) as occupied_beds,
               ROUND(((capacity - available_beds) * 100.0 / capacity), 2) as occupancy_rate
        FROM facilities
    """
    df_beds = pd.read_sql_query(bed_query, conn)
    conn.close()
    
    return {
        "mat_summary": df_mat.to_dict(orient="records"),
        "bed_summary": df_beds.to_dict(orient="records")
    }
```

---

## 2. High-Performance REST API Service (`FastAPI`)

FastAPI serves as the secure backend API. It exposes endpoints that return aggregated metrics, validating tokens or API keys to protect sensitive client PII in compliance with HIPAA guidelines.

```python
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List, Dict

API_KEY = "safehaven_secure_dashboard_secret_token"
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI(title="SafeHaven & IX1 Sentinel Reporting API")

class MATMetric(BaseModel):
    medication_name: str
    total_active: int

class BedMetric(BaseModel):
    name: str
    facility_type: str
    capacity: int
    available_beds: int
    occupied_beds: int
    occupancy_rate: float

async def verify_api_key(header_value: str = Security(api_key_header)):
    if header_value == API_KEY:
        return header_value
    raise HTTPException(status_code=403, detail="Could not authorize dashboard request.")

@app.get("/api/v1/metrics/mat", response_model=List[MATMetric])
async def read_mat_metrics(token: str = Depends(verify_api_key)):
    metrics = get_dashboard_metrics()
    return metrics["mat_summary"]

@app.get("/api/v1/metrics/beds", response_model=List[BedMetric])
async def read_bed_metrics(token: str = Depends(verify_api_key)):
    metrics = get_dashboard_metrics()
    return metrics["bed_summary"]
```

---

## 3. Interactive Web Dashboard Frontend (`Streamlit` & `Plotly`)

Streamlit provides a clean, reactive frontend layout. Plotly is used to compile interactive, beautiful charts (such as bar charts or doughnut charts) that render directly on-screen.

```python
import streamlit as st
import plotly.express as px
import requests

st.set_page_col_config = {"layout": "wide"}
st.title("🛡️ SafeHaven & IX1 Sentinel Reporting Portal")

# 1. Fetch data from secure FastAPI endpoints
headers = {"X-API-Key": "safehaven_secure_dashboard_secret_token"}
try:
    beds_data = requests.get("http://127.0.0.1:8000/api/v1/metrics/beds", headers=headers).json()
    df_beds = pd.DataFrame(beds_data)
except Exception as e:
    st.error(f"Failed to fetch real-time metrics: {e}")
    df_beds = pd.DataFrame()

if not df_beds.empty:
    # 2. Render KPI Summary Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Unified Capacity", value=int(df_beds["capacity"].sum()))
    with col2:
        st.metric(label="Total Empty Beds Available", value=int(df_beds["available_beds"].sum()))
    with col3:
        st.metric(label="Average Occupancy Rate", value=f"{df_beds['occupancy_rate'].mean():.2f}%")

    # 3. Compile Plotly Interactive Visualization
    st.subheader("Crisis Bed Occupancy & Capacity by Facility")
    fig = px.bar(
        df_beds, 
        x="name", 
        y=["occupied_beds", "available_beds"],
        title="Bed Distribution Tracker",
        labels={"value": "Total Beds", "variable": "Bed Status"},
        barmode="stack",
        color_discrete_map={"occupied_beds": "#1f77b4", "available_beds": "#2ca02c"}
    )
    st.plotly_chart(fig, use_container_width=True)
```

---

## 4. Automated Video Briefing Generator (`MoviePy`)

For mobile advocates and caseworkers working directly in the field, this engine compiles static reporting charts, text summaries, and audio voiceover dispatches into a clean, 60-second video brief (.mp4) that can be easily shared or viewed on-the-go.

```python
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
import os

def generate_daily_briefing_video(image_path: str, audio_path: str, output_path: str):
    """
    Stitches a static dashboard visualization (e.g., compiled map or occupancy chart)
    together with a caseworker's recorded voice note into a standardized MP4 briefing.
    """
    if not os.path.exists(image_path) or not os.path.exists(audio_path):
        raise FileNotFoundError("Missing visual or audio inputs for MoviePy compiler.")
        
    # 1. Load the recorded voiceover brief
    audio_clip = AudioFileClip(audio_path)
    brief_duration = audio_clip.duration
    
    # 2. Set up the visualization clip to match the audio length
    visual_clip = ImageClip(image_path).set_duration(brief_duration)
    
    # 3. Merge audio and video layers into a single composite clip
    video_clip = visual_clip.set_audio(audio_clip)
    
    # 4. Export as a high-fidelity, mobile-ready MP4 file
    video_clip.write_videofile(
        output_path, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        temp_audiofile="/workspace/scratch/temp-audio.m4a",
        remove_temp=True
    )
    
    audio_clip.close()
    video_clip.close()
    print(f"Daily Briefing Video successfully generated at: {output_path}")

# Example Usage:
# generate_daily_briefing_video(
#     image_path="docs/assets/fccw_zoning_audit_map.png",
#     audio_path="voice_note_briefing.mp3",
#     output_path="/workspace/out/daily_zoning_alert_brief.mp4"
# )
```
