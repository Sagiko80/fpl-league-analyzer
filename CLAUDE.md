# CLAUDE.md - FPL League Analyzer

## Project Overview
This is an **FPL (Fantasy Premier League) League Analyzer** - a comprehensive Python tool that collects data from the official FPL API and generates detailed weekly summaries for your WhatsApp group.

## Key Commands

### Quick Start (הכי חשוב!)
```bash
# Install dependencies
pip install -r requirements.txt

# Setup config (first time only)
python src/fpl_weekly_summary.py --setup

# Run weekly summary
./run_summary.sh 922765
```

### Individual Commands
```bash
# 1. Collect data from FPL API
python src/fpl_data_collector.py 922765

# 2. Generate & send weekly summary
python src/fpl_weekly_summary.py

# Without WhatsApp (just save to file)
python src/fpl_weekly_summary.py --no-whatsapp
```

### Legacy Scripts (optional)
```bash
python src/analyze_data.py           # Basic analysis
python src/weekly_report.py          # Detailed report
python src/whatsapp_summary.py       # Old WhatsApp summary
python src/gold_mine_analysis.py     # Advanced analytics
python src/transfer_recommendations.py
python src/captain_selector.py
```

## Project Architecture

```
fpl-league-analyzer/
├── src/                          # Main Python scripts
│   ├── fpl_data_collector.py     # Data collection from FPL API
│   ├── analyze_data.py           # Basic analysis
│   ├── weekly_report.py          # Detailed weekly report
│   ├── whatsapp_summary.py       # Hebrew summary for sharing
│   ├── gold_mine_analysis.py     # Advanced analytics
│   ├── captain_selector.py       # Captain selection helper
│   └── transfer_recommendations.py # Transfer suggestions
├── scripts/                      # Shell scripts
│   ├── run_all.sh               # Linux/Mac runner
│   └── run_all.bat              # Windows runner
├── fpl_data/                     # Output directory (auto-created)
│   ├── reports/                  # Generated reports
│   └── *.json                    # Collected data files
├── docs/                         # Documentation
│   ├── QUICKSTART.md            # Quick start guide
│   ├── USAGE_GUIDE.md           # Detailed usage guide
│   └── WEEKLY_REPORT_GUIDE.md   # Weekly report guide
├── requirements.txt              # Python dependencies
├── CLAUDE.md                     # This file
└── README.md                     # Main documentation
```

## How to Find Your League ID

1. Go to https://fantasy.premierleague.com
2. Navigate to your league page
3. Look at the URL: `https://fantasy.premierleague.com/leagues/922765/standings/c`
4. The number (922765) is your League ID

## Data Files Generated

After running `fpl_data_collector.py`, these files are created in `fpl_data/`:

| File | Description |
|------|-------------|
| `bootstrap_data_YYYY-MM-DD.json` | Global FPL data (all players, teams, gameweeks) |
| `league_XXXXX_YYYY-MM-DD.json` | Your league standings |
| `live_gwXX_YYYY-MM-DD.json` | Current gameweek live data |
| `managers_detailed_YYYY-MM-DD.json` | Detailed data for each manager |
| `summary_YYYY-MM-DD.json` | Collection summary |

## Key Classes and Functions

### FPLDataCollector (`src/fpl_data_collector.py`)
- `get_bootstrap_data()` - Fetch global FPL data
- `get_league_standings()` - Fetch private league standings
- `get_manager_history(manager_id)` - Fetch manager's full history
- `get_manager_gameweek_picks(manager_id, gw)` - Fetch picks for specific GW
- `get_gameweek_live_data(gw)` - Fetch live GW data
- `collect_all_data()` - Main collection function

### WeeklyLeagueReport (`src/weekly_report.py`)
- `analyze_manager_week()` - Analyze a manager's performance
- `calculate_manager_score()` - Score 1-10 for each manager
- `generate_weekly_report()` - Generate full text + JSON report
- `generate_compact_summary()` - Short summary with scores

### FPLAdvancedAnalytics (`src/gold_mine_analysis.py`)
- `find_differentials()` - Find players owned by few managers
- `analyze_momentum()` - Track who's rising/falling in rank
- `find_template_team()` - Find most-owned players
- `analyze_budget_management()` - Analyze team values
- `analyze_consistency()` - Identify consistent vs explosive managers

### WhatsAppSummary (`src/whatsapp_summary.py`)
- `generate_summary()` - Generate Hebrew weekly summary
- `get_differentials()` - Find unique players that performed well
- `get_chips_status()` - Track chips usage since GW19

### CaptainSelector (`src/captain_selector.py`)
- `analyze_captain_options()` - Rank captain candidates
- `get_league_captain_choices()` - What the league chose
- `print_captain_report()` - Full captain analysis

### TransferRecommendationEngine (`src/transfer_recommendations.py`)
- `calculate_player_score()` - Rate player quality
- `find_best_replacements()` - Find optimal replacements
- `get_transfer_recommendations()` - Complete transfer suggestions

## API Rate Limiting

The FPL API has rate limits. The scripts include:
- 0.5 second delay between manager requests
- Error handling for 429 (too many requests)

## Output Formats

1. **Text Reports** (.txt) - Human-readable, copy-paste friendly
2. **JSON Data** (.json) - Machine-readable for further analysis
3. **WhatsApp Summary** - Hebrew text optimized for sharing in groups

## Language Support

- Code comments: Bilingual (English + Hebrew)
- Reports: Bilingual headers
- WhatsApp Summary: Full Hebrew

## Common Development Tasks

### Add a new analysis feature
1. Create function in appropriate script (or new script)
2. Load data using `load_latest_*` pattern
3. Use `self.players_map` and `self.teams_map` for lookups
4. Save output to `self.output_dir`

### Modify report format
Edit the `generate_*_report()` functions in respective scripts.

### Change scoring algorithm
Edit `calculate_manager_score()` in `weekly_report.py`.

## FPL API Endpoints Used

```
BASE_URL = "https://fantasy.premierleague.com/api"

- /bootstrap-static/                    # Global data
- /leagues-classic/{id}/standings/      # League standings
- /entry/{id}/history/                  # Manager history
- /entry/{id}/event/{gw}/picks/         # Manager GW picks
- /event/{gw}/live/                     # Live GW data
```

## Debugging Tips

- Check `fpl_data/` for raw JSON data
- Enable verbose output with print statements
- API errors usually mean rate limiting - add delays
- "No current gameweek" happens between seasons

## Testing

```bash
# Test data collection with a small league
python src/fpl_data_collector.py 922765

# Verify files were created
ls fpl_data/

# Test individual scripts
python src/analyze_data.py
```

## Notes for Claude Code

When working on this project:
1. Always run `fpl_data_collector.py` first to get fresh data
2. Check the `fpl_data/` directory for available JSON files
3. Use the `load_latest_*` methods to get the most recent data
4. Reports go to `fpl_data/reports/`
5. The Hebrew text in `whatsapp_summary.py` is UTF-8 encoded
