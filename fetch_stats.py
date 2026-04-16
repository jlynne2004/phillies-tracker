"""
fetch_stats.py
──────────────────────────────────────────────────────────────────────────────
Automatically fetches game-by-game stats for the Phillies core 4 from
Baseball Savant (via pybaseball) and updates data/game_log.csv.

Usage:
    # Fetch from season start to today:
    python fetch_stats.py

    # Fetch a specific date range:
    python fetch_stats.py --start 2026-04-01 --end 2026-04-15

    # Fetch only one player:
    python fetch_stats.py --player "Bryce Harper"

    # Dry run (print without saving):
    python fetch_stats.py --dry-run

Requirements:
    pip install pybaseball pandas
"""

import argparse
import os
import warnings
from datetime import date, datetime

import pandas as pd
from pybaseball import statcast_batter

warnings.filterwarnings("ignore")

# ── CONFIG ───────────────────────────────────────────────────────────────────
PLAYERS = {
    "Bryce Harper":   547180,
    "Kyle Schwarber": 656941,
    "Trea Turner":    607208,
    "J.T. Realmuto":  592663,
}

SEASON_START = "2026-03-26"
LOG_PATH     = "data/game_log.csv"

LOG_COLS = [
    "player","date","opponent","home_away",
    "pa","ab","hits","doubles","triples","hr","bb","hbp","sf","r","rbi",
    "pa_vs_r","ab_vs_r","h_vs_r","hr_vs_r","bb_vs_r","hbp_vs_r","sf_vs_r",
    "pa_vs_l","ab_vs_l","h_vs_l","hr_vs_l","bb_vs_l","hbp_vs_l","sf_vs_l",
    "team_h","team_ab",
]


# ── DATA HELPERS ──────────────────────────────────────────────────────────────
def load_existing():
    if os.path.exists(LOG_PATH):
        df = pd.read_csv(LOG_PATH)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        for col in LOG_COLS:
            if col not in df.columns:
                df[col] = 0 if col not in ["home_away","opponent","player","date"] else ""
        return df
    return pd.DataFrame(columns=LOG_COLS)


def save_log(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(LOG_PATH, index=False)
    print(f"✅ Saved {len(df)} rows to {LOG_PATH}")


# ── STAT HELPERS ──────────────────────────────────────────────────────────────
def hand_stats(hand_df):
    """Aggregate counting stats for a subset of PA rows (filtered by pitcher hand)."""
    if hand_df.empty:
        return {"pa":0,"ab":0,"h":0,"hr":0,"bb":0,"hbp":0,"sf":0}
    ev    = hand_df["events"].str.lower()
    h_bb  = int((ev == "walk").sum())
    h_hbp = int((ev == "hit_by_pitch").sum())
    h_sf  = int((ev == "sac_fly").sum())
    h_sb  = int((ev == "sac_bunt").sum())
    h_pa  = len(hand_df)
    h_ab  = h_pa - h_bb - h_hbp - h_sf - h_sb
    h_h   = int((ev.isin(["single","double","triple","home_run"])).sum())
    h_hr  = int((ev == "home_run").sum())
    return {"pa":h_pa,"ab":h_ab,"h":h_h,"hr":h_hr,"bb":h_bb,"hbp":h_hbp,"sf":h_sf}


# ── FETCH FUNCTIONS ───────────────────────────────────────────────────────────
def fetch_player(name, player_id, start_date, end_date):
    """
    Fetch all Statcast plate appearances for a player in the date range,
    then aggregate to one row per game with full vs R / vs L splits.
    """
    print(f"  Fetching {name} ({start_date} → {end_date})...")
    raw = statcast_batter(start_date, end_date, player_id=player_id)

    if raw.empty:
        print(f"    ⚠️  No data returned for {name}")
        return pd.DataFrame()

    raw["game_date"] = pd.to_datetime(raw["game_date"]).dt.date

    rows = []
    for game_date, gdf in raw.groupby("game_date"):
        # Only rows with a completed plate appearance
        pa_df = gdf[gdf["events"].notna()].copy()
        if pa_df.empty:
            continue

        # Home/Away
        home_team = pa_df["home_team"].iloc[0] if "home_team" in pa_df.columns else ""
        home_away = "Home" if str(home_team).upper() == "PHI" else "Away"

        # Opponent
        if home_away == "Home":
            opponent = str(pa_df["away_team"].iloc[0]).upper() if "away_team" in pa_df.columns else "—"
        else:
            opponent = str(pa_df["home_team"].iloc[0]).upper() if "home_team" in pa_df.columns else "—"

        # ── Overall counting stats ────────────────────────────────────────────
        events   = pa_df["events"].str.lower()
        pa       = len(pa_df)
        bb       = int((events == "walk").sum())
        hbp      = int((events == "hit_by_pitch").sum())
        sf       = int((events == "sac_fly").sum())
        sac_bunt = int((events == "sac_bunt").sum())
        ab       = pa - bb - hbp - sf - sac_bunt
        hits     = int((events.isin(["single","double","triple","home_run"])).sum())
        doubles  = int((events == "double").sum())
        triples  = int((events == "triple").sum())
        hr       = int((events == "home_run").sum())

        # Runs scored
        r = 0
        if "post_bat_score" in pa_df.columns and "bat_score" in pa_df.columns:
            pa_df["runs_this_pa"] = (
                pd.to_numeric(pa_df["post_bat_score"], errors="coerce") -
                pd.to_numeric(pa_df["bat_score"], errors="coerce")
            )
            r = int(pa_df["runs_this_pa"].clip(lower=0).sum())

        # RBI from Statcast batted_rbi field
        rbi = 0
        if "batted_rbi" in pa_df.columns:
            rbi = int(pd.to_numeric(pa_df["batted_rbi"], errors="coerce").fillna(0).sum())

        # ── Per-pitcher-hand splits ───────────────────────────────────────────
        if "p_throws" in pa_df.columns:
            vs_r = hand_stats(pa_df[pa_df["p_throws"] == "R"].copy())
            vs_l = hand_stats(pa_df[pa_df["p_throws"] == "L"].copy())
        else:
            vs_r = hand_stats(pd.DataFrame())
            vs_l = hand_stats(pd.DataFrame())

        rows.append({
            "player":     name,
            "date":       game_date,
            "opponent":   opponent,
            "home_away":  home_away,
            "pa":         pa,
            "ab":         ab,
            "hits":       hits,
            "doubles":    doubles,
            "triples":    triples,
            "hr":         hr,
            "bb":         bb,
            "hbp":        hbp,
            "sf":         sf,
            "r":          r,
            "rbi":        rbi,
            "pa_vs_r":    vs_r["pa"],  "ab_vs_r":   vs_r["ab"],  "h_vs_r":   vs_r["h"],
            "hr_vs_r":    vs_r["hr"],  "bb_vs_r":   vs_r["bb"],  "hbp_vs_r": vs_r["hbp"], "sf_vs_r": vs_r["sf"],
            "pa_vs_l":    vs_l["pa"],  "ab_vs_l":   vs_l["ab"],  "h_vs_l":   vs_l["h"],
            "hr_vs_l":    vs_l["hr"],  "bb_vs_l":   vs_l["bb"],  "hbp_vs_l": vs_l["hbp"], "sf_vs_l": vs_l["sf"],
            "team_h":     0,
            "team_ab":    0,
        })

    result = pd.DataFrame(rows)
    print(f"    ✅ {len(result)} games found for {name}")
    return result


def fetch_team_stats(start_date, end_date):
    """
    Fetch Phillies team H and AB per game from the MLB Stats API.
    Returns a dict: {game_date: {"team_h": int, "team_ab": int}}
    """
    print("  Fetching Phillies team stats from MLB Stats API...")
    try:
        import urllib.request
        import json
        team_rows = {}
        url = (
            f"https://statsapi.mlb.com/api/v1/schedule"
            f"?teamId=143&startDate={start_date}&endDate={end_date}&sportId=1&hydrate=boxscore"
        )
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        for date_entry in data.get("dates", []):
            for game in date_entry.get("games", []):
                gdate = datetime.strptime(date_entry["date"], "%Y-%m-%d").date()
                bs = game.get("teams", {})
                home_id = bs.get("home", {}).get("team", {}).get("id", 0)
                away_id = bs.get("away", {}).get("team", {}).get("id", 0)
                if home_id == 143:
                    phi_side = bs.get("home", {})
                elif away_id == 143:
                    phi_side = bs.get("away", {})
                else:
                    continue
                batting = phi_side.get("teamStats", {}).get("batting", {})
                team_rows[gdate] = {
                    "team_h":  batting.get("hits", 0),
                    "team_ab": batting.get("atBats", 0),
                }
        print(f"    ✅ Team stats fetched for {len(team_rows)} games")
        return team_rows
    except Exception as e:
        print(f"    ⚠️  Could not fetch team stats: {e}")
        return {}


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fetch Phillies core 4 stats from Baseball Savant")
    parser.add_argument("--start",   default=SEASON_START,    help="Start date YYYY-MM-DD")
    parser.add_argument("--end",     default=str(date.today()), help="End date YYYY-MM-DD")
    parser.add_argument("--player",  default=None,            help="Single player name to fetch")
    parser.add_argument("--dry-run", action="store_true",     help="Print without saving")
    args = parser.parse_args()

    print(f"\n🔴⚾ Phillies $85M Tracker — Fetching stats {args.start} → {args.end}\n")

    # Load existing log
    existing = load_existing()
    existing_keys = set(zip(existing["player"], existing["date"])) if not existing.empty else set()

    # Which players to fetch
    players_to_fetch = {k: v for k, v in PLAYERS.items() if args.player is None or k == args.player}
    if not players_to_fetch:
        print(f"❌ Player '{args.player}' not found. Options: {list(PLAYERS.keys())}")
        return

    # Fetch player stats
    new_rows = []
    for name, pid in players_to_fetch.items():
        player_df = fetch_player(name, pid, args.start, args.end)
        if not player_df.empty:
            for _, row in player_df.iterrows():
                key = (row["player"], row["date"])
                if key not in existing_keys:
                    new_rows.append(row)
                else:
                    print(f"    ⏭️  Skipping {name} {row['date']} (already logged)")

    if not new_rows:
        print("\n✅ No new games to add — already up to date!")
        return

    new_df = pd.DataFrame(new_rows)

    # Fetch and merge team stats
    print()
    team_stats = fetch_team_stats(args.start, args.end)
    if team_stats:
        def fill_team_stats(row):
            if row["player"] == "Bryce Harper":
                ts = team_stats.get(row["date"], {})
                row["team_h"]  = ts.get("team_h",  0)
                row["team_ab"] = ts.get("team_ab", 0)
            return row
        new_df = new_df.apply(fill_team_stats, axis=1)

    # Combine with existing and sort
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.sort_values(["date","player"]).reset_index(drop=True)
    for col in LOG_COLS:
        if col not in combined.columns:
            combined[col] = 0
    combined = combined[LOG_COLS]

    # Summary
    print(f"\n📊 Summary:")
    print(f"   Existing rows : {len(existing)}")
    print(f"   New rows added: {len(new_df)}")
    print(f"   Total rows    : {len(combined)}")
    print()
    print(new_df[["player","date","opponent","home_away","ab","hits","hr","bb","r","rbi","ab_vs_r","h_vs_r","ab_vs_l","h_vs_l"]].to_string(index=False))
    print()
    print("⚠️  Note: RBI uses Statcast 'batted_rbi' field. Cross-check with baseball-reference.com")
    print("   and edit via the Game Log tab or data/game_log.csv if needed.")

    if args.dry_run:
        print("\n🔍 Dry run — nothing saved.")
    else:
        save_log(combined)
        print(f"\n🎉 Done! Upload data/game_log.csv to GitHub to update the live app.")


if __name__ == "__main__":
    main()
