import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

# ── CONFIG ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The $85M Hit Drought Tracker",
    page_icon="⚾",
    layout="wide",
)

PLAYERS = ["Bryce Harper", "Kyle Schwarber", "Trea Turner", "J.T. Realmuto"]
PLAYER_NUMBERS = {"Bryce Harper": "3", "Kyle Schwarber": "12", "Trea Turner": "7", "J.T. Realmuto": "10"}
LOG_PATH = "data/game_log.csv"
RECORD_PATH = "data/team_record.csv"

LOG_COLS = ["player","date","opponent","pa","ab","hits","doubles","triples","hr","bb","hbp","sf","r","rbi"]
RECORD_COLS = ["wins","losses"]

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+3:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
}

.stApp {
    background-color: #0d0d0d;
    color: #f0ece4;
}

/* Header */
.tracker-header {
    background: linear-gradient(135deg, #c8102e 0%, #9b0c23 60%, #6e0018 100%);
    padding: 28px 32px 22px;
    border-bottom: 3px solid #e8d5a0;
    margin: -1rem -1rem 1.5rem -1rem;
    border-radius: 0;
}
.tracker-header .eyebrow {
    font-size: 11px;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #e8d5a0;
    margin-bottom: 6px;
}
.tracker-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    color: #ffffff;
    margin: 0 0 4px 0;
    line-height: 1.1;
}
.tracker-header .season {
    font-size: 12px;
    color: rgba(255,255,255,0.55);
    letter-spacing: 1px;
}

/* Cards */
.card {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.card-title {
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #e8d5a0;
    margin-bottom: 12px;
}

/* Player card header */
.player-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}
.player-badge {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: linear-gradient(135deg, #c8102e, #9b0c23);
    border: 2px solid rgba(232,213,160,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: #e8d5a0;
    font-size: 13px;
    flex-shrink: 0;
}
.player-name {
    font-size: 18px;
    font-weight: 700;
    color: #f0ece4;
}
.player-meta {
    font-size: 11px;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.streak-badge {
    color: #4ade80;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Stat cells */
.stat-grid {
    display: grid;
    gap: 0;
    border: 1px solid #1f1f1f;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 8px;
}
.stat-cell {
    padding: 10px 8px;
    text-align: center;
    border-right: 1px solid #1f1f1f;
    background: #111;
}
.stat-cell:last-child { border-right: none; }
.stat-label {
    font-size: 9px;
    color: #555;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.stat-value {
    font-size: 16px;
    font-weight: 700;
    color: #f0ece4;
}
.stat-value.gold { color: #e8d5a0; }
.stat-value.green { color: #4ade80; }
.stat-value.red { color: #c8102e; }
.stat-sub {
    font-size: 9px;
    color: #444;
    margin-top: 2px;
}

/* Drought warning */
.drought-warning {
    background: rgba(200,16,46,0.12);
    border-top: 1px solid rgba(200,16,46,0.2);
    border-radius: 0 0 8px 8px;
    padding: 8px 12px;
    text-align: center;
    font-size: 12px;
    color: #c8102e;
}

/* Multi-hit badge */
.multihit-badge {
    background: rgba(200,168,0,0.15);
    border: 1px solid #c8a800;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    color: #c8a800;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Leaderboard row */
.lb-row {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid #1a1a1a;
    gap: 12px;
}
.lb-row:last-child { border-bottom: none; }

/* Record numbers */
.record-wins { font-size: 36px; font-weight: 700; color: #4ade80; }
.record-losses { font-size: 36px; font-weight: 700; color: #c8102e; }
.record-pct { font-size: 36px; font-weight: 700; color: #e8d5a0; }

/* Streamlit overrides */
div[data-testid="stMetric"] {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 12px;
}
div[data-testid="stMetric"] label { color: #888 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 1px; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #e8d5a0 !important; font-size: 22px !important; }

.stTabs [data-baseweb="tab-list"] {
    background: #111;
    border-bottom: 1px solid #2a2a2a;
}
.stTabs [data-baseweb="tab"] {
    color: #666;
    font-size: 12px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-family: 'Source Sans 3', sans-serif;
}
.stTabs [aria-selected="true"] {
    color: #e8d5a0 !important;
    border-bottom: 2px solid #c8102e !important;
}
.stTabs [data-baseweb="tab-panel"] { background: #0d0d0d; padding-top: 16px; }

div[data-testid="stForm"] {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 20px;
}

.stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label {
    color: #888 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #c8102e, #9b0c23) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    width: 100%;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.stDataFrame { border: 1px solid #2a2a2a; border-radius: 8px; }

.stButton button {
    background: #161616 !important;
    color: #888 !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
}
.stButton button:hover {
    border-color: #c8102e !important;
    color: #f0ece4 !important;
}

hr { border-color: #2a2a2a; }

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── DATA LAYER ───────────────────────────────────────────────────────────────
def load_log():
    if os.path.exists(LOG_PATH):
        df = pd.read_csv(LOG_PATH)
        for col in LOG_COLS:
            if col not in df.columns:
                df[col] = 0
        df["date"] = pd.to_datetime(df["date"]).dt.date
        for col in ["pa","ab","hits","doubles","triples","hr","bb","hbp","sf","r","rbi"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        return df
    return pd.DataFrame(columns=LOG_COLS)

def save_log(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(LOG_PATH, index=False)

def load_record():
    if os.path.exists(RECORD_PATH):
        df = pd.read_csv(RECORD_PATH)
        return int(df["wins"].iloc[0]), int(df["losses"].iloc[0])
    return 0, 0

def save_record(wins, losses):
    os.makedirs("data", exist_ok=True)
    pd.DataFrame({"wins": [wins], "losses": [losses]}).to_csv(RECORD_PATH, index=False)


# ── STAT CALCULATIONS ────────────────────────────────────────────────────────
def calc_stats(df):
    if df.empty:
        return {"ab":0,"h":0,"2b":0,"3b":0,"hr":0,"bb":0,"hbp":0,"sf":0,"r":0,"rbi":0,
                "ba":".000","obp":".000","slg":".000","ops":".000",
                "ba_raw":0,"obp_raw":0,"slg_raw":0,"ops_raw":0}
    ab  = df["ab"].sum()
    h   = df["hits"].sum()
    d   = df["doubles"].sum()
    t   = df["triples"].sum()
    hr  = df["hr"].sum()
    bb  = df["bb"].sum()
    hbp = df["hbp"].sum()
    sf  = df["sf"].sum()
    r   = df["r"].sum()
    rbi = df["rbi"].sum()
    singles = h - d - t - hr
    tb = singles + 2*d + 3*t + 4*hr
    obp_denom = ab + bb + hbp + sf
    ba_raw  = h/ab if ab > 0 else 0
    obp_raw = (h+bb+hbp)/obp_denom if obp_denom > 0 else 0
    slg_raw = tb/ab if ab > 0 else 0
    ops_raw = obp_raw + slg_raw
    def fmt(v): return (f"{v:.3f}").lstrip("0") or ".000"
    return {
        "ab":ab,"h":h,"2b":d,"3b":t,"hr":hr,"bb":bb,"hbp":hbp,"sf":sf,"r":r,"rbi":rbi,
        "ba":fmt(ba_raw),"obp":fmt(obp_raw),"slg":fmt(slg_raw),
        "ops":f"{ops_raw:.3f}",
        "ba_raw":ba_raw,"obp_raw":obp_raw,"slg_raw":slg_raw,"ops_raw":ops_raw,
    }

def calc_streak(pdf):
    if pdf.empty: return 0, 0, None, None
    sorted_df = pdf.sort_values("date", ascending=False)
    hit_streak = 0
    games_since = 0
    ab_since = 0
    last_hit_date = None
    last_hit_opp = None
    drought_done = False
    streak_done = False
    for _, row in sorted_df.iterrows():
        if not drought_done:
            if row["hits"] > 0:
                drought_done = True
                last_hit_date = row["date"]
                last_hit_opp = row["opponent"]
            else:
                games_since += 1
                ab_since += row["ab"]
        if not streak_done:
            if row["hits"] > 0:
                hit_streak += 1
            else:
                streak_done = True
    return hit_streak, games_since, ab_since, last_hit_date, last_hit_opp

def elapsed_days(d):
    if d is None: return "—"
    delta = (date.today() - d).days
    if delta == 0: return "Today"
    return f"{delta}d ago"


# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tracker-header">
    <div class="eyebrow">Philadelphia Phillies</div>
    <h1>The $85M Hit Drought Tracker</h1>
    <div class="season">2026 Season</div>
</div>
""", unsafe_allow_html=True)


# ── LOAD DATA ────────────────────────────────────────────────────────────────
log_df = load_log()
wins, losses = load_record()


# ── TABS ─────────────────────────────────────────────────────────────────────
tab_team, tab_players, tab_log, tab_entry = st.tabs(["🏆 Team", "⚾ Players", "📋 Game Log", "➕ Log Game"])


# ══════════════════════════════════════════════════════════════════════════════
# TEAM TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_team:

    # Record
    st.markdown('<div class="card"><div class="card-title">2026 Team Record</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Wins", wins)
    with col2: st.metric("Losses", losses)
    with col3:
        total = wins + losses
        pct = f"{(wins/total*100):.1f}%" if total > 0 else "—"
        st.metric("Win %", pct)

    with st.expander("✏️ Update Team Record"):
        with st.form("record_form"):
            rc1, rc2 = st.columns(2)
            new_wins = rc1.number_input("Wins", min_value=0, value=wins, step=1)
            new_losses = rc2.number_input("Losses", min_value=0, value=losses, step=1)
            if st.form_submit_button("Save Record"):
                save_record(int(new_wins), int(new_losses))
                st.success("Record updated!")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Combined production
    all_stats = {p: calc_stats(log_df[log_df["player"] == p]) for p in PLAYERS}
    total_ab  = sum(s["ab"]  for s in all_stats.values())
    total_h   = sum(s["h"]   for s in all_stats.values())
    total_hr  = sum(s["hr"]  for s in all_stats.values())
    total_r   = sum(s["r"]   for s in all_stats.values())
    total_rbi = sum(s["rbi"] for s in all_stats.values())
    cba_raw   = total_h / total_ab if total_ab > 0 else 0
    cba       = f"{cba_raw:.3f}".lstrip("0") or ".000"

    st.markdown('<div class="card"><div class="card-title">Combined $85M Production</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("BA",  cba)
    c2.metric("H",   total_h)
    c3.metric("HR",  total_hr)
    c4.metric("R",   total_r)
    c5.metric("RBI", total_rbi)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Leaderboard
    st.markdown('<div class="card"><div class="card-title">Leaderboard</div>', unsafe_allow_html=True)
    lb_stat = st.radio("Sort by", ["BA","OBP","SLG","OPS"], horizontal=True, label_visibility="collapsed")
    stat_key = {"BA":"ba_raw","OBP":"obp_raw","SLG":"slg_raw","OPS":"ops_raw"}[lb_stat]
    disp_key = lb_stat.lower()
    medals = ["🥇","🥈","🥉","4️⃣"]

    lb_data = sorted(PLAYERS, key=lambda p: all_stats[p][stat_key], reverse=True)
    for rank, player in enumerate(lb_data):
        s = all_stats[player]
        val = s[disp_key]
        val_raw = s[stat_key]
        if lb_stat == "BA":   color = "green" if val_raw >= 0.280 else ("gold" if val_raw >= 0.230 else "red")
        elif lb_stat == "OBP": color = "green" if val_raw >= 0.350 else ("gold" if val_raw >= 0.300 else "red")
        elif lb_stat == "SLG": color = "green" if val_raw >= 0.450 else ("gold" if val_raw >= 0.380 else "red")
        else:                  color = "green" if val_raw >= 0.800 else ("gold" if val_raw >= 0.680 else "red")
        colors = {"green":"#4ade80","gold":"#e8d5a0","red":"#c8102e"}
        c = colors[color]
        st.markdown(f"""
        <div style="display:flex;align-items:center;padding:12px 8px;border-bottom:1px solid #1a1a1a;gap:12px;">
            <div style="font-size:20px;width:28px">{medals[rank]}</div>
            <div style="width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#c8102e,#9b0c23);
                display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;color:#e8d5a0;flex-shrink:0">
                #{PLAYER_NUMBERS[player]}</div>
            <div style="flex:1">
                <div style="font-size:15px;font-weight:700;color:#f0ece4">{player.split()[-1]}</div>
                <div style="font-size:11px;color:#555;margin-top:2px">{s['h']}H · {s['hr']}HR · {s['rbi']}RBI · {s['bb']}BB</div>
            </div>
            <div style="font-size:24px;font-weight:700;color:{c}">{val}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # CSV Export
    if not log_df.empty:
        csv = log_df.to_csv(index=False)
        st.download_button("⬇️ Export to CSV", csv, "phillies_hit_tracker_2026.csv", "text/csv", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PLAYERS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_players:
    for player in PLAYERS:
        pdf = log_df[log_df["player"] == player].copy()
        s = calc_stats(pdf)
        hit_streak, games_since, ab_since, last_hit_date, last_hit_opp = calc_streak(pdf)
        drought = games_since >= 3
        games_logged = len(pdf)

        border_color = "#c8102e55" if drought else "#2a2a2a"
        box_shadow = "0 0 20px rgba(200,16,46,0.15)" if drought else "none"

        streak_html = f'<span class="streak-badge">🔥 {hit_streak}-game hit streak</span>' if hit_streak >= 2 else ""

        st.markdown(f"""
        <div style="background:#161616;border:1px solid {border_color};border-radius:12px;
            overflow:hidden;margin-bottom:16px;box-shadow:{box_shadow}">
            <div style="display:flex;align-items:center;padding:14px 16px;border-bottom:1px solid #1f1f1f;gap:12px">
                <div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#c8102e,#9b0c23);
                    border:2px solid rgba(232,213,160,0.3);display:flex;align-items:center;justify-content:center;
                    font-size:13px;font-weight:bold;color:#e8d5a0;flex-shrink:0">#{PLAYER_NUMBERS[player]}</div>
                <div style="flex:1">
                    <div style="font-size:17px;font-weight:700;color:#f0ece4">{player}</div>
                    <div style="font-size:11px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-top:2px">
                        {games_logged} games logged &nbsp; {streak_html}
                    </div>
                </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;border-bottom:1px solid #1f1f1f">
                {"".join([f'<div style="padding:12px 10px;text-align:center;border-right:{("1px solid #1f1f1f" if i<2 else "none")}"><div style="font-size:9px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px">{lbl}</div><div style="font-size:13px;font-weight:bold;color:#f0ece4">{val}</div><div style="font-size:9px;color:#444;margin-top:2px">{sub}</div></div>' for i,(lbl,val,sub) in enumerate([
                    ("Last Hit", last_hit_date.strftime("%b %-d, %Y") if last_hit_date else "—", f"vs {last_hit_opp}" if last_hit_opp else "no data"),
                    ("Time Elapsed", elapsed_days(last_hit_date), "since last hit"),
                    ("Games / AB", f"{games_since}G / {ab_since}AB" if games_logged else "—", "since last hit"),
                ])])}
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr;border-bottom:1px solid #1f1f1f">
                {"".join([f'<div style="padding:10px 6px;text-align:center;border-right:{("1px solid #1f1f1f" if i<4 else "none")}"><div style="font-size:9px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px">{lbl}</div><div style="font-size:15px;font-weight:bold;color:#e8d5a0">{val}</div></div>' for i,(lbl,val) in enumerate([("H",s["h"]),("HR",s["hr"]),("R",s["r"]),("RBI",s["rbi"]),("BB",s["bb"])])])}
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr">
                {"".join([f'<div style="padding:10px 6px;text-align:center;border-right:{("1px solid #1f1f1f" if i<3 else "none")}"><div style="font-size:9px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px">{lbl}</div><div style="font-size:14px;font-weight:bold;color:#e8d5a0">{val}</div></div>' for i,(lbl,val) in enumerate([("BA",s["ba"]),("OBP",s["obp"]),("SLG",s["slg"]),("OPS",s["ops"])])])}
            </div>

            {"f'<div style=\"background:rgba(200,16,46,0.12);padding:8px 16px;border-top:1px solid rgba(200,16,46,0.2);text-align:center;font-size:12px;color:#c8102e\">⚠️ {games_since}-game hitless streak — {ab_since} AB without a hit</div>'" if drought else ""}
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GAME LOG TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_log:
    if log_df.empty:
        st.info("No games logged yet. Head to the Log Game tab to get started!")
    else:
        filter_player = st.selectbox("Filter by player", ["All"] + PLAYERS, label_visibility="collapsed")
        filtered = log_df if filter_player == "All" else log_df[log_df["player"] == filter_player]
        filtered = filtered.sort_values(["player","date"], ascending=[True, False])

        display_cols = ["player","date","opponent","ab","hits","doubles","triples","hr","bb","hbp","sf","r","rbi"]
        rename = {"player":"Player","date":"Date","opponent":"Opp","ab":"AB","hits":"H",
                  "doubles":"2B","triples":"3B","hr":"HR","bb":"BB","hbp":"HBP","sf":"SF","r":"R","rbi":"RBI"}

        display_df = filtered[display_cols].rename(columns=rename).copy()
        display_df["Date"] = display_df["Date"].astype(str)

        def highlight_multihit(row):
            if row["H"] >= 2:
                return ["background-color: #1a1500; color: #c8a800"] * len(row)
            return [""] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_multihit, axis=1),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("✏️ Edit or Delete an Entry")
        if not log_df.empty:
            log_df_display = log_df.copy()
            log_df_display["label"] = log_df_display.apply(
                lambda r: f"{r['player']} — {r['date']} vs {r['opponent']} ({r['hits']}H/{r['ab']}AB)", axis=1)
            entry_label = st.selectbox("Select entry", log_df_display["label"].tolist())
            selected_idx = log_df_display[log_df_display["label"] == entry_label].index[0]
            selected_row = log_df.loc[selected_idx]

            with st.form("edit_form"):
                st.markdown(f"**Editing:** {selected_row['player']} — {selected_row['date']} vs {selected_row['opponent']}")
                ec1, ec2 = st.columns(2)
                e_opp  = ec1.text_input("Opponent", value=str(selected_row["opponent"]))
                e_date = ec2.date_input("Date", value=pd.to_datetime(selected_row["date"]).date())
                ec3,ec4,ec5,ec6,ec7 = st.columns(5)
                e_pa   = ec3.number_input("PA",  min_value=0, value=int(selected_row.get("pa",0)))
                e_ab   = ec4.number_input("AB",  min_value=0, value=int(selected_row["ab"]))
                e_hits = ec5.number_input("H",   min_value=0, value=int(selected_row["hits"]))
                e_2b   = ec6.number_input("2B",  min_value=0, value=int(selected_row.get("doubles",0)))
                e_3b   = ec7.number_input("3B",  min_value=0, value=int(selected_row.get("triples",0)))
                ec8,ec9,ec10,ec11,ec12,ec13 = st.columns(6)
                e_hr   = ec8.number_input("HR",  min_value=0, value=int(selected_row["hr"]))
                e_bb   = ec9.number_input("BB",  min_value=0, value=int(selected_row.get("bb",0)))
                e_hbp  = ec10.number_input("HBP",min_value=0, value=int(selected_row.get("hbp",0)))
                e_sf   = ec11.number_input("SF", min_value=0, value=int(selected_row.get("sf",0)))
                e_r    = ec12.number_input("R",  min_value=0, value=int(selected_row["r"]))
                e_rbi  = ec13.number_input("RBI",min_value=0, value=int(selected_row["rbi"]))

                sc1, sc2 = st.columns(2)
                save_btn = sc1.form_submit_button("💾 Save Changes", use_container_width=True)
                del_btn  = sc2.form_submit_button("🗑️ Delete Entry", use_container_width=True)

                if save_btn:
                    log_df.loc[selected_idx, ["date","opponent","pa","ab","hits","doubles","triples","hr","bb","hbp","sf","r","rbi"]] = [
                        e_date, e_opp, e_pa, e_ab, e_hits, e_2b, e_3b, e_hr, e_bb, e_hbp, e_sf, e_r, e_rbi]
                    save_log(log_df)
                    st.success("Entry updated!")
                    st.rerun()
                if del_btn:
                    log_df = log_df.drop(index=selected_idx)
                    save_log(log_df)
                    st.success("Entry deleted!")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# LOG GAME TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_entry:
    st.markdown("### Log a Game")
    with st.form("log_form", clear_on_submit=True):
        lc1, lc2 = st.columns(2)
        l_player = lc1.selectbox("Player", PLAYERS)
        l_date   = lc2.date_input("Game Date", value=date.today())
        l_opp    = st.text_input("Opponent (e.g. ARI, ATL, NYM)")

        st.markdown("**Counting Stats**")
        cc1,cc2,cc3,cc4,cc5 = st.columns(5)
        l_pa   = cc1.number_input("PA",  min_value=0, value=0)
        l_ab   = cc2.number_input("AB",  min_value=0, value=4)
        l_hits = cc3.number_input("H",   min_value=0, value=0)
        l_2b   = cc4.number_input("2B",  min_value=0, value=0)
        l_3b   = cc5.number_input("3B",  min_value=0, value=0)

        cc6,cc7,cc8,cc9,cc10,cc11,cc12 = st.columns(7)
        l_hr  = cc6.number_input("HR",  min_value=0, value=0)
        l_bb  = cc7.number_input("BB",  min_value=0, value=0)
        l_hbp = cc8.number_input("HBP", min_value=0, value=0)
        l_sf  = cc9.number_input("SF",  min_value=0, value=0)
        l_r   = cc10.number_input("R",  min_value=0, value=0)
        l_rbi = cc11.number_input("RBI",min_value=0, value=0)

        submitted = st.form_submit_button("⚾ Save Game", use_container_width=True)
        if submitted:
            if not l_opp:
                st.error("Please enter an opponent!")
            elif l_hits > l_ab:
                st.error("Hits can't exceed AB!")
            elif (l_2b + l_3b + l_hr) > l_hits:
                st.error("XBH can't exceed total hits!")
            else:
                new_row = pd.DataFrame([{
                    "player": l_player, "date": l_date, "opponent": l_opp.upper(),
                    "pa": l_pa, "ab": l_ab, "hits": l_hits, "doubles": l_2b,
                    "triples": l_3b, "hr": l_hr, "bb": l_bb, "hbp": l_hbp,
                    "sf": l_sf, "r": l_r, "rbi": l_rbi,
                }])
                log_df = pd.concat([log_df, new_row], ignore_index=True)
                save_log(log_df)
                st.success(f"✅ {l_player} — {l_date} vs {l_opp.upper()} logged!")
                st.rerun()
