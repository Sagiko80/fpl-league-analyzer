# מדריך מהיר | Quick Start Guide

## 🚀 התחלה מהירה | Quick Start

### שלב 1: מצא את מזהה הליגה | Step 1: Find Your League ID

1. היכנס ל- https://fantasy.premierleague.com
2. לך לליגה הפרטית שלך
3. העתק את המספר מה-URL:
   ```
   https://fantasy.premierleague.com/leagues/314159/standings/c
                                              ^^^^^^
                                            זה המזהה!
   ```

### שלב 2: התקן תלויות | Step 2: Install Dependencies

```bash
pip install requests
```

או:
```bash
pip install -r requirements.txt
```

### שלב 3: הרץ את האיסוף | Step 3: Run Collection

**אופציה א' - עם Python ישירות:**
```bash
python fpl_data_collector.py 314159
```

**אופציה ב' - עם סקריפט Bash:**
```bash
./collect_fpl_data.sh 314159
```

### שלב 4: נתח את הדאטה | Step 4: Analyze Data

```bash
python analyze_data.py
```

או:
```bash
./analyze.sh
```

---

## 📁 מה יווצר? | What Gets Created?

אחרי ההרצה תווצר תיקייה `fpl_data/` עם:

```
fpl_data/
├── bootstrap_data_2024-02-02.json      # כל השחקנים והקבוצות
├── league_314159_2024-02-02.json       # דירוג הליגה
├── live_gw20_2024-02-02.json           # נתוני מחזור נוכחי LIVE
├── managers_detailed_2024-02-02.json   # דאטה מפורט של כל מנהל
└── summary_2024-02-02.json             # סיכום
```

---

## 📊 מה יוצא בניתוח? | What's in the Analysis?

הסקריפט `analyze_data.py` מציג:

1. **טבלת דירוג** - המצב הנוכחי בליגה
2. **מובילים במחזור** - מי עשה הכי טוב השבוע
3. **קפטנים פופולריים** - מי הקפטן הכי נפוץ
4. **שחקנים בבעלות** - השחקנים הפופולריים ביותר
5. **פעילות העברות** - מי עשה כמה העברות

---

## ⚙️ הרצה אוטומטית | Automatic Running

### עם Cron (Linux/Mac):

```bash
# ערוך crontab
crontab -e

# הוסף שורה להרצה יומית ב-23:00
0 23 * * * cd /path/to/fpl_tracker && python3 fpl_data_collector.py 314159
```

ראה עוד דוגמאות ב-`crontab_examples.txt`

### עם Task Scheduler (Windows):

1. חפש "Task Scheduler" בחיפוש Windows
2. לחץ "Create Basic Task"
3. תן שם למשימה (למשל "FPL Data Collector")
4. Trigger: Daily
5. Time: 23:00 (או זמן אחר)
6. Action: Start a Program
7. Program: `python`
8. Arguments: `fpl_data_collector.py 314159`
9. Start in: הנתיב המלא לתיקייה
10. Finish!

---

## 🔍 דוגמאות שימוש נוספות | Additional Usage Examples

### ניתוח מותאם אישית:

```python
from analyze_data import FPLAnalyzer

analyzer = FPLAnalyzer()

# קבל רק את המובילים
top_managers = analyzer.get_league_standings()[:3]

# קבל את הקפטן הפופולרי
captains = analyzer.get_most_captained_players()
print(f"Most popular captain: {captains[0]['player']}")

# בדוק מי עשה הכי הרבה העברות
transfers = analyzer.get_transfer_activity()
most_active = max(transfers, key=lambda x: x['transfers'])
print(f"Most active: {most_active['player_name']} with {most_active['transfers']} transfers")
```

### עבודה עם הדאטה הגולמי:

```python
import json

# טען דאטה של מנהל
with open('fpl_data/managers_detailed_2024-02-02.json') as f:
    managers = json.load(f)

# עבור על כל מנהל
for manager_id, data in managers.items():
    name = data['manager_info']['player_name']
    points = data['manager_info']['total_points']
    print(f"{name}: {points} points")
```

---

## 🎯 טיפים למתקדמים | Advanced Tips

### 1. שמירת היסטוריה

הקבצים נשמרים עם תאריך, אז אפשר לאסוף דאטה לאורך זמן ולהשוות:

```bash
# הרץ כל יום והקבצים יישמרו בנפרד
python fpl_data_collector.py 314159  # יום א'
python fpl_data_collector.py 314159  # יום ב'
python fpl_data_collector.py 314159  # יום ג'
# וכו'...
```

### 2. ניתוח השוואתי

```python
import json
import glob

# טען את כל הקבצים ההיסטוריים
files = sorted(glob.glob('fpl_data/managers_detailed_*.json'))

# השווה בין שני תאריכים
with open(files[0]) as f:
    old_data = json.load(f)
with open(files[-1]) as f:
    new_data = json.load(f)

# חשב שינויים
for manager_id in old_data:
    old_points = old_data[manager_id]['manager_info']['total_points']
    new_points = new_data[manager_id]['manager_info']['total_points']
    gain = new_points - old_points
    print(f"Manager {manager_id} gained {gain} points")
```

### 3. ייצוא לאקסל

```python
import json
import pandas as pd

with open('fpl_data/managers_detailed_2024-02-02.json') as f:
    data = json.load(f)

# המר לטבלה
rows = []
for manager_id, info in data.items():
    for gw in info['history']['current']:
        rows.append({
            'manager': info['manager_info']['player_name'],
            'gameweek': gw['event'],
            'points': gw['points'],
            'total': gw['total_points'],
            'rank': gw.get('rank', 'N/A')
        })

df = pd.DataFrame(rows)
df.to_excel('fpl_analysis.xlsx', index=False)
print("Exported to fpl_analysis.xlsx")
```

---

## ❓ שאלות נפוצות | FAQ

**ש: הסקריפט לא מוצא את הליגה שלי**
ת: וודא שמזהה הליגה נכון ושהליגה היא ציבורית (או שאתה חבר בה)

**ש: אני מקבל שגיאת "Too many requests"**
ת: ה-API מוגבל. הסקריפט מוסיף המתנות אוטומטיות, אבל אם הליגה גדולה מאוד זה יכול לקרות

**ש: האם הדאטה בזמן אמת?**
ת: כן! הסקריפט מושך את הדאטה האחרון כולל מחזורים שעדיין בעיצומם

**ש: איך אני יכול לראות מה קרה במחזורים קודמים?**
ת: כל הדאטה נשמר בקובץ `managers_detailed_*.json` תחת `history.current`

**ש: האם אפשר להריץ את זה על כמה ליגות?**
ת: כן! פשוט הרץ עם ID שונה לכל ליגה:
```bash
python fpl_data_collector.py 111111
python fpl_data_collector.py 222222
python fpl_data_collector.py 333333
```

---

## 🆘 עזרה | Help

אם נתקלת בבעיות:
1. בדוק שהתקנת את `requests`: `pip install requests`
2. וודא שמזהה הליגה נכון
3. בדוק את הלוגים אם הוספת אותם
4. נסה להריץ ידנית קודם כדי לראות שהכל עובד

---

**בהצלחה! Good luck!** 🎯⚽
