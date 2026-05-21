"""Database descriptions and schema hints for THA MCP Server.

Built from live MotherDuck inventory (2026-05-21).
"""

ALL_DBS = [
    "nhl", "swe", "shl_analytics", "nor", "sui", "liiga", "met", "moneypuck", "hockey_ref",
]

TIER_PRESETS: dict[str, list[str]] = {
    "nhl":        ["nhl", "moneypuck"],
    "swe":        ["swe", "shl_analytics"],
    "nor":        ["nor"],
    "sui":        ["sui"],
    "liiga":      ["liiga"],
    "met":        ["met"],
    "nordic":     ["swe", "shl_analytics", "nor", "sui", "liiga", "met"],
    "hockey_ref": ["hockey_ref"],
    "full":       list(ALL_DBS),
    "internal":   list(ALL_DBS),
}

DB_DESCRIPTIONS: dict[str, dict] = {
    "nhl": {
        "description": (
            "NHL (National Hockey League) 2010–2025. "
            "21K games, 6.7M play-by-play events, 861K player-game lines. "
            "Rolling form windows (5/10/20 games), team Corsi/Fenwick, "
            "EDGE speed/skating metrics, standings, draft, playoff brackets."
        ),
        "key_tables": {
            "games":                  "21K games — game_date, season, home/away team abbr, scores, OT/SO, game_state, venue",
            "game_events":            "6.7M PBP events — goals, shots, faceoffs, hits, blocks, penalties, x/y coordinates",
            "player_game_stats":      "861K player-game lines — G/A/PTS, TOI, shots, hits, blocks, faceoffs, +/-, sweater",
            "player_rolling_stats":   "774K rows — 5/10/20-game rolling form per player (goals, assists, points trends)",
            "goalie_rolling_stats":   "45K rows — goalie rolling form (GAA, SVS%, starts, TOI trends)",
            "standings":              "524 team standings snapshots — PTS, W/L/OTL, ROW, L10 record, streak",
            "skater_stats":           "15K season totals per player-season (regular season + playoffs)",
            "goalie_stats":           "1,615 goalie season stat lines — GAA, SVS%, W/L, shutouts",
            "edge_skater_summary":    "15K EDGE season totals — skating speed, distance, shot speed per skater",
            "edge_skater_realtime":   "15K rows — hits, blocks, giveaways, takeaways, empty-net goals",
            "edge_skater_puck_poss":  "15K rows — zone start % (DZ/NZ/OZ), faceoff %, individual shot rates",
            "edge_skater_powerplay":  "15K rows — PP goals, PP assists, PP/60 rates",
            "edge_skater_percentages":"15K rows — SAT%, SAT% ahead/behind/close/tied",
            "edge_goalie_summary":    "1,606 goalie EDGE season totals",
            "edge_goalie_advanced":   "1,606 rows — complete game %, goals for while playing",
            "team_corsi":             "43K rows — CF, CA, CF% per game (team possession proxy)",
            "team_rolling_stats":     "39K rows — team rolling stats (goals, xG proxy, wins)",
            "team_stats":             "524 team season stat lines — faceoff%, GA/game, GF/game",
            "pbp_events":             "380K PBP events (alternative source, different schema)",
            "playoff_brackets":       "263 playoff series — seed, wins, opponent, round",
            "players":                "866 active player profiles — name, DOB, position, height, weight",
            "teams":                  "32 NHL teams — conference, division, abbreviation, franchise_id",
            "roster":                 "1,732 player-team-season roster entries",
            "draft":                  "63 draft year summaries with round structure",
            "glossary":               "321 stat abbreviation definitions",
            "game_ids":               "3,699 game ID cross-reference mappings",
            "agent_insights":         "14 AI-generated insight rows (entity trends)",
            "insights_history":       "209 historical insight records",
        },
    },

    "swe": {
        "description": (
            "Swehockey — ALL Swedish hockey leagues 2020–2025. "
            "126K games, 22.7M events. "
            "Covers SHL, HockeyAllsvenskan (HA), Hockeyettan, Hockeytvåan, "
            "women's (SDHL), junior (J20/J18), and more. "
            "Filter by 'league' or 'league_id' columns."
        ),
        "key_tables": {
            "games":               "126K games — game_date, season ('2024'), league, league_id, home/away team, result, venue",
            "game_events":         "22.7M events — goals, penalties, shots, faceoffs per game across ALL leagues",
            "game_goals":          "22K goals — scorer, assist1, assist2, period, event_time, goal_type (PP/EQ/SH)",
            "game_penalties":      "21K penalties — player, team_abbr, minutes, period, event_time, penalty type",
            "game_lineups":        "4.3M lineup entries — player name/number, team, game (great for career appearance data)",
            "game_period_scores":  "259K period scores — home/away score per period",
            "game_player_stats":   "33K detailed box-score lines (subset of games with full individual stats)",
            "game_goalie_stats":   "1,978 goalie game lines — saves, GA, SVS%, TOI",
            "game_starting_lineup":"179K starting lineup entries per game",
            "game_winners":        "2.1M records — winning/losing team, score, season per game (broadest coverage)",
            "game_on_ice_json":    "1.3M on-ice events — event_team, side, event_type with player context",
            "game_period_stats":   "7,842 team-period stat rows (goals, shots, saves per period)",
            "game_goalkeepers":    "280K goalkeeper-game rows — saves, game_date, season, league",
            "game_referees_json":  "346K referee assignments — name, role, game",
            "game_spectators":     "2,705 games with spectator (attendance) counts",
        },
    },

    "shl_analytics": {
        "description": (
            "SHL.se official analytics — Swedish Hockey League ONLY. "
            "Detailed per-game stats: TOI, hits, face-offs, shot attempts, blocked shots. "
            "Currently ~2 seasons of data (backfill to 1975/76 in progress). "
            "Two schemas: 'raw' (direct from SHL.se API) and 'analytics' (cleaned facts/dims). "
            "Swedish column names (e.g. 'spelare'=player, 'lag'=team, 'mal'=goals)."
        ),
        "key_tables": {
            "raw.players_per_game":    "49K player-game rows — TOI, G, A, hits, face-off W/L, shots, blocked shots, +/-",
            "raw.goalies_per_game":    "4,966 goalie-game rows — saves, GA, SVS%, TOI, shots against",
            "raw.teams_per_game":      "2,476 team-game rows — SOG, PP attempts/goals, PK, hits, blocked shots",
            "raw.player_totals":       "2K season totals per player — G/A/PTS, GP, avg TOI, hits total",
            "analytics.fact_player_game": "1,761 cleaned/normalized player-game rows",
            "analytics.fact_team_game":   "88 team-game fact rows (summary level)",
            "analytics.dim_standings":    "10 standing dimension rows (latest season)",
        },
    },

    "nor": {
        "description": (
            "Norwegian hockey — GET-ligaen / Fjordkraft-ligaen. "
            "Rich shift-level data (1.9M shifts with timestamps), "
            "momentum tracking (6.5M data points), full play-by-play. "
            "Multiple team_slug entries per team (team identifier in this DB)."
        ),
        "key_tables": {
            "matches":             "2,664 games — match_date, home/away team, final score, status",
            "shifts":              "1.9M individual player shifts — start/end timestamps, period, player_id (TOI derivable)",
            "goal_events":         "15K goals — scorer, assist, period, match_time, team",
            "penalty_events":      "19K penalties — player, period, match_time, penalty duration",
            "match_lineup":        "111K lineup entries — player_id, first/last name, jersey, role (forward/defense/goalie)",
            "match_period_stats":  "25K period stats — shots, goals per period per team (home/away)",
            "match_powerplay_stats":"4,968 PP summary rows — powerplay_count, PP goals, PP time seconds",
            "skater_summaries":    "3,144 player season summaries — G/A/PTS, PIM, +/-, penalty_count",
            "players":             "824 player profiles — height, weight, handedness, birth_date",
            "momentum":            "6.5M momentum data points — value per timestamp per match (unique granularity)",
            "tournaments":         "112 tournament/season definitions — name, phase, year, league",
        },
    },

    "sui": {
        "description": (
            "Swiss National League (NL) and other Swiss leagues 2023–2025. "
            "Full player game stats with TOI, hits, shot attempts, faceoffs. "
            "League identifier in 'league_id' / 'league_name' columns."
        ),
        "key_tables": {
            "games":            "3,212 games — season, league_id, start_dt, home/away team, scores, venue",
            "game_player_stats":"101K player-game rows — TOI, G, A, shots, hits, blocks, faceoffs, +/-",
            "game_goals":       "21K goals — scorer, assists, period, time_in_period, strength (PP/EQ/SH)",
            "game_penalties":   "23K penalties — player, team, duration seconds, period, start/end time",
            "game_team_stats":  "6,424 team-game rows — SOG, PP stats, faceoff %, PIM, hits",
            "game_goalie_stats":"11K goalie-game rows — saves, GA, SVS%, TOI, shots against",
        },
    },

    "liiga": {
        "description": (
            "Finnish Liiga (SM-liiga, top hockey league) 2003–2025. "
            "22 seasons of game results and goal events with scorer/assist detail. "
            "Goal type codes: YV=PP, AV=EV, VT=SH, RL=empty-net, JA=SO."
        ),
        "key_tables": {
            "games":       "11K games — season (year), serie (runkosarja/playoffs), home/away team, scores, game_id",
            "goal_events": "60K goals — scorer_name, scorer_player_id, assist1/2, period, time, team_side, goal_type",
            "standings":   "943 season standings rows — team_name, W/OW/OL/L, GF/GA, PTS per season",
        },
    },

    "met": {
        "description": (
            "Danish Metal Ligaen — player/team stats from icehockey24.com and metalligaen.dk. "
            "Multiple seasons of results, standings and player performance. "
            "All values are strings (scraped directly from web)."
        ),
        "key_tables": {
            "ih24_results":   "2,861 game results — date, round, home/away team, score, match_url",
            "ih24_standings": "252 standings entries — team, GP, W, L, OT wins/losses, PTS, season",
            "ep_player_stats":"1,875 player stats (Elite Prospects) — G, A, PTS, PIM, league, season",
            "ep_goalie_stats":"879 goalie stat rows — GAA, SVS%, GP, W, league, season",
            "ml_player_stats":"200 rows — Metalligaen.dk player stats (navn=name, hold=team)",
            "ml_goalie_stats":"158 rows — Metalligaen.dk goalie stats",
        },
    },

    "moneypuck": {
        "description": (
            "MoneyPuck NHL advanced analytics 2009–2024. "
            "Expected goals (xG), Corsi/Fenwick, shot coordinates with arena adjustments. "
            "All skater/goalie/team/line stats split by situation: "
            "'all', '5on5', 'powerPlay', 'penaltyKill', '4on5', 'other'. "
            "Largest table: skater_summaries with 150+ metrics per row."
        ),
        "key_tables": {
            "shots":             "786K shots — xGoal, arenaAdjusted x/y coordinates, shot type, distance, "
                                 "shooter/goalie/blocker IDs, game context (score state, manpower)",
            "skater_summaries":  "94K rows — 150 metrics per skater-season-situation: "
                                 "xGoalsFor/Against, CF, FF, TOI, on-ice xG%, individual xG, "
                                 "rush%, rebound%, zone entries/exits",
            "team_summaries":    "3,550 rows — xGoalsPercentage, corsiPercentage, fenwickPercentage "
                                 "per team-season-situation",
            "line_summaries":    "149K line combination rows — xG and shot metrics per line-season-situation",
            "goalie_summaries":  "9,185 rows — xGoalsAgainst, GSAx (goals saved above expected), "
                                 "SVS%, low/medium/high danger saves",
        },
    },

    "hockey_ref": {
        "description": (
            "Hockey Reference player data + IIHF international tournament results + Puckpedia salary data. "
            "Smaller reference dataset — useful for cross-league career data and international results."
        ),
        "key_tables": {
            "iihf_games":     "8,775 IIHF international games — Worlds, Olympics, U-20, U-18, Women's (1920→2024)",
            "iihf_tournaments":"835 IIHF tournament definitions — comp_id, title, year, game_count",
            "pp_contracts":   "32 NHL salary contracts — cap_hit, AAV, base_salary, signing_bonus, performance_bonus",
            "pp_players":     "5 player profiles with salary history (from Puckpedia)",
            "pp_seasons":     "124 player-season stat lines for salary-tracked players",
            "hr_players":     "3 player profiles from Hockey Reference",
            "hr_seasons":     "7 player-season career stat lines",
        },
    },
}

SQL_HINTS = """
## DuckDB SQL Quick Reference

### Table qualification (always required for cross-db)
  nhl.main.games              — database.schema.table
  shl_analytics.raw.players_per_game  — non-main schema
  swe.main.game_goals         — standard

### Useful DuckDB functions
  DATE_TRUNC('month', game_date)
  STRPTIME(date_str, '%Y-%m-%d')
  EPOCH(timestamp)
  LIST_AGG(col, ', ')
  PIVOT / UNPIVOT
  UNNEST(list_col)

### Season formats (vary by source)
  nhl:          20242025  (INTEGER, e.g. 20242025 = 2024-25 season)
  swe/nor/liiga: '2024'   (VARCHAR, last year of season)
  shl_analytics: '2024-25' (VARCHAR)
  moneypuck:    '2024'    (VARCHAR)
  sui:          '2024/2025' or '2024-25'

### Cross-database JOINs
  -- NHL player stats + MoneyPuck xG
  SELECT p.lastName, s.goals, m.I_F_xGoals
  FROM nhl.main.skater_stats s
  JOIN nhl.main.players p ON p.id = s.playerId
  JOIN moneypuck.main.skater_summaries m
    ON m.playerId = CAST(p.id AS VARCHAR)
    AND m.season = '2024' AND m.situation = '5on5'
  WHERE s.season = 20242025

### SHL analytics — Swedish column names
  spelare = player name
  lag = team
  mal = goals
  assist = assists
  poang = points
  matcher = games played
  hemma_borta = home/away
"""
