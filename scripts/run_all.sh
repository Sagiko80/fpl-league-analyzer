#!/bin/bash
# FPL Complete Analysis - Run everything with one command!
# הרץ הכל בפקודה אחת!

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=================================="
echo "🚀 FPL Complete Analysis"
echo "ניתוח מלא של FPL"
echo "=================================="
echo ""

# Check if league ID is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide league ID"
    echo ""
    echo "Usage: ./scripts/run_all.sh <LEAGUE_ID> [optional: your name]"
    echo "Example: ./scripts/run_all.sh 922765"
    echo "Example: ./scripts/run_all.sh 922765 \"Sagi Cohen\""
    echo ""
    echo "To find your league ID:"
    echo "1. Go to fantasy.premierleague.com"
    echo "2. Click on your league"
    echo "3. Look at URL: .../leagues/922765/standings/c"
    echo "4. The number (922765) is your league ID"
    exit 1
fi

LEAGUE_ID=$1
YOUR_NAME="${2:-}"

echo "📋 League ID: $LEAGUE_ID"
if [ -n "$YOUR_NAME" ]; then
    echo "👤 Analyzing for: $YOUR_NAME"
fi
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Step 1: Collect data
echo "=================================="
echo "📥 Step 1/6: Collecting data..."
echo "=================================="
python src/fpl_data_collector.py $LEAGUE_ID
if [ $? -ne 0 ]; then
    echo "❌ Failed to collect data"
    exit 1
fi
echo "✅ Data collected successfully!"
echo ""

# Step 2: Basic analysis
echo "=================================="
echo "📊 Step 2/6: Basic Analysis"
echo "=================================="
python src/analyze_data.py
echo ""

# Step 3: Weekly Report
echo "=================================="
echo "📋 Step 3/6: Weekly League Report"
echo "=================================="
python src/weekly_report.py
echo ""

# Step 4: Gold mine analysis
echo "=================================="
echo "💎 Step 4/6: Gold Mine Analysis"
echo "=================================="
python src/gold_mine_analysis.py
echo ""

# Step 5: Transfer recommendations
echo "=================================="
echo "🔄 Step 5/6: Transfer Recommendations"
echo "=================================="
if [ -n "$YOUR_NAME" ]; then
    python src/transfer_recommendations.py "$YOUR_NAME"
else
    python src/transfer_recommendations.py
fi
echo ""

# Step 6: Captain selection
echo "=================================="
echo "👑 Step 6/6: Captain Selection"
echo "=================================="
if [ -n "$YOUR_NAME" ]; then
    python src/captain_selector.py "$YOUR_NAME"
else
    python src/captain_selector.py
fi
echo ""

# Step 7: WhatsApp Summary (optional)
echo "=================================="
echo "📱 Bonus: WhatsApp Summary (Hebrew)"
echo "=================================="
python src/whatsapp_summary.py
echo ""

# Final message
echo "=================================="
echo "✅ ANALYSIS COMPLETE!"
echo "=================================="
echo ""
echo "📊 You now have complete insights into your FPL league!"
echo "קיבלת ניתוח מלא של הליגה שלך!"
echo ""
echo "📁 Reports saved in: fpl_data/reports/"
echo ""
echo "💡 Next steps:"
echo "   - Review the differential players"
echo "   - Check transfer recommendations"
echo "   - Choose your captain"
echo "   - Share the WhatsApp summary with your league!"
echo "   - WIN your league! 🏆"
echo ""
echo "=================================="
