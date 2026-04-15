# ⚾ The $85M Hit Drought Tracker

A Streamlit app tracking 2026 batting stats for the Phillies' core four:
Bryce Harper, Kyle Schwarber, Trea Turner, and J.T. Realmuto.

## Running Locally

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the app**
```bash
streamlit run app.py
```

3. Open your browser to `http://localhost:8501`

---

## Deploying to Streamlit Community Cloud

1. Push this project to a **GitHub repository**

2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub

3. Click **"New app"** and select your repository

4. Set:
   - **Branch:** main
   - **Main file path:** app.py

5. Click **Deploy!**

> ⚠️ **Important:** The `data/` folder with CSV files must be committed to GitHub for the app to work on first deploy. The CSVs will update as you log games, but on Streamlit Community Cloud the data resets if the app redeploys. For persistent data across redeployments, consider adding the `data/` folder to your repo and committing updates periodically, or upgrading to a cloud database later.

---

## Project Structure

```
phillies-tracker/
├── app.py              # Main Streamlit app
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── data/
    ├── game_log.csv    # All logged game entries
    └── team_record.csv # Team W/L record
```

---

## Features

- **Team Dashboard** — W/L record, combined production, BA/OBP/SLG/OPS leaderboards
- **Players Dashboard** — Per-player drought tracker, hit streaks, full stat lines
- **Game Log** — Full history with multi-hit game highlights, edit & delete
- **Log Game** — Full stat entry form (PA, AB, H, 2B, 3B, HR, BB, HBP, SF, R, RBI)
- **CSV Export** — Download all data anytime

---

*"Turning chaos into clarity" — jesshaydenconsulting.com*
