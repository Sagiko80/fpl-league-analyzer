# 💎 FPL Gold Mine - מדריך שימוש מלא
## How to Turn Your FPL Data Into GOLD!

---

## 📚 תוכן עניינים | Table of Contents

1. [סקירה כללית](#overview)
2. [התקנה](#installation)
3. [איסוף דאטה](#data-collection)
4. [ניתוחים זמינים](#available-analytics)
5. [דוגמאות שימוש](#usage-examples)
6. [אסטרטגיות מנצחות](#winning-strategies)

---

## 🎯 סקירה כללית | Overview {#overview}

יש לך עכשיו **5 סקריפטים חזקים** שהופכים את הדאטה שלך לתובנות מנצחות:

### 1. **fpl_data_collector.py** 📊
איסוף כל הדאטה מה-API

### 2. **analyze_data.py** 📈
ניתוח בסיסי - דירוג, ביצועים שבועיים, קפטנים פופולריים

### 3. **gold_mine_analysis.py** 💎
ניתוחים מתקדמים:
- Differentials (שחקנים שרק לך יש)
- Momentum (מי עולה/יורד)
- Template team (מה כולם עושים)
- Budget management
- Consistency analysis

### 4. **transfer_recommendations.py** 🔄
המלצות העברות:
- מי להוציא
- מי להביא
- ניתוח עלות-תועלת

### 5. **captain_selector.py** 👑
עזרה בבחירת קפטן:
- ניתוח כל האופציות שלך
- מה הליגה בוחרת
- Safe vs Differential picks

---

## 🚀 התקנה | Installation {#installation}

### שלב 1: התקן Python
אם אין לך, הורד מ-https://python.org (Python 3.8+)

### שלב 2: התקן תלויות
```bash
pip install requests
```

### שלב 3: בדוק שהכל עובד
```bash
python --version
# אמור להציג: Python 3.x.x
```

---

## 📥 איסוף דאטה | Data Collection {#data-collection}

### איסוף דאטה בסיסי

```bash
# החלף 922765 במזהה הליגה שלך
python fpl_data_collector.py 922765
```

**איך למצוא את מזהה הליגה?**
1. לך ל-https://fantasy.premierleague.com
2. לחץ על הליגה שלך
3. תראה URL: `.../leagues/922765/standings/c`
4. המספר (922765) זה המזהה!

### מה נוצר?
```
fpl_data/
├── bootstrap_data_2024-02-02.json       # כל השחקנים והקבוצות
├── league_922765_2024-02-02.json        # דירוג הליגה
├── live_gw23_2024-02-02.json            # נתוני מחזור LIVE
├── managers_detailed_2024-02-02.json    # דאטה מפורט של כולם
└── summary_2024-02-02.json              # סיכום
```

---

## 🔬 ניתוחים זמינים | Available Analytics {#available-analytics}

### 1️⃣ ניתוח בסיסי (analyze_data.py)

```bash
python analyze_data.py
```

**מה תקבל:**
- 🏆 טבלת דירוג מלאה
- ⚡ מובילים במחזור הנוכחי
- 👑 קפטנים פופולריים
- ⭐ שחקנים בבעלות גבוהה
- 🔄 פעילות העברות

**מתי להשתמש:**
- כל שבוע אחרי שהמחזור מסתיים
- לראות את המצב הכללי בליגה

---

### 2️⃣ ניתוח מתקדם - Gold Mine (gold_mine_analysis.py)

```bash
python gold_mine_analysis.py
```

**מה תקבל:**

#### 💎 Differentials
שחקנים שמעט מאוד אנשים מחזיקים אבל עם סטטיסטיקות טובות.

**למה זה חשוב?**
אם הם יתפוצצו, רק לך יהיו הנקודות! 🚀

#### 📊 Momentum Analysis
מי עולה ומי יורד בדירוג לאחרונה.

**למה זה חשוב?**
מזהה טרנדים לפני כולם - תוכל לתפוס שחקנים "לפני שהם מפורסמים"

#### 🎯 Template Team
השחקנים שכולם מחזיקים (30%+ ownership).

**למה זה חשוב?**
- אם אין לך אותם ונכשלים = בעיה קטנה
- אם אין לך אותם והם מתפוצצים = אסון! 💥
- עקוב אחרי ה-template אבל אל תהיה עבד שלו

#### 💰 Budget Management
מי מנהל את התקציב בצורה הכי חכמה.

**למה זה חשוב?**
Team Value גבוה = גמישות בהעברות בהמשך העונה

#### 📈 Consistency vs Explosiveness
מי יציב (מביא נקודות כל שבוע) ומי volatile (פעם 80, פעם 30).

**למה זה חשוב?**
עוזר לך להחליט על אסטרטגיה - בטוח או מסוכן?

**מתי להשתמש:**
- לפני כל העברה חשובה
- כשאתה רוצה לשנות אסטרטגיה
- פעם בשבוע לבדוק טרנדים

---

### 3️⃣ המלצות העברות (transfer_recommendations.py)

```bash
# ניתוח כללי
python transfer_recommendations.py

# ניתוח לשחקן ספציפי
python transfer_recommendations.py "Sagi Cohen"
```

**מה תקבל:**
1. **רשימת שחקנים חלשים** בקבוצה שלך
2. **5 תחליפים מומלצים** לכל שחקן חלש
3. **ניתוח עלות-תועלת** (האם שווה לקחת hit?)

**אלגוריתם הציון:**
```
Score = (Form × 3) + (PPG × 2) + (ICT/10) + (Selected%/5) + (Minutes/900)
```

**מתי להשתמש:**
- **לפני deadline!** (שעתיים לפני)
- כשיש לך free transfer
- כשאתה שוקל hit (-4 נקודות)

**כלל אצבע להיטים:**
⚠️ אל תקח hit אלא אם ההעברה תרוויח לך **8+ נקודות**

---

### 4️⃣ בחירת קפטן (captain_selector.py)

```bash
# ניתוח כללי
python captain_selector.py

# ניתוח לשחקן ספציפי
python captain_selector.py "Sagi Cohen"
```

**מה תקבל:**
1. **דירוג כל האופציות שלך** לקפטן
2. **מה הליגה בוחרת** (popularity %)
3. **Safe Pick** - הבחירה הבטוחה
4. **Differential Pick** - הבחירה המסוכנת אבל מתגמלת

**אלגוריתם הציון:**
```
Captain Score = (Form × 5) + (PPG × 3) + (Bonus/2) + ((Goals+Assists)/3) + (ICT/20)
```

**מתי להשתמש:**
- **כל שבוע לפני deadline!**
- בחירת הקפטן היא ההחלטה החשובה ביותר

**אסטרטגיות:**

🟢 **Safe Strategy:**
- בחר את הקפטן הכי פופולרי
- פחות סיכון
- פחות סיכוי להתבדל

🔴 **Aggressive Strategy:**
- בחר differential captain
- יותר סיכון
- אם יצליח - תעקוף המון אנשים!

💡 **מתי differential captain?**
- כשאתה מאחורה בדירוג
- כשהפער קטן ואתה רוצה להשתלט
- כשה-safe pick לא נראה חזק מאוד

---

## 💡 דוגמאות שימוש | Usage Examples {#usage-examples}

### תרחיש 1: זה רביעי בלילה, deadline מחר

```bash
# 1. אסוף דאטה עדכני
python fpl_data_collector.py 922765

# 2. בדוק מה קורה בליגה
python analyze_data.py

# 3. קבל המלצות העברות
python transfer_recommendations.py "Your Name"

# 4. בחר קפטן
python captain_selector.py "Your Name"
```

### תרחיש 2: אתה רוצה לשנות אסטרטגיה לטווח ארוך

```bash
# 1. אסוף דאטה
python fpl_data_collector.py 922765

# 2. הרץ ניתוח מתקדם
python gold_mine_analysis.py

# 3. חפש differentials
# (בתוך הדוח - קטע "DIFFERENTIAL OPPORTUNITIES")

# 4. בדוק budget management
# (בתוך הדוח - קטע "BUDGET MANAGEMENT")
```

### תרחיש 3: אתה מאחורי בדירוג וצריך לסכן

```bash
# 1. אסוף דאטה
python fpl_data_collector.py 922765

# 2. הרץ Gold Mine
python gold_mine_analysis.py

# מצא differentials בדוח
# מצא שחקנים שרק מעטים מחזיקים

# 3. בחר differential captain
python captain_selector.py "Your Name"
# תחפש את ה-"DIFFERENTIAL PICK"
```

---

## 🏆 אסטרטגיות מנצחות | Winning Strategies {#winning-strategies}

### 📅 שגרת שבוע מומלצת

**ראשון-שלישי:**
```bash
python fpl_data_collector.py YOUR_LEAGUE_ID
python gold_mine_analysis.py
```
- בדוק differentials
- עקוב אחרי injuries
- תכנן העברות

**רביעי-חמישי (לפני deadline):**
```bash
python fpl_data_collector.py YOUR_LEAGUE_ID
python transfer_recommendations.py "Your Name"
python captain_selector.py "Your Name"
```
- קבל החלטות סופיות
- העברות
- קפטן

**שישי-ראשון (אחרי המחזור):**
```bash
python fpl_data_collector.py YOUR_LEAGUE_ID
python analyze_data.py
```
- ראה תוצאות
- נתח מה עבד ומה לא

---

### 🎯 כללי אצבע חשובים

#### 1. Differentials (💎)
- **מתי לקחת:** כשאתה מאחורי בדירוג
- **סיכון:** בינוני-גבוה
- **תגמול:** עלייה מהירה בדירוג אם יצליח

#### 2. Template Players (👥)
- **חייב להחזיק:** Top 3 (50%+ owned)
- **כדאי להחזיק:** Top 10 (30%+ owned)
- **אופציונלי:** מתחת ל-30%

#### 3. Budget Management (💰)
- **Bank אופטימלי:** £0.0-1.0m
- **מעל £2.0m בבנק:** אתה מבזבז כסף!
- **Team Value אופטימלי:** £103.0m+ באמצע העונה

#### 4. Captain (👑)
- **אל תשכח!** זה פי 2 נקודות
- **90% מהזמן:** Template captain
- **10% מהזמן:** Differential (כשמאחורי)

#### 5. Hits (-4 נקודות) (⚠️)
- **כדאי לקחת רק אם:** השחקן החדש ירוויח 8+ נקודות יותר
- **לא כדאי:** אם זה סתם שיפור קטן

---

### 📊 KPIs לעקוב אחריהם

מדדים שכדאי לעקוב אחריהם כל שבוע:

1. **Overall Rank** - הדירוג הכללי שלך
2. **League Rank** - הדירוג בליגה הפרטית
3. **Team Value** - ערך הקבוצה (רוצה שיעלה)
4. **Avg Points/GW** - ממוצע נקודות למחזור
5. **Green Arrows** - כמה שבועות עליתי
6. **Red Arrows** - כמה שבועות ירדתי

---

### 🔥 טיפים מתקדמים

#### 1. Fixture Analysis
עקוב אחרי לוח המשחקים הקרוב:
- קבוצות עם 3+ משחקים קלים = 📈
- קבוצות עם 3+ משחקים קשים = 📉

#### 2. Double Gameweeks
שבועות עם 2 משחקים לקבוצה:
- 🔥 **זמן מושלם ל-Triple Captain!**
- הבא שחקנים מקבוצות עם DGW

#### 3. Blank Gameweeks
שבועות שבהם חלק מהקבוצות לא משחקות:
- 🎯 **זמן מושלם ל-Free Hit!**
- או תכנן מראש קבוצה ללא השחקנים האלו

#### 4. Form vs Fixtures
מה יותר חשוב?
- **Short term (1-3 GWs):** Form
- **Long term (4+ GWs):** Fixtures

---

## 🤖 Automation Tips

### Windows - Task Scheduler

1. פתח Task Scheduler
2. Create Basic Task
3. Name: "FPL Data Collection"
4. Trigger: Daily at 11 PM
5. Action: Start a Program
   - Program: `python`
   - Arguments: `fpl_data_collector.py YOUR_LEAGUE_ID`
   - Start in: `C:\path\to\fpl_tracker`

### Mac/Linux - Crontab

```bash
# ערוך crontab
crontab -e

# הוסף שורה - איסוף יומי ב-23:00
0 23 * * * cd /path/to/fpl_tracker && python3 fpl_data_collector.py YOUR_LEAGUE_ID
```

---

## 🆘 פתרון בעיות | Troubleshooting

### בעיה: "ModuleNotFoundError: No module named 'requests'"
```bash
pip install requests
```

### בעיה: "urllib3 v2.0 only supports OpenSSL 1.1.1+"
```bash
pip install 'urllib3==1.26.18'
```

### בעיה: "League not found"
- וודא שמזהה הליגה נכון
- בדוק שהליגה ציבורית או שאתה חבר בה

### בעיה: הסקריפט לא מוצא קבצים
```bash
# וודא שהרצת קודם את איסוף הדאטה
python fpl_data_collector.py YOUR_LEAGUE_ID
```

---

## 📞 עזרה נוספת

עם שאלות? בדוק את:
1. README.md - מדריך כללי
2. QUICKSTART.md - התחלה מהירה
3. הקוד עצמו - יש הרבה הערות

---

## 🎯 סיכום

יש לך עכשיו **ארסנל מלא של כלים** להפוך דאטה לזהב:

1. ✅ **איסוף דאטה** - fpl_data_collector.py
2. ✅ **ניתוח בסיסי** - analyze_data.py  
3. ✅ **ניתוחים מתקדמים** - gold_mine_analysis.py
4. ✅ **המלצות העברות** - transfer_recommendations.py
5. ✅ **בחירת קפטן** - captain_selector.py

**השתמש בהם בחכמה ותנצח את הליגה! 🏆**

---

**Good luck and may the stats be with you!**
**בהצלחה וישאו הסטטיסטיקות אתכם!** ⚽📊💎
