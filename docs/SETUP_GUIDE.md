# 🚀 מדריך הגדרה - FPL Weekly Summary

## שלב 1: התקנת Dependencies

```bash
pip install -r requirements.txt
```

---

## שלב 2: הגדרת Twilio (לשליחת WhatsApp)

### 2.1 יצירת חשבון Twilio (חינמי!)

1. היכנס ל: https://www.twilio.com/try-twilio
2. הירשם עם אימייל
3. אשר את הטלפון שלך

### 2.2 הפעלת WhatsApp Sandbox

1. היכנס ל: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. תראה מספר כמו: `+14155238886`
3. שלח מהטלפון שלך הודעת WhatsApp למספר הזה עם הקוד שמופיע (משהו כמו: `join XXX-XXX`)
4. תקבל אישור שהצטרפת ל-Sandbox

### 2.3 קבלת המפתחות

1. היכנס ל: https://console.twilio.com/
2. בצד שמאל תראה:
   - **Account SID** - מתחיל ב-`AC...`
   - **Auth Token** - לחץ על העין לחשוף

---

## שלב 3: הגדרת Claude API (לתחזיות חכמות)

### 3.1 יצירת חשבון Anthropic

1. היכנס ל: https://console.anthropic.com/
2. הירשם
3. לך ל-API Keys
4. צור מפתח חדש

**הערה:** יש $5 קרדיט חינמי לחשבון חדש!

---

## שלב 4: יצירת קובץ Config

הרץ:
```bash
python src/fpl_weekly_summary.py --setup
```

זה ייצור קובץ `config.json`. ערוך אותו:

```json
{
  "claude_api_key": "sk-ant-XXXXX",
  "twilio_account_sid": "ACXXXXXXXXXXXXXXX",
  "twilio_auth_token": "XXXXXXXXXXXXXXX",
  "twilio_from_number": "+14155238886",
  "whatsapp_to_number": "+972501234567"
}
```

### הסבר על השדות:

| שדה | הסבר |
|-----|------|
| `claude_api_key` | מפתח API של Anthropic |
| `twilio_account_sid` | Account SID מ-Twilio |
| `twilio_auth_token` | Auth Token מ-Twilio |
| `twilio_from_number` | מספר ה-Sandbox של Twilio (בדרך כלל `+14155238886`) |
| `whatsapp_to_number` | **המספר שלך** בפורמט `+972XXXXXXXXX` |

---

## שלב 5: הרצה!

```bash
# איסוף נתונים (אם עוד לא עשית)
python src/fpl_data_collector.py 922765

# הרצת הסיכום השבועי
python src/fpl_weekly_summary.py
```

### אפשרויות הרצה:

```bash
# רגיל - סיכום + WhatsApp
python src/fpl_weekly_summary.py

# בלי WhatsApp (רק שמירה לקובץ)
python src/fpl_weekly_summary.py --no-whatsapp

# יצירת קובץ config
python src/fpl_weekly_summary.py --setup
```

---

## 🔧 פתרון בעיות

### "Twilio לא מוגדר"
- ודא שיצרת `config.json` עם המפתחות הנכונים
- ודא ששלחת `join XXX-XXX` מהטלפון שלך ל-Twilio

### "Claude API error"
- ודא שמפתח ה-API תקין
- אפשר להמשיך בלי - תקבל תחזיות בסיסיות

### "לא נמצאו קבצי נתונים"
- הרץ קודם: `python src/fpl_data_collector.py <LEAGUE_ID>`

---

## 💡 טיפים

1. **Twilio Sandbox** - ההודעות יעבדו רק למספר ששלח `join` (את עצמך). לשליחה לקבוצה תצטרך חשבון Twilio בתשלום.

2. **Claude API** - אופציונלי לגמרי! בלעדיו תקבל תחזיות בסיסיות.

3. **משתני סביבה** - במקום `config.json` אפשר להגדיר:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-XXXXX"
   export TWILIO_ACCOUNT_SID="ACXXXXX"
   export TWILIO_AUTH_TOKEN="XXXXX"
   export TWILIO_FROM_NUMBER="+14155238886"
   export WHATSAPP_TO_NUMBER="+972501234567"
   ```

---

## 📱 שליחה לקבוצת WhatsApp

ה-Sandbox של Twilio מאפשר לשלוח רק למספר ששלח `join`.

**לשליחה לקבוצה:**
1. תצטרך חשבון Twilio בתשלום
2. או: שלח לעצמך והעתק לקבוצה ידנית
3. או: שתמש ב-WhatsApp Web API (מסובך יותר)

---

בהצלחה! 🏆⚽
