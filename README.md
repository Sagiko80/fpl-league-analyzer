# 🏆 FPL League Analyzer

**Fantasy Premier League Private League Analyzer & Report Generator**

A comprehensive Python toolkit that collects data from the official FPL API and generates detailed reports, analytics, and recommendations for your private league.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- 📊 **Complete Data Collection** - Fetches all data from the FPL API
- 📋 **Weekly Reports** - Detailed analysis for each manager
- 🎯 **Captain Selection** - Data-driven captain recommendations
- 🔄 **Transfer Recommendations** - Find the best transfers for your team
- 💎 **Advanced Analytics** - Differentials, momentum, template team analysis
- 📱 **WhatsApp Summary** - Hebrew summary ready to share in groups
- ⭐ **Manager Scoring** - Rate each manager's performance (1-10)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fpl-league-analyzer.git
cd fpl-league-analyzer

# Install dependencies
pip install -r requirements.txt
```

### Find Your League ID

1. Go to https://fantasy.premierleague.com
2. Navigate to your league page
3. URL format: `https://fantasy.premierleague.com/leagues/922765/standings/c`
4. Your League ID is: **922765**

### Run Full Analysis

```bash
# Linux/Mac
./scripts/run_all.sh 922765

# Windows
scripts\run_all.bat 922765

# With your name (for personalized analysis)
./scripts/run_all.sh 922765 "Your Name"
```

### Run Individual Scripts

```bash
# 1. Collect data (required first)
python src/fpl_data_collector.py 922765

# 2. Basic analysis
python src/analyze_data.py

# 3. Weekly report
python src/weekly_report.py

# 4. WhatsApp summary (Hebrew)
python src/whatsapp_summary.py

# 5. Advanced analytics
python src/gold_mine_analysis.py

# 6. Transfer recommendations
python src/transfer_recommendations.py "Your Name"

# 7. Captain selection
python src/captain_selector.py "Your Name"
```

## 📁 Output Files

After running the scripts, you'll find these files in `fpl_data/`:

| File | Description |
|------|-------------|
| `bootstrap_data_*.json` | Global FPL data (players, teams, gameweeks) |
| `league_*.json` | Your league standings |
| `live_gw*.json` | Current gameweek live data |
| `managers_detailed_*.json` | Detailed data for each manager |
| `reports/weekly_report_*.txt` | Weekly text report |
| `reports/whatsapp_summary_*.txt` | Hebrew summary |
| `reports/gold_mine_report_*.txt` | Advanced analytics report |

## 📊 Sample Output

### Weekly Report
```
====================================================================================================
📊 FPL WEEKLY LEAGUE REPORT
====================================================================================================

📅 Gameweek: 24
👥 Total Managers: 8

📈 GAMEWEEK SUMMARY
Average Score: 52.3 points
Highest Score: 68 points (Manager A)
Lowest Score: 38 points (Manager B)

👤 DETAILED MANAGER ANALYSIS
====================================================================================================
#1 - Manager A | Team Name
====================================================================================================

📊 PERFORMANCE
Gameweek Points: 68 points
Overall Rank: 234,567 ⬆️ UP 12,345 places (+5.3%)

👑 CAPTAINCY
Captain: Haaland (MCI) - FWD
Captain Points: 14 x 2 = 28 points
✅ EXCELLENT captain choice!
```

### Manager Score (1-10)
Each manager receives a weekly score based on:
- Points relative to league average
- Rank change
- Captain performance
- Bench decisions
- Transfer costs (hits)

## 🔧 Configuration

### Automating Data Collection

#### Linux/Mac (Cron)
```bash
# Run daily at 23:00
crontab -e
0 23 * * * cd /path/to/fpl-league-analyzer && python src/fpl_data_collector.py 922765
```

#### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at desired time
4. Action: Start a Program
5. Program: `python`
6. Arguments: `src/fpl_data_collector.py 922765`
7. Start in: Your project folder

## 🏗️ Project Structure

```
fpl-league-analyzer/
├── src/                          # Python source files
│   ├── fpl_data_collector.py     # Data collection
│   ├── analyze_data.py           # Basic analysis
│   ├── weekly_report.py          # Weekly reports
│   ├── whatsapp_summary.py       # WhatsApp summary
│   ├── gold_mine_analysis.py     # Advanced analytics
│   ├── captain_selector.py       # Captain recommendations
│   └── transfer_recommendations.py # Transfer suggestions
├── scripts/                      # Shell scripts
│   ├── run_all.sh               # Linux/Mac
│   └── run_all.bat              # Windows
├── docs/                         # Documentation
├── fpl_data/                     # Output (auto-created)
├── requirements.txt
├── CLAUDE.md                     # Claude Code instructions
└── README.md
```

## 📚 Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Detailed Usage Guide](docs/USAGE_GUIDE.md)
- [Weekly Report Guide](docs/WEEKLY_REPORT_GUIDE.md)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- [Fantasy Premier League](https://fantasy.premierleague.com) for the API
- All FPL managers who inspired this project

---

**Good luck with your FPL season! 🎯⚽**
