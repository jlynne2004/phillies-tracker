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
    "Bryce Harper":    547180,
    "Kyle Schwarber":  656941,
    "Trea Turner":     607208,
    "J.T. Realmuto":   592663,
}

SEASON_START = "2026-03-26"
LOG_PATH     = "data/game_log.csv"

LOG_COLS = [
    "player","date","opponent","home_away",
    "pa","ab","hits","doubles","triples","hr","bb","hbp","sf","r","rbi",
    "pa_vs_r","ab_vs_r","h_vs_r","hr_vs_r","bb_vs_r","hbp_vs_r","sf_vs_r",
    "pa_vs_l","ab_vs_l","h_vs_l","hr_vs_l","bb_vs_l","hbp_vs_l","sf_vs_l",
    "team_h","team_ab"
]
# ── HELPERS ──────────────────────────────────────────────────────────────────
def load_existing():
    if os.path.exists(LOG_PATH):
        df = pd.read_csv(LOG_PATH)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        # Add any missing columns with defaults
        for col in LOG_COLS:
            if col not in df.columns:
                df[col] = 0 if col not in ["home_away","opponent","player","date"] else ""
        return df
    return pd.DataFrame(columns=LOG_COLS)


def save_log(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(LOG_PATH, index=False)
    print(f"✅ Saved {len(df)} rows to {LOG_PATH}")


def summarize_pitcher_hand(hands):
    """
    Given a list of pitcher hands faced in a game (e.g. ['R','R','L','R']),
    return a summary string:
      - 'R'   if all righties
      - 'L'   if all lefties
      - 'R/L' if mixed (bullpen games, openers, etc.)
    """
    unique = set(h for h in hands if pd.notna(h) and h in ["R","L"])
    if not unique:       return "—"
    if unique == {"R"}:  return "R"
    if unique == {"L"}:  return "L"
    return "R/L"


def fetch_player(name, player_id, start_date, end_date):
    """
    Fetch all Statcast plate appearances for a player in the date range,
    then aggregate to one row per game.
    """
    print(f"  Fetching {name} ({start_date} → {end_date})...")
    raw = statcast_batter(start_date, end_date, player_id=player_id)

    if raw.empty:
        print(f"    ⚠️  No data returned for {name}")
        return pd.DataFrame()

    # ── Relevant Statcast columns ────────────────────────────────────────────
    # game_date       — date of game
    # home_team       — home team abbreviation
    # away_team       — away team abbreviation
    # inning_topbot   — "Top" or "Bot"
    # p_throws        — pitcher hand: "R" or "L"
    # events          — plate appearance result (single, home_run, walk, etc.)
    # bb_type         — batted ball type
    # hit_distance_sc — hit distance
    # estimated_woba_using_speedangle
    # on_3b, on_2b, on_1b — runners on base

    raw["game_date"] = pd.to_datetime(raw["game_date"]).dt.date

    rows = []
    for game_date, gdf in raw.groupby("game_date"):
        # Only keep rows with a plate appearance result
        pa_df = gdf[gdf["events"].notna()].copy()
        if pa_df.empty:
            continue

        # Determine home/away — Phillies are PHI
        # If home_team == "PHI" → Home, else Away
        home_team = pa_df["home_team"].iloc[0] if "home_team" in pa_df.columns else ""
        home_away = "Home" if str(home_team).upper() == "PHI" else "Away"

        # Opponent
        if home_away == "Home":
            opponent = str(pa_df["away_team"].iloc[0]).upper() if "away_team" in pa_df.columns else "—"
        else:
            opponent = str(pa_df["home_team"].iloc[0]).upper() if "home_team" in pa_df.columns else "—"

        # ── Per-pitcher-hand splits ──────────────────────────────────────────
        def hand_stats(hand_df):
            if hand_df.empty:
                return {"pa":0,"ab":0,"h":0,"hr":0,"bb":0,"hbp":0,"sf":0}
            ev = hand_df["events"].str.lower()
            h_bb  = int((ev == "walk").sum())
            h_hbp = int((ev == "hit_by_pitch").sum())
            h_sf  = int((ev == "sac_fly").sum())
            h_sb  = int((ev == "sac_bunt").sum())
            h_pa  = len(hand_df)
            h_ab  = h_pa - h_bb - h_hbp - h_sf - h_sb
            h_h   = int((ev.isin(["single","double","triple","home_run"])).sum())
            h_hr  = int((ev == "home_run").sum())
            return {"pa":h_pa,"ab":h_ab,"h":h_h,"hr":h_hr,"bb":h_bb,"hbp":h_hbp,"sf":h_sf}

        r_df = pa_df[pa_df["p_throws"] == "R"] if "p_throws" in pa_df.columns else pd.DataFrame()
        l_df = pa_df[pa_df["p_throws"] == "L"] if "p_throws" in pa_df.columns else pd.DataFrame()
        vs_r = hand_stats(r_df)
        vs_l = hand_stats(l_df)

        rows.append({
            "player":    name,
            "date":      game_date,
            "opponent":  opponent,
            "home_away": home_away,
            "pa":        pa,
            "ab":        ab,
            "hits":      hits,
            "doubles":   doubles,
            "triples":   triples,
            "hr":        hr,
            "bb":        bb,
            "hbp":       hbp,
            "sf":        sf,
            "r":         r,
            "rbi":       rbi,
            "pa_vs_r":   vs_r["pa"],  "ab_vs_r":  vs_r["ab"],  "h_vs_r":  vs_r["h"],
            "hr_vs_r":   vs_r["hr"],  "bb_vs_r":  vs_r["bb"],  "hbp_vs_r":vs_r["hbp"], "sf_vs_r": vs_r["sf"],
            "pa_vs_l":   vs_l["pa"],  "ab_vs_l":  vs_l["ab"],  "h_vs_l":  vs_l["h"],
            "hr_vs_l":   vs_l["hr"],  "bb_vs_l":  vs_l["bb"],  "hbp_vs_l":vs_l["hbp"], "sf_vs_l": vs_l["sf"],
            "team_h":    0,
            "team_ab":   0,
        })

    result = pd.DataFrame(rows)
    print(f"    ✅ {len(result)} games found for {name}")
    return result


def fetch_rbi_from_bref(start_date, end_date):
    """
    Fetch per-player RBI totals from Baseball Reference via batting_stats_range.
    Returns a dict: {(player_name, game_date): rbi}
    Note: batting_stats_range returns CUMULATIVE stats for the date range,
    so we fetch day-by-day to get per-game RBI.
    For efficiency we fetch the full range and use it as a cross-check/fill.
    """
    print("  Fetching RBI from Baseball Reference...")
    try:
        from pybaseball import batting_stats_range
        df = batting_stats_range(start_date, end_date)
        if df.empty:
            print("    ⚠️  No RBI data from bref")
            return {}
        # batting_stats_range returns season totals per player for the range
        # columns include: Name, RBI, and others
        rbi_map = {}
        name_map = {
            "Bryce Harper":   ["Bryce Harper"],
            "Kyle Schwarber": ["Kyle Schwarber"],
            "Trea Turner":    ["Trea Turner"],
            "J.T. Realmuto":  ["J.T. Realmuto", "JT Realmuto"],
        }
        for player, aliases in name_map.items():
            row = df[df["Name"].isin(aliases)]
            if not row.empty:
                rbi_map[player] = int(row["RBI"].iloc[0])
                print(f"    {player}: {rbi_map[player]} RBI (range total)")
        return rbi_map
    except Exception as e:
        print(f"    ⚠️  Could not fetch RBI from bref: {e}")
        return {}
    """
    Fetch team H and AB per game from the Phillies' team batting.
    Uses Harper as the proxy — every game Harper plays = a Phillies game.
    Team stats come from the full boxscore via MLB API (fallback: leave as 0).
    """
    print("  Fetching Phillies team stats...")
    try:
        from pybaseball import team_batting_bref
        # team_batting_bref gives season totals, not per-game — not useful here
        # For per-game team stats, use MLB Stats API directly
        import urllib.request, json
        team_rows = {}
        # Get schedule for PHI in date range
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end   = datetime.strptime(end_date,   "%Y-%m-%d")
        url = f"https://statsapi.mlb.com/api/v1/schedule?teamId=143&startDate={start_date}&endDate={end_date}&sportId=1&hydrate=boxscore"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        for date_entry in data.get("dates", []):
            for game in date_entry.get("games", []):
                gdate = date_entry["date"]
                gdate_obj = datetime.strptime(gdate, "%Y-%m-%d").date()
                bs = game.get("teams", {})
                # Figure out which side is PHI
                home_id = bs.get("home", {}).get("team", {}).get("id", 0)
                away_id = bs.get("away", {}).get("team", {}).get("id", 0)
                if home_id == 143:
                    phi_side = bs.get("home", {})
                elif away_id == 143:
                    phi_side = bs.get("away", {})
                else:
                    continue
                batting = phi_side.get("teamStats", {}).get("batting", {})
                team_rows[gdate_obj] = {
                    "team_h":  batting.get("hits", 0),
                    "team_ab": batting.get("atBats", 0),
                }
        print(f"    ✅ Team stats fetched for {len(team_rows)} games")
        return team_rows
    except Exception as e:
        print(f"    ⚠️  Could not fetch team stats: {e}")
        return {}


# ── MAIN ─────────────────────────────────────────────────────────────────────
def fetch_team_stats(start_date, end_date):
    """
    Fetch Phillies team H and AB per game from the MLB Stats API.
    Returns a dict: {game_date: {"team_h": int, "team_ab": int}}
    """
    print("  Fetching Phillies team stats from MLB API...")
    try:
        import urllib.request, json
        team_rows = {}
        url = f"https://statsapi.mlb.com/api/v1/schedule?teamId=143&startDate={start_date}&endDate={end_date}&sportId=1&hydrate=boxscore"
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


def main():
    parser = argparse.ArgumentParser(description="Fetch Phillies core 4 stats from Baseball Savant")
    parser.add_argument("--start",  default=SEASON_START, help="Start date YYYY-MM-DD")
    parser.add_argument("--end",    default=str(date.today()), help="End date YYYY-MM-DD")
    parser.add_argument("--player", default=None, help="Single player name to fetch")
    parser.add_argument("--dry-run", action="store_true", help="Print without saving")
    args = parser.parse_args()

    print(f"\n🔴⚾ Phillies $85M Tracker — Fetching stats {args.start} → {args.end}\n")

    # Load existing log
    existing = load_existing()
    existing_keys = set(zip(existing["player"], existing["date"])) if not existing.empty else set()

    # Determine which players to fetch
    players_to_fetch = {k: v for k, v in PLAYERS.items() if args.player is None or k == args.player}

    if not players_to_fetch:
        print(f"❌ Player '{args.player}' not found. Options: {list(PLAYERS.keys())}")
        return

    # Fetch player stats
    new_rows = []
    for name, pid in players_to_fetch.items():
        player_df = fetch_player(name, pid, args.start, args.end)
        if not player_df.empty:
            # Skip rows we already have
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

    # Fetch team stats and merge in
    print()
    team_stats = fetch_team_stats(args.start, args.end)
    if team_stats:
        def fill_team_stats(row):
            ts = team_stats.get(row["date"], {})
            # Only fill team stats on Harper's row (first player alphabetically per game)
            if row["player"] == "Bryce Harper":
                row["team_h"]  = ts.get("team_h",  0)
                row["team_ab"] = ts.get("team_ab", 0)
            return row
        new_df = new_df.apply(fill_team_stats, axis=1)

    # Combine with existing
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.sort_values(["date","player"]).reset_index(drop=True)

    # Ensure all columns exist
    for col in LOG_COLS:
        if col not in combined.columns:
            combined[col] = 0

    combined = combined[LOG_COLS]

    print(f"\n📊 Summary:")
    print(f"   Existing rows : {len(existing)}")
    print(f"   New rows added: {len(new_df)}")
    print(f"   Total rows    : {len(combined)}")
    print()
    print(new_df[["player","date","opponent","home_away","pitcher_hand","ab","hits","hr","bb","r","rbi"]].to_string(index=False))
    print()
    print("⚠️  Note: RBI values come from Statcast 'batted_rbi' field where available.")
    print("   If RBI looks off, cross-check with baseball-reference.com and edit via")
    print("   the Game Log tab in the app, or edit data/game_log.csv directly.")

    if args.dry_run:
        print("\n🔍 Dry run — nothing saved.")
    else:
        save_log(combined)
        print(f"\n🎉 Done! Upload data/game_log.csv to GitHub to update the live app.")


if __name__ == "__main__":
    main()
