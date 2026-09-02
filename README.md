# City-Wide ANPR Trajectory Tracking — SIH Demo

One-day hackathon demo. Real OCR, fake camera network, synthetic traffic
analytics, working trajectory search + heatmap dashboard.

## Setup (run once)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

First `easyocr` import will download model weights (~1-2 min, needs internet).

## Step-by-step

### 1. Generate the fake camera network
```bash
python generate_cameras.py
```
Edit `generate_cameras.py` to use real landmarks in your city if you want.

### 2. Add plate images
Drop photos of number plates into `data/images/`.
Best case: take 6-10 photos yourself on your phone, at different times, and
name them like:

```
CAM01_2026-08-31_08-15-00.jpg
CAM04_2026-08-31_09-40-00.jpg
CAM01_2026-08-31_11-05-00.jpg   <- same plate, different time = builds a route
```

Reusing the SAME physical plate (or the same car) across 3-4 "camera" photos
is what makes the trajectory demo actually show a route on the map. If you
don't do this, the script auto-assigns random cameras/times so it still runs,
but the story is weaker.

If you don't have real plate photos, search "indian license plate" images
online for a handful of test images — good enough for a demo.

### 3. Run OCR
```bash
python run_ocr.py
```
Reads every image, extracts plate text, writes `data/db/detections.csv`.
Check this file — OCR on printed/angled photos won't be perfect, so fix any
obviously wrong readings by hand in the CSV before your demo.

### 4. Generate traffic analytics data
```bash
python generate_traffic_data.py
```
Synthetic but realistic-looking density/speed/congestion data per camera.

### 5. Set up the blacklist alert demo
Edit `data/blacklist.csv` — put in one of the plate numbers that actually
showed up in `detections.csv` after step 3, so the alert fires live.

### 6. Launch the dashboard
```bash
streamlit run app.py
```
Opens in your browser. Three tabs: Trajectory Tracking, Traffic Analytics, Alerts.

## Demo script (suggested order in front of judges)

1. **Open with the problem** — isolated camera silos, no cross-camera tracking today.
2. **Tab 1 (Trajectory)** — search your test plate live, show the route
   drawing across the map with real timestamps. This is the core "wow" moment.
3. **Tab 2 (Analytics)** — pan through the heatmap, point out the rush-hour
   density spike in the line chart. Say: "in production this pulls from live
   camera feeds across the city — today it's simulated for demo purposes,
   but the pipeline is the same."
4. **Tab 3 (Alerts)** — trigger a blacklist match live, show the real-time flag.
5. **Close with scale** — OCR engine is swappable/pluggable (mention EasyOCR/
   PaddleOCR benchmarks for the >90% accuracy claim), architecture is designed
   to plug into a real citywide ANPR camera network via the same ingestion path.

## Honesty notes for Q&A

Be upfront if asked directly:
- Traffic analytics numbers are simulated — no live sensor network exists yet.
- OCR accuracy claim (>90%) is based on published EasyOCR/PaddleOCR benchmarks
  on standard plate datasets, not a benchmark you ran yourself today.
- Camera network is a small fixed demo set, not integrated with real city
  infrastructure — the point is proving the trajectory-linking architecture works.

Judges respect honesty about what's real vs. simulated far more than false
claims that don't hold up under a follow-up question.
