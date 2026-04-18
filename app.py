import streamlit as st
import pandas as pd
import os
from datetime import date

# ── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="The $97.7M Hit Drought Tracker", page_icon="⚾", layout="wide")

PLAYERS = ["Bryce Harper", "Kyle Schwarber", "Trea Turner", "J.T. Realmuto"]
PLAYER_NUMBERS = {"Bryce Harper": "3", "Kyle Schwarber": "12", "Trea Turner": "7", "J.T. Realmuto": "10"}
PLAYER_IDS = {"Bryce Harper": "547180", "Kyle Schwarber": "656941", "Trea Turner": "607208", "J.T. Realmuto": "592663"}
PLAYER_SALARIES = {
    "Bryce Harper":   25_384_615,
    "Kyle Schwarber": 30_000_000,
    "Trea Turner":    27_272_727,
    "J.T. Realmuto":  15_000_000,
}
TOTAL_SALARY = sum(PLAYER_SALARIES.values())  # $97,657,342
SEASON_GAMES = 162

def headshot_url(player):
    pid = PLAYER_IDS[player]
    return f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{pid}/headshot/67/current"

LOG_PATH    = "data/game_log.csv"
RECORD_PATH = "data/team_record.csv"
LOG_COLS    = ["player","date","opponent","home_away","pa","ab","hits","doubles","triples","hr","bb","hbp","sf","r","rbi","pa_vs_r","ab_vs_r","h_vs_r","hr_vs_r","bb_vs_r","hbp_vs_r","sf_vs_r","pa_vs_l","ab_vs_l","h_vs_l","hr_vs_l","bb_vs_l","hbp_vs_l","sf_vs_l","team_h","team_ab"]

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+3:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Source Sans 3', sans-serif; }
.stApp { background-color: #0d0d0d; color: #f0ece4; }
.tracker-header {
    background: linear-gradient(135deg, #c8102e 0%, #9b0c23 60%, #6e0018 100%);
    padding: 28px 32px 22px; border-bottom: 3px solid #e8d5a0;
    margin: -1rem -1rem 1.5rem -1rem;
}
.tracker-header .eyebrow { font-size:11px; letter-spacing:4px; text-transform:uppercase; color:#e8d5a0; margin-bottom:6px; }
.tracker-header h1 { font-family:'Playfair Display',serif; font-size:2.2rem; color:#fff; margin:0 0 4px 0; line-height:1.1; }
.tracker-header .season { font-size:12px; color:rgba(255,255,255,0.55); letter-spacing:1px; }
div[data-testid="stMetric"] { background:#161616; border:1px solid #2a2a2a; border-radius:8px; padding:12px; }
div[data-testid="stMetric"] label { color:#888 !important; font-size:11px !important; text-transform:uppercase; letter-spacing:1px; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color:#e8d5a0 !important; font-size:22px !important; }
.stTabs [data-baseweb="tab-list"] { background:#111; border-bottom:1px solid #2a2a2a; }
.stTabs [data-baseweb="tab"] { color:#666; font-size:12px; letter-spacing:1.5px; text-transform:uppercase; }
.stTabs [aria-selected="true"] { color:#e8d5a0 !important; border-bottom:2px solid #c8102e !important; }
.stTabs [data-baseweb="tab-panel"] { background:#0d0d0d; padding-top:16px; }
div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg,#c8102e,#9b0c23) !important;
    color:white !important; border:none !important; border-radius:8px !important; width:100%; font-weight:600;
}
.stButton button { background:#161616 !important; color:#888 !important; border:1px solid #333 !important; border-radius:8px !important; }
.stButton button:hover { border-color:#c8102e !important; color:#f0ece4 !important; }
#MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ── DATA ─────────────────────────────────────────────────────────────────────
def load_log():
    if os.path.exists(LOG_PATH):
        df = pd.read_csv(LOG_PATH)
        for col in LOG_COLS:
            if col not in df.columns:
                df[col] = 0 if col not in ["home_away","opponent","player","date"] else ""
        df["date"] = pd.to_datetime(df["date"]).dt.date
        int_cols = ["pa","ab","hits","doubles","triples","hr","bb","hbp","sf","r","rbi",
                    "pa_vs_r","ab_vs_r","h_vs_r","hr_vs_r","bb_vs_r","hbp_vs_r","sf_vs_r",
                    "pa_vs_l","ab_vs_l","h_vs_l","hr_vs_l","bb_vs_l","hbp_vs_l","sf_vs_l",
                    "team_h","team_ab"]
        for col in int_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        if "home_away" not in df.columns or df["home_away"].isnull().all():
            df["home_away"] = "Home"
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

def save_record(w, l):
    os.makedirs("data", exist_ok=True)
    pd.DataFrame({"wins":[w],"losses":[l]}).to_csv(RECORD_PATH, index=False)

# ── STATS ────────────────────────────────────────────────────────────────────
def calc_stats(df):
    if df.empty:
        return {k:0 for k in ["ab","h","2b","3b","hr","bb","hbp","sf","r","rbi","team_h","team_ab"]} | {"ba":".000","obp":".000","slg":".000","ops":".000","ba_raw":0,"obp_raw":0,"slg_raw":0,"ops_raw":0}
    ab=df["ab"].sum(); h=df["hits"].sum(); d=df["doubles"].sum(); t=df["triples"].sum()
    hr=df["hr"].sum(); bb=df["bb"].sum(); hbp=df["hbp"].sum(); sf=df["sf"].sum()
    r=df["r"].sum(); rbi=df["rbi"].sum()
    team_h=df["team_h"].sum(); team_ab=df["team_ab"].sum()
    singles=h-d-t-hr; tb=singles+2*d+3*t+4*hr
    obp_d=ab+bb+hbp+sf
    ba_r=h/ab if ab>0 else 0
    obp_r=(h+bb+hbp)/obp_d if obp_d>0 else 0
    slg_r=tb/ab if ab>0 else 0
    ops_r=obp_r+slg_r
    def fmt(v): return f"{v:.3f}".lstrip("0") or ".000"
    return {"ab":ab,"h":h,"2b":d,"3b":t,"hr":hr,"bb":bb,"hbp":hbp,"sf":sf,"r":r,"rbi":rbi,
            "team_h":int(team_h),"team_ab":int(team_ab),
            "ba":fmt(ba_r),"obp":fmt(obp_r),"slg":fmt(slg_r),"ops":f"{ops_r:.3f}",
            "ba_raw":ba_r,"obp_raw":obp_r,"slg_raw":slg_r,"ops_raw":ops_r}

def calc_streak(pdf):
    if pdf.empty: return 0, 0, 0, None, None
    sorted_df = pdf.sort_values("date", ascending=False)
    hit_streak=0; games_since=0; ab_since=0; last_hit_date=None; last_hit_opp=None
    drought_done=False; streak_done=False
    for _, row in sorted_df.iterrows():
        if not drought_done:
            if row["hits"]>0: drought_done=True; last_hit_date=row["date"]; last_hit_opp=row["opponent"]
            else: games_since+=1; ab_since+=row["ab"]
        if not streak_done:
            if row["hits"]>0: hit_streak+=1
            else: streak_done=True
    return hit_streak, games_since, ab_since, last_hit_date, last_hit_opp

def calc_hand_splits(df):
    """Calculate BA, OBP, SLG, OPS vs R and vs L pitchers."""
    def splits(ab, h, hr, bb, hbp, sf):
        singles = h - hr  # simplified: no 2B/3B split by hand stored
        tb = singles + 4 * hr  # simplified total bases
        obp_d = ab + bb + hbp + sf
        ba_r  = h/ab if ab > 0 else 0
        obp_r = (h+bb+hbp)/obp_d if obp_d > 0 else 0
        slg_r = tb/ab if ab > 0 else 0
        ops_r = obp_r + slg_r
        def fmt(v): return f"{v:.3f}".lstrip("0") or ".000"
        return {"ab":ab,"h":h,"hr":hr,"bb":bb,"ba":fmt(ba_r),"obp":fmt(obp_r),"slg":fmt(slg_r),"ops":f"{ops_r:.3f}"}
    if df.empty:
        empty = {"ab":0,"h":0,"hr":0,"bb":0,"ba":".000","obp":".000","slg":".000","ops":".000"}
        return empty, empty
    vs_r = splits(
        int(df["ab_vs_r"].sum()), int(df["h_vs_r"].sum()), int(df["hr_vs_r"].sum()),
        int(df["bb_vs_r"].sum()), int(df["hbp_vs_r"].sum()), int(df["sf_vs_r"].sum())
    )
    vs_l = splits(
        int(df["ab_vs_l"].sum()), int(df["h_vs_l"].sum()), int(df["hr_vs_l"].sum()),
        int(df["bb_vs_l"].sum()), int(df["hbp_vs_l"].sum()), int(df["sf_vs_l"].sum())
    )
    return vs_r, vs_l
    if d is None: return "—"
    delta=(date.today()-d).days
    return "Today" if delta==0 else f"{delta}d ago"

def elapsed_days(d):
    if d is None: return "—"
    delta = (date.today() - d).days
    return "Today" if delta == 0 else f"{delta}d ago"


def sparkline_svg(ba_series, width=120, height=32):
    """Generate a tiny SVG sparkline of BA over games."""
    if len(ba_series) < 2: return ""
    vals = list(ba_series)
    mn, mx = min(vals), max(vals)
    rng = mx - mn if mx != mn else 0.001
    pts = []
    for i, v in enumerate(vals):
        x = int(i / (len(vals)-1) * width)
        y = int((1 - (v - mn) / rng) * (height - 4) + 2)
        pts.append(f"{x},{y}")
    polyline = " ".join(pts)
    return f'<svg width="{width}" height="{height}" style="position:absolute;bottom:0;left:0;right:0;opacity:0.15"><polyline points="{polyline}" fill="none" stroke="#c8102e" stroke-width="1.5"/></svg>'

def running_ba(pdf):
    """Return list of cumulative BA after each game."""
    sorted_df = pdf.sort_values("date")
    bas = []
    cum_h = 0; cum_ab = 0
    for _, row in sorted_df.iterrows():
        cum_h += row["hits"]; cum_ab += row["ab"]
        bas.append(cum_h/cum_ab if cum_ab>0 else 0)
    return bas

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tracker-header">
    <div class="eyebrow">Philadelphia Phillies &nbsp;&middot;&nbsp; 2026 Season</div>
    <h1>The $97.7M Hit Drought Tracker</h1>
    <div class="season">📊 Stats updated every Saturday &mdash; or log games yourself in real time using the Log Game tab!</div>
</div>
""", unsafe_allow_html=True)

log_df = load_log()
wins, losses = load_record()

tab_team, tab_players, tab_log, tab_entry = st.tabs(["🏆 Team", "⚾ Players", "📋 Game Log", "➕ Log Game"])

# ══════════════════════════════════════════════════════════════════════════════
# TEAM TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_team:
    # Record
    st.markdown('<div style="background:#161616;border:1px solid #2a2a2a;border-radius:12px;padding:16px;margin-bottom:16px">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#e8d5a0;margin-bottom:12px">2026 Team Record</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric("Wins", wins)
    c2.metric("Losses", losses)
    total = wins+losses
    c3.metric("Win %", f"{wins/total*100:.1f}%" if total>0 else "—")
    with st.expander("✏️ Update Record"):
        with st.form("record_form"):
            rc1,rc2=st.columns(2)
            nw=rc1.number_input("Wins",min_value=0,value=wins,step=1)
            nl=rc2.number_input("Losses",min_value=0,value=losses,step=1)
            if st.form_submit_button("Save"):
                save_record(int(nw),int(nl)); st.success("Updated!"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Combined production
    all_stats = {p: calc_stats(log_df[log_df["player"]==p]) for p in PLAYERS}
    tot_ab=sum(s["ab"] for s in all_stats.values())
    tot_h =sum(s["h"]  for s in all_stats.values())
    tot_hr=sum(s["hr"] for s in all_stats.values())
    tot_r =sum(s["r"]  for s in all_stats.values())
    tot_rbi=sum(s["rbi"] for s in all_stats.values())
    cba = f"{tot_h/tot_ab:.3f}".lstrip("0") if tot_ab>0 else ".000"

    st.markdown('<div style="background:#161616;border:1px solid #2a2a2a;border-radius:12px;padding:16px;margin-bottom:16px">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#e8d5a0;margin-bottom:12px">Combined $97.7M Production</div>', unsafe_allow_html=True)
    p1,p2,p3,p4,p5=st.columns(5)
    p1.metric("BA",cba); p2.metric("H",tot_h); p3.metric("HR",tot_hr); p4.metric("R",tot_r); p5.metric("RBI",tot_rbi)
    st.markdown('</div>', unsafe_allow_html=True)

    # Core 4 vs Team comparison
    if not log_df.empty and "team_ab" in log_df.columns and log_df["team_ab"].sum() > 0:
        st.markdown('<div style="background:#161616;border:1px solid #2a2a2a;border-radius:12px;padding:16px;margin-bottom:16px">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#e8d5a0;margin-bottom:12px">Core 4 vs. Rest of Lineup</div>', unsafe_allow_html=True)

        # Per game comparison — use most recent game date
        game_dates = sorted(log_df["date"].dropna().unique(), reverse=True)
        recent = game_dates[0] if game_dates else None
        if recent:
            recent_df = log_df[log_df["date"]==recent]
            c4_h  = recent_df["hits"].sum()
            c4_ab = recent_df["ab"].sum()
            t_h   = recent_df["team_h"].sum() // max(len(recent_df),1) * 4  # avg team H scaled
            t_ab  = recent_df["team_ab"].sum() // max(len(recent_df),1) * 4
            # Use actual team totals from first row (same game)
            if len(recent_df) > 0:
                t_h  = int(recent_df["team_h"].iloc[0])
                t_ab = int(recent_df["team_ab"].iloc[0])
            rest_h  = t_h  - c4_h
            rest_ab = t_ab - c4_ab
            c4_ba   = f"{c4_h/c4_ab:.3f}".lstrip("0") if c4_ab>0 else ".000"
            rest_ba = f"{rest_h/rest_ab:.3f}".lstrip("0") if rest_ab>0 else ".000"
            team_ba = f"{t_h/t_ab:.3f}".lstrip("0") if t_ab>0 else ".000"
            st.markdown(f'<div style="font-size:11px;color:#666;margin-bottom:8px">Most recent game: {recent}</div>', unsafe_allow_html=True)
            cc1,cc2,cc3=st.columns(3)
            cc1.metric("Core 4 BA", c4_ba, f"{c4_h}H / {c4_ab}AB")
            cc2.metric("Rest of Lineup", rest_ba, f"{rest_h}H / {rest_ab}AB")
            cc3.metric("Full Team", team_ba, f"{t_h}H / {t_ab}AB")
        st.markdown('</div>', unsafe_allow_html=True)

    # Team hot/cold indicator
    streaks = {p: calc_streak(log_df[log_df["player"]==p])[0] for p in PLAYERS}
    droughts = {p: calc_streak(log_df[log_df["player"]==p])[1] for p in PLAYERS}
    hot_count  = sum(1 for v in streaks.values()  if v >= 2)
    cold_count = sum(1 for v in droughts.values() if v >= 3)
    if hot_count >= 3:
        st.markdown(f'<div style="background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.3);border-radius:10px;padding:12px 16px;text-align:center;font-size:14px;color:#4ade80;margin-bottom:16px">🔥 The $97.7M is ON FIRE! ({hot_count}/4 players on a hit streak)</div>', unsafe_allow_html=True)
    elif cold_count >= 3:
        st.markdown(f'<div style="background:rgba(147,197,253,0.1);border:1px solid rgba(147,197,253,0.3);border-radius:10px;padding:12px 16px;text-align:center;font-size:14px;color:#93c5fd;margin-bottom:16px">🧊 You\'re as cold as ice! ({cold_count}/4 players in a hitless drought)</div>', unsafe_allow_html=True)

    # Leaderboard
    st.markdown('<div style="background:#161616;border:1px solid #2a2a2a;border-radius:12px;padding:16px;margin-bottom:16px">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#e8d5a0;margin-bottom:12px">Leaderboard</div>', unsafe_allow_html=True)
    lb_stat = st.radio("Sort by", ["BA","OBP","SLG","OPS"], horizontal=True, label_visibility="collapsed")
    stat_key = {"BA":"ba_raw","OBP":"obp_raw","SLG":"slg_raw","OPS":"ops_raw"}[lb_stat]
    disp_key = lb_stat.lower()
    medals = ["🥇","🥈","🥉","4️⃣"]
    lb_data = sorted(PLAYERS, key=lambda p: all_stats[p][stat_key], reverse=True)
    for rank, player in enumerate(lb_data):
        s = all_stats[player]
        val_raw = s[stat_key]; val = s[disp_key]
        if lb_stat=="BA":   c="#4ade80" if val_raw>=0.280 else ("#e8d5a0" if val_raw>=0.230 else "#c8102e")
        elif lb_stat=="OBP": c="#4ade80" if val_raw>=0.350 else ("#e8d5a0" if val_raw>=0.300 else "#c8102e")
        elif lb_stat=="SLG": c="#4ade80" if val_raw>=0.450 else ("#e8d5a0" if val_raw>=0.380 else "#c8102e")
        else:                c="#4ade80" if val_raw>=0.800 else ("#e8d5a0" if val_raw>=0.680 else "#c8102e")
        st.markdown(f"""
        <div style="display:flex;align-items:center;padding:12px 8px;border-bottom:1px solid #1a1a1a;gap:12px">
            <div style="font-size:20px;width:28px">{medals[rank]}</div>
            <img src="{headshot_url(player)}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;border:2px solid #c8102e;flex-shrink:0" onerror="this.style.display='none'"/>
            <div style="flex:1">
                <div style="font-size:15px;font-weight:700;color:#f0ece4">{player.split()[-1]}</div>
                <div style="font-size:11px;color:#555;margin-top:2px">{s['h']}H · {s['hr']}HR · {s['rbi']}RBI · {s['bb']}BB</div>
            </div>
            <div style="font-size:24px;font-weight:700;color:{c}">{val}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not log_df.empty:
        csv = log_df.to_csv(index=False)
        st.download_button("⬇️ Export to CSV", csv, "phillies_hit_tracker_2026.csv", "text/csv", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PLAYERS TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_players:
    def stat_cell(lbl, val, sub="", border=True):
        br = "1px solid #1f1f1f" if border else "none"
        return f'<div style="padding:12px 10px;text-align:center;border-right:{br}"><div style="font-size:9px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px">{lbl}</div><div style="font-size:13px;font-weight:bold;color:#f0ece4">{val}</div><div style="font-size:9px;color:#444;margin-top:2px">{sub}</div></div>'

    def rate_cell(lbl, val, border=True):
        br = "1px solid #1f1f1f" if border else "none"
        return f'<div style="padding:10px 6px;text-align:center;border-right:{br}"><div style="font-size:9px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px">{lbl}</div><div style="font-size:15px;font-weight:bold;color:#e8d5a0">{val}</div></div>'

    for player in PLAYERS:
        pdf = log_df[log_df["player"]==player].copy()
        s = calc_stats(pdf)
        hit_streak, games_since, ab_since, last_hit_date, last_hit_opp = calc_streak(pdf)
        drought = games_since >= 3
        games_logged = len(pdf)

        border_color = "#c8102e55" if drought else ("#93c5fd33" if games_since >= 3 else "#2a2a2a")
        box_shadow = "0 0 20px rgba(200,16,46,0.15)" if drought else "none"

        # Status badge
        if hit_streak >= 2:
            status_html = f'<span style="color:#4ade80;font-size:11px;text-transform:uppercase;letter-spacing:1px">🔥 {hit_streak}-game hit streak</span>'
        elif games_since >= 3:
            status_html = f'<span style="color:#93c5fd;font-size:11px;text-transform:uppercase;letter-spacing:1px">🧊 You\'re as cold as ice!</span>'
        else:
            status_html = ""

        last_hit_str = last_hit_date.strftime("%b %d, %Y").replace(" 0"," ") if last_hit_date else "—"
        last_hit_sub = f"vs {last_hit_opp}" if last_hit_opp else "no data"
        elapsed_str  = elapsed_days(last_hit_date)
        games_ab_str = f"{games_since}G / {ab_since}AB" if games_logged else "—"

        vs_r, vs_l = calc_hand_splits(pdf)
        has_splits = vs_r["ab"] > 0 or vs_l["ab"] > 0

        # Pre-build all pieces
        ba_series = running_ba(pdf)
        spark = sparkline_svg(ba_series)
        drought_bar = f'<div style="background:rgba(200,16,46,0.12);padding:8px 16px;border-top:1px solid rgba(200,16,46,0.2);text-align:center;font-size:12px;color:#c8102e">&#9888; {games_since}-game hitless streak &mdash; {ab_since} AB without a hit</div>' if drought else ""

        cell_last   = stat_cell("Last Hit",    last_hit_str,  last_hit_sub,     True)
        cell_elap   = stat_cell("Time Elapsed", elapsed_str,  "since last hit",  True)
        cell_gab    = stat_cell("Games / AB",   games_ab_str, "since last hit",  False)
        cell_ba     = rate_cell("BA",  s["ba"],       True)
        cell_hr     = rate_cell("HR",  str(s["hr"]),  True)
        cell_rbi    = rate_cell("RBI", str(s["rbi"]), True)
        cell_ops    = rate_cell("OPS", s["ops"],       False)
        img_src     = headshot_url(player)
        num         = PLAYER_NUMBERS[player]

        splits_html = ""
        if has_splits:
            splits_html = (
                f'<div style="display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #1f1f1f">'
                f'<div style="padding:10px 12px;border-right:1px solid #1f1f1f">'
                f'<div style="font-size:9px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px">vs RHP &nbsp;<span style="color:#666">({vs_r["ab"]}AB)</span></div>'
                f'<div style="display:flex;gap:12px">'
                f'<span style="font-size:12px;color:#e8d5a0"><span style="font-size:9px;color:#555;text-transform:uppercase">BA </span>{vs_r["ba"]}</span>'
                f'<span style="font-size:12px;color:#e8d5a0"><span style="font-size:9px;color:#555;text-transform:uppercase">OBP </span>{vs_r["obp"]}</span>'
                f'<span style="font-size:12px;color:#e8d5a0"><span style="font-size:9px;color:#555;text-transform:uppercase">SLG </span>{vs_r["slg"]}</span>'
                f'<span style="font-size:12px;color:#e8d5a0"><span style="font-size:9px;color:#555;text-transform:uppercase">OPS </span>{vs_r["ops"]}</span>'
                f'</div></div>'
                f'<div style="padding:10px 12px">'
                f'<div style="font-size:9px;color:#555;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px">vs LHP &nbsp;<span style="color:#666">({vs_l["ab"]}AB)</span></div>'
                f'<div style="display:flex;gap:12px">'
                f'<span style="font-size:12px;color:#e8d5a0"><span style="font-size:9px;color:#555;text-transform:uppercase">BA </span>{vs_l["ba"]}</span>'
                f'<span style="font-size:12px;color:#e8d5a0"><span style="font-size:9px;color:#555;text-transform:uppercase">OBP </span>{vs_l["obp"]}</span>'
                f'<span style="font-size:12px;color:#e8d5a0"><span style="font-size:9px;color:#555;text-transform:uppercase">SLG </span>{vs_l["slg"]}</span>'
                f'<span style="font-size:12px;color:#e8d5a0"><span style="font-size:9px;color:#555;text-transform:uppercase">OPS </span>{vs_l["ops"]}</span>'
                f'</div></div>'
                f'</div>'
            )

        html = (
            f'<div style="background:#161616;border:1px solid {border_color};border-radius:12px;overflow:hidden;margin-bottom:16px;box-shadow:{box_shadow}">'
            f'<div style="display:flex;align-items:center;padding:14px 16px;border-bottom:1px solid #1f1f1f;gap:12px;position:relative">'
            f'{spark}'
            f'<img src="{img_src}" style="width:52px;height:52px;border-radius:50%;object-fit:cover;border:2px solid #c8102e;flex-shrink:0;position:relative;z-index:1"/>'
            f'<div style="flex:1;position:relative;z-index:1">'
            f'<div style="font-size:17px;font-weight:700;color:#f0ece4">{player}</div>'
            f'<div style="font-size:11px;color:#666;text-transform:uppercase;letter-spacing:1px;margin-top:2px">{games_logged} games logged &nbsp;&middot;&nbsp; #{num} &nbsp; {status_html}</div>'
            f'</div></div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;border-bottom:1px solid #1f1f1f">{cell_last}{cell_elap}{cell_gab}</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr">{cell_ba}{cell_hr}{cell_rbi}{cell_ops}</div>'
            f'{splits_html}'
            f'{drought_bar}'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GAME LOG TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_log:
    if log_df.empty:
        st.info("No games logged yet. Head to the Log Game tab to get started!")
    else:
        filter_player = st.selectbox("Filter by player", ["All"]+PLAYERS, label_visibility="collapsed")
        filtered = log_df if filter_player=="All" else log_df[log_df["player"]==filter_player]
        filtered = filtered.sort_values(["player","date"], ascending=[True,False])

        display_cols = ["player","date","opponent","home_away","pitcher_hand","ab","hits","doubles","triples","hr","bb","hbp","sf","r","rbi","team_h","team_ab"]
        rename = {"player":"Player","date":"Date","opponent":"Opp","home_away":"H/A","pitcher_hand":"P-Hand",
                  "ab":"AB","hits":"H","doubles":"2B","triples":"3B","hr":"HR","bb":"BB","hbp":"HBP",
                  "sf":"SF","r":"R","rbi":"RBI","team_h":"Tm H","team_ab":"Tm AB"}
        disp_cols = [c for c in display_cols if c in filtered.columns]
        display_df = filtered[disp_cols].rename(columns=rename).copy()
        display_df["Date"] = display_df["Date"].astype(str)

        def highlight_multihit(row):
            if row.get("H",0) >= 2: return ["background-color:#1a1500;color:#c8a800"]*len(row)
            return [""]*len(row)

        st.dataframe(display_df.style.apply(highlight_multihit, axis=1), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("✏️ Edit or Delete an Entry")
        log_df_display = log_df.copy()
        log_df_display["label"] = log_df_display.apply(lambda r: f"{r['player']} — {r['date']} vs {r['opponent']} ({r['hits']}H/{r['ab']}AB)", axis=1)
        entry_label = st.selectbox("Select entry", log_df_display["label"].tolist())
        selected_idx = log_df_display[log_df_display["label"]==entry_label].index[0]
        sr = log_df.loc[selected_idx]

        with st.form("edit_form"):
            st.markdown(f"**Editing:** {sr['player']} — {sr['date']} vs {sr['opponent']}")
            ec1,ec2,ec3,ec4 = st.columns(4)
            e_opp  = ec1.text_input("Opponent", value=str(sr["opponent"]))
            e_date = ec2.date_input("Date", value=pd.to_datetime(sr["date"]).date())
            e_ha   = ec3.selectbox("Home/Away", ["Home","Away"], index=0 if str(sr.get("home_away","Home"))=="Home" else 1)
            e_ph   = ec4.selectbox("Pitcher Hand", ["R","L","—"], index=["R","L","—"].index(str(sr.get("pitcher_hand","—"))) if str(sr.get("pitcher_hand","—")) in ["R","L","—"] else 2)
            ec5,ec6,ec7,ec8,ec9 = st.columns(5)
            e_pa=ec5.number_input("PA",min_value=0,value=int(sr.get("pa",0)))
            e_ab=ec6.number_input("AB",min_value=0,value=int(sr["ab"]))
            e_h =ec7.number_input("H", min_value=0,value=int(sr["hits"]))
            e_2b=ec8.number_input("2B",min_value=0,value=int(sr.get("doubles",0)))
            e_3b=ec9.number_input("3B",min_value=0,value=int(sr.get("triples",0)))
            ec10,ec11,ec12,ec13,ec14,ec15,ec16,ec17 = st.columns(8)
            e_hr =ec10.number_input("HR", min_value=0,value=int(sr["hr"]))
            e_bb =ec11.number_input("BB", min_value=0,value=int(sr.get("bb",0)))
            e_hbp=ec12.number_input("HBP",min_value=0,value=int(sr.get("hbp",0)))
            e_sf =ec13.number_input("SF", min_value=0,value=int(sr.get("sf",0)))
            e_r  =ec14.number_input("R",  min_value=0,value=int(sr["r"]))
            e_rbi=ec15.number_input("RBI",min_value=0,value=int(sr["rbi"]))
            e_th =ec16.number_input("Tm H", min_value=0,value=int(sr.get("team_h",0)))
            e_tab=ec17.number_input("Tm AB",min_value=0,value=int(sr.get("team_ab",0)))
            sc1,sc2=st.columns(2)
            save_btn=sc1.form_submit_button("💾 Save Changes",use_container_width=True)
            del_btn =sc2.form_submit_button("🗑️ Delete Entry", use_container_width=True)
            if save_btn:
                log_df.loc[selected_idx,["date","opponent","home_away","pitcher_hand","pa","ab","hits","doubles","triples","hr","bb","hbp","sf","r","rbi","team_h","team_ab"]] = [
                    e_date,e_opp,e_ha,e_ph,e_pa,e_ab,e_h,e_2b,e_3b,e_hr,e_bb,e_hbp,e_sf,e_r,e_rbi,e_th,e_tab]
                save_log(log_df); st.success("Updated!"); st.rerun()
            if del_btn:
                log_df=log_df.drop(index=selected_idx)
                save_log(log_df); st.success("Deleted!"); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# LOG GAME TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_entry:
    st.markdown("### ➕ Log a Game")
    with st.form("log_form", clear_on_submit=True):
        lc1,lc2,lc3 = st.columns(3)
        l_player = lc1.selectbox("Player", PLAYERS)
        l_date   = lc2.date_input("Game Date", value=date.today())
        l_ha     = lc3.selectbox("Home / Away", ["Home","Away"])
        l_opp    = st.text_input("Opponent (e.g. ARI, ATL, NYM)")

        st.markdown("**Overall Stats**")
        cc1,cc2,cc3,cc4,cc5 = st.columns(5)
        l_pa  = cc1.number_input("PA", min_value=0,value=0)
        l_ab  = cc2.number_input("AB", min_value=0,value=4)
        l_h   = cc3.number_input("H",  min_value=0,value=0)
        l_2b  = cc4.number_input("2B", min_value=0,value=0)
        l_3b  = cc5.number_input("3B", min_value=0,value=0)
        cc6,cc7,cc8,cc9,cc10,cc11 = st.columns(6)
        l_hr  = cc6.number_input("HR",  min_value=0,value=0)
        l_bb  = cc7.number_input("BB",  min_value=0,value=0)
        l_hbp = cc8.number_input("HBP", min_value=0,value=0)
        l_sf  = cc9.number_input("SF",  min_value=0,value=0)
        l_r   = cc10.number_input("R",  min_value=0,value=0)
        l_rbi = cc11.number_input("RBI",min_value=0,value=0)

        st.markdown("**vs RHP**")
        rc1,rc2,rc3,rc4,rc5,rc6,rc7 = st.columns(7)
        l_pa_r  = rc1.number_input("PA",  min_value=0,value=0,key="pa_r")
        l_ab_r  = rc2.number_input("AB",  min_value=0,value=0,key="ab_r")
        l_h_r   = rc3.number_input("H",   min_value=0,value=0,key="h_r")
        l_hr_r  = rc4.number_input("HR",  min_value=0,value=0,key="hr_r")
        l_bb_r  = rc5.number_input("BB",  min_value=0,value=0,key="bb_r")
        l_hbp_r = rc6.number_input("HBP", min_value=0,value=0,key="hbp_r")
        l_sf_r  = rc7.number_input("SF",  min_value=0,value=0,key="sf_r")

        st.markdown("**vs LHP**")
        lc1b,lc2b,lc3b,lc4b,lc5b,lc6b,lc7b = st.columns(7)
        l_pa_l  = lc1b.number_input("PA",  min_value=0,value=0,key="pa_l")
        l_ab_l  = lc2b.number_input("AB",  min_value=0,value=0,key="ab_l")
        l_h_l   = lc3b.number_input("H",   min_value=0,value=0,key="h_l")
        l_hr_l  = lc4b.number_input("HR",  min_value=0,value=0,key="hr_l")
        l_bb_l  = lc5b.number_input("BB",  min_value=0,value=0,key="bb_l")
        l_hbp_l = lc6b.number_input("HBP", min_value=0,value=0,key="hbp_l")
        l_sf_l  = lc7b.number_input("SF",  min_value=0,value=0,key="sf_l")

        st.markdown("**Team Stats**")
        tc1,tc2 = st.columns(2)
        l_th  = tc1.number_input("Team Hits",   min_value=0,value=0)
        l_tab = tc2.number_input("Team At-Bats", min_value=0,value=0)

        submitted = st.form_submit_button("⚾ Save Game", use_container_width=True)
        if submitted:
            if not l_opp: st.error("Please enter an opponent!")
            elif l_h > l_ab: st.error("Hits can't exceed AB!")
            elif (l_2b+l_3b+l_hr) > l_h: st.error("XBH can't exceed total hits!")
            else:
                new_row = pd.DataFrame([{
                    "player":l_player,"date":l_date,"opponent":l_opp.upper(),"home_away":l_ha,
                    "pa":l_pa,"ab":l_ab,"hits":l_h,"doubles":l_2b,"triples":l_3b,
                    "hr":l_hr,"bb":l_bb,"hbp":l_hbp,"sf":l_sf,"r":l_r,"rbi":l_rbi,
                    "pa_vs_r":l_pa_r,"ab_vs_r":l_ab_r,"h_vs_r":l_h_r,"hr_vs_r":l_hr_r,"bb_vs_r":l_bb_r,"hbp_vs_r":l_hbp_r,"sf_vs_r":l_sf_r,
                    "pa_vs_l":l_pa_l,"ab_vs_l":l_ab_l,"h_vs_l":l_h_l,"hr_vs_l":l_hr_l,"bb_vs_l":l_bb_l,"hbp_vs_l":l_hbp_l,"sf_vs_l":l_sf_l,
                    "team_h":l_th,"team_ab":l_tab,
                }])
                log_df = pd.concat([log_df,new_row],ignore_index=True)
                save_log(log_df)
                st.success(f"✅ {l_player} — {l_date} vs {l_opp.upper()} ({l_ha}) logged!")
                st.rerun()
