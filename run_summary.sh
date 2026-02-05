#!/bin/bash
# FPL Weekly Summary - סיכום שבועי מהיר

echo "🏆 FPL Weekly Summary"
echo "===================="
echo ""

# בדוק אם יש league ID
if [ -z "$1" ]; then
    echo "Usage: ./run_summary.sh <LEAGUE_ID>"
    echo "Example: ./run_summary.sh 922765"
    exit 1
fi

LEAGUE_ID=$1

# שלב 1: איסוף נתונים
echo "📥 אוסף נתונים מה-API..."
python src/fpl_data_collector.py $LEAGUE_ID

if [ $? -ne 0 ]; then
    echo "❌ שגיאה באיסוף נתונים"
    exit 1
fi

echo ""

# שלב 2: יצירת סיכום
echo "📊 מייצר סיכום שבועי..."
python src/fpl_weekly_summary.py

echo ""
echo "✅ סיום!"
