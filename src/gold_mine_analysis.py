#!/usr/bin/env python3
"""
FPL Advanced Analytics - ENHANCED VERSION
גרסה משופרת - שומרת תוצאות לקבצים!
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict, Counter
from datetime import datetime


class FPLAdvancedAnalytics:
    def __init__(self, data_dir: str = "fpl_data"):
        self.data_dir = Path(data_dir)
        self.output_dir = self.data_dir / "reports"
        self.output_dir.mkdir(exist_ok=True)
        
        self.managers_data = self.load_latest_managers_data()
        self.bootstrap_data = self.load_latest_bootstrap_data()
        self.live_data = self.load_latest_live_data()
        
        # מפות עזר
        self.players_map = {p['id']: p for p in self.bootstrap_data['elements']}
        self.teams_map = {t['id']: t for t in self.bootstrap_data['teams']}
    
    def load_latest_managers_data(self) -> Dict:
        manager_files = list(self.data_dir.glob("managers_detailed_*.json"))
        if not manager_files:
            raise FileNotFoundError("לא נמצאו קבצי מנהלים")
        latest_file = max(manager_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_latest_bootstrap_data(self) -> Dict:
        bootstrap_files = list(self.data_dir.glob("bootstrap_data_*.json"))
        if not bootstrap_files:
            raise FileNotFoundError("לא נמצאו קבצי bootstrap")
        latest_file = max(bootstrap_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_latest_live_data(self) -> Dict:
        live_files = list(self.data_dir.glob("live_gw*.json"))
        if not live_files:
            return {}
        latest_file = max(live_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_current_gameweek(self) -> int:
        for event in self.bootstrap_data['events']:
            if event['is_current']:
                return event['id']
        return 1
    
    def find_differentials(self, max_ownership: int = 2) -> List[Dict]:
        """מצא שחקנים שמעט מאוד אנשים מחזיקים"""
        ownership = defaultdict(int)
        
        for manager_id, data in self.managers_data.items():
            for pick in data['current_picks']['picks']:
                ownership[pick['element']] += 1
        
        differentials = []
        for player_id, count in ownership.items():
            if count <= max_ownership:
                player = self.players_map.get(player_id)
                if player:
                    differentials.append({
                        'name': player['web_name'],
                        'full_name': f"{player['first_name']} {player['second_name']}",
                        'team': self.teams_map[player['team']]['name'],
                        'position': ['GKP', 'DEF', 'MID', 'FWD'][player['element_type'] - 1],
                        'owned_by': count,
                        'total_points': player['total_points'],
                        'form': float(player['form']),
                        'price': player['now_cost'] / 10,
                        'points_per_game': float(player['points_per_game']) if player['points_per_game'] else 0
                    })
        
        differentials.sort(key=lambda x: (x['total_points'], x['form']), reverse=True)
        return differentials
    
    def analyze_momentum(self, last_n_weeks: int = 5) -> List[Dict]:
        """מי עולה בדירוג ומי יורד"""
        momentum_data = []
        
        for manager_id, data in self.managers_data.items():
            history = data['history']['current']
            if len(history) < last_n_weeks:
                continue
            
            recent = history[-last_n_weeks:]
            points_trend = [gw['points'] for gw in recent]
            avg_recent = sum(points_trend) / len(points_trend)
            
            if len(history) >= last_n_weeks + 1:
                rank_change = history[-last_n_weeks]['rank'] - history[-1]['rank']
            else:
                rank_change = 0
            
            momentum_data.append({
                'player_name': data['manager_info']['player_name'],
                'team_name': data['manager_info']['team_name'],
                'avg_points_last_n': round(avg_recent, 1),
                'recent_points': points_trend,
                'rank_change': rank_change,
                'trending': '📈 UP' if rank_change > 0 else ('📉 DOWN' if rank_change < 0 else '➡️ STABLE')
            })
        
        momentum_data.sort(key=lambda x: x['avg_points_last_n'], reverse=True)
        return momentum_data
    
    def find_template_team(self) -> Dict:
        """מצא את ה-template"""
        ownership = Counter()
        captain_count = Counter()
        
        for manager_id, data in self.managers_data.items():
            for pick in data['current_picks']['picks']:
                ownership[pick['element']] += 1
                if pick['is_captain']:
                    captain_count[pick['element']] += 1
        
        total_managers = len(self.managers_data)
        
        template_players = []
        for player_id, count in ownership.most_common(20):
            ownership_pct = (count / total_managers) * 100
            player = self.players_map.get(player_id)
            if player and ownership_pct >= 30:
                template_players.append({
                    'name': player['web_name'],
                    'position': ['GKP', 'DEF', 'MID', 'FWD'][player['element_type'] - 1],
                    'owned_by': count,
                    'ownership_pct': round(ownership_pct, 1),
                    'captained_by': captain_count.get(player_id, 0),
                    'price': player['now_cost'] / 10
                })
        
        return {
            'template_players': template_players,
            'total_managers': total_managers
        }
    
    def analyze_budget_management(self) -> List[Dict]:
        """נתח איך כל מנהל מנהל את התקציב שלו - FIX: חישוב נכון!"""
        budget_analysis = []
        
        for manager_id, data in self.managers_data.items():
            if not data['history']['current']:
                continue
            
            latest = data['history']['current'][-1]
            
            # FIX: ה-API מחזיר value כבר כולל bank!
            # value = סה"כ ערך (קבוצה + בנק) בעשיריות של פאונד
            # bank = כסף בבנק בעשיריות של פאונד
            
            total_value = latest.get('value', 1000) / 10  # זה כבר הסכום הכולל!
            bank = latest.get('bank', 0) / 10
            team_value = total_value - bank  # ערך הקבוצה בלבד
            
            budget_analysis.append({
                'manager': data['manager_info']['player_name'],
                'team_value': round(team_value, 1),
                'bank': round(bank, 1),
                'total_value': round(total_value, 1),
                'transfers_made': latest.get('event_transfers', 0),
                'hits_taken': latest.get('event_transfers_cost', 0) / 4
            })
        
        budget_analysis.sort(key=lambda x: x['total_value'], reverse=True)
        return budget_analysis
    
    def analyze_consistency(self) -> List[Dict]:
        """מי יציב ומי מתפוצץ מדי פעם?"""
        consistency_data = []
        
        for manager_id, data in self.managers_data.items():
            history = data['history']['current']
            if len(history) < 5:
                continue
            
            points = [gw['points'] for gw in history]
            avg = sum(points) / len(points)
            variance = sum((p - avg) ** 2 for p in points) / len(points)
            std_dev = variance ** 0.5
            
            max_gw = max(points)
            min_gw = min(points)
            
            consistency_data.append({
                'manager': data['manager_info']['player_name'],
                'avg_points': round(avg, 1),
                'std_deviation': round(std_dev, 1),
                'max_gw': max_gw,
                'min_gw': min_gw,
                'range': max_gw - min_gw,
                'type': 'Consistent' if std_dev < 15 else 'Explosive'
            })
        
        return consistency_data
    
    def save_report_to_file(self, content: str, filename: str):
        """שמור דוח לקובץ"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Saved: {filepath}")
        return filepath
    
    def generate_gold_report(self):
        """הפק דוח מלא - גם למסך וגם לקובץ!"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        current_gw = self.get_current_gameweek()
        
        # בנה את הדוח
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("💎 FPL GOLD MINE - Advanced Analytics Report")
        report_lines.append("🏆 דוח ניתוח מתקדם - הפוך דאטה לזהב!")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append(f"📅 Current Gameweek: {current_gw}")
        report_lines.append(f"👥 Total Managers: {len(self.managers_data)}")
        report_lines.append(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 1. DIFFERENTIALS
        report_lines.append("")
        report_lines.append("🔍 " + "=" * 75)
        report_lines.append("💎 DIFFERENTIAL OPPORTUNITIES - שחקנים שרק מעטים מחזיקים")
        report_lines.append("=" * 78)
        report_lines.append("אלו שחקנים שיכולים לתת לך יתרון אם הם יתפוצצו!")
        report_lines.append("")
        
        differentials = self.find_differentials(max_ownership=2)
        report_lines.append(f"{'Player':<25} {'Pos':<5} {'Team':<15} {'Owned':<8} {'Points':<8} {'Form':<8} {'Price':<8}")
        report_lines.append("-" * 90)
        for diff in differentials[:15]:
            report_lines.append(
                f"{diff['name']:<25} {diff['position']:<5} {diff['team']:<15} "
                f"{diff['owned_by']:<8} {diff['total_points']:<8} "
                f"{diff['form']:<8.1f} £{diff['price']:<7.1f}m"
            )
        
        # 2. MOMENTUM
        report_lines.append("")
        report_lines.append("")
        report_lines.append("📊 " + "=" * 75)
        report_lines.append("🔥 MOMENTUM ANALYSIS - מי עולה ומי יורד")
        report_lines.append("=" * 78)
        report_lines.append("נתח מי בפורמה טובה לאחרונה!")
        report_lines.append("")
        
        momentum = self.analyze_momentum(last_n_weeks=5)
        report_lines.append(f"{'Manager':<30} {'Trend':<12} {'Avg Last 5':<12} {'Rank Change':<12}")
        report_lines.append("-" * 78)
        for m in momentum[:10]:
            report_lines.append(
                f"{m['player_name']:<30} {m['trending']:<12} "
                f"{m['avg_points_last_n']:<12} {m['rank_change']:<12}"
            )
        
        # 3. TEMPLATE
        report_lines.append("")
        report_lines.append("")
        report_lines.append("🎯 " + "=" * 75)
        report_lines.append("👥 TEMPLATE TEAM - השחקנים שכולם מחזיקים")
        report_lines.append("=" * 78)
        report_lines.append("זה מה שכולם עושים - האם אתה רוצה להיות שונה?")
        report_lines.append("")
        
        template = self.find_template_team()
        report_lines.append(f"{'Player':<25} {'Pos':<5} {'Ownership':<12} {'Captain %':<12} {'Price':<8}")
        report_lines.append("-" * 78)
        for player in template['template_players']:
            cap_pct = (player['captained_by'] / template['total_managers']) * 100
            report_lines.append(
                f"{player['name']:<25} {player['position']:<5} "
                f"{player['ownership_pct']:<12.1f}% {cap_pct:<12.1f}% £{player['price']:<7.1f}m"
            )
        
        # 4. BUDGET MANAGEMENT
        report_lines.append("")
        report_lines.append("")
        report_lines.append("💰 " + "=" * 75)
        report_lines.append("💵 BUDGET MANAGEMENT - ניהול תקציב")
        report_lines.append("=" * 78)
        report_lines.append("מי מנהל את הכסף בצורה הכי חכמה?")
        report_lines.append("")
        
        budget = self.analyze_budget_management()
        report_lines.append(f"{'Manager':<30} {'Team Value':<12} {'Bank':<10} {'Total':<10} {'Hits':<8}")
        report_lines.append("-" * 78)
        for b in budget[:10]:
            report_lines.append(
                f"{b['manager']:<30} £{b['team_value']:<11.1f}m £{b['bank']:<9.1f}m "
                f"£{b['total_value']:<9.1f}m {int(b['hits_taken']):<8}"
            )
        
        # 5. CONSISTENCY
        report_lines.append("")
        report_lines.append("")
        report_lines.append("🎲 " + "=" * 75)
        report_lines.append("📈 CONSISTENCY vs EXPLOSIVENESS")
        report_lines.append("=" * 78)
        report_lines.append("מי יציב ומי משחק מסוכן?")
        report_lines.append("")
        
        consistency = self.analyze_consistency()
        report_lines.append(f"{'Manager':<30} {'Type':<12} {'Avg':<8} {'StdDev':<10} {'Range':<10}")
        report_lines.append("-" * 78)
        for c in consistency[:10]:
            report_lines.append(
                f"{c['manager']:<30} {c['type']:<12} {c['avg_points']:<8.1f} "
                f"{c['std_deviation']:<10.1f} {c['range']:<10}"
            )
        
        # RECOMMENDATIONS
        report_lines.append("")
        report_lines.append("")
        report_lines.append("💡 " + "=" * 75)
        report_lines.append("🎯 STRATEGIC RECOMMENDATIONS - המלצות אסטרטגיות")
        report_lines.append("=" * 78)
        
        report_lines.append("")
        report_lines.append("1. 💎 Differential Strategy:")
        if differentials:
            top_diff = differentials[0]
            report_lines.append(
                f"   → Consider: {top_diff['name']} ({top_diff['position']}) - "
                f"Only {top_diff['owned_by']} managers have him!"
            )
        
        report_lines.append("")
        report_lines.append("2. 🔥 Form Players:")
        if momentum:
            top_form = momentum[0]
            report_lines.append(
                f"   → Hot streak: {top_form['player_name']} - "
                f"Avg {top_form['avg_points_last_n']} pts in last 5 GWs"
            )
        
        report_lines.append("")
        report_lines.append("3. 👥 Template Avoidance:")
        template_count = len(template['template_players'])
        report_lines.append(f"   → {template_count} players are heavily owned (30%+)")
        report_lines.append(f"   → Consider differentiating in at least 3-4 positions")
        
        report_lines.append("")
        report_lines.append("4. 💰 Budget Tips:")
        if budget:
            richest = budget[0]
            report_lines.append(
                f"   → Highest team value: {richest['manager']} (£{richest['total_value']}m)"
            )
            report_lines.append(f"   → Don't waste money in the bank - invest wisely!")
        
        report_lines.append("")
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("🎯 Good luck! May the stats be with you! בהצלחה!")
        report_lines.append("=" * 80)
        
        # צור את הטקסט המלא
        full_report = "\n".join(report_lines)
        
        # הדפס למסך
        print(full_report)
        
        # שמור לקובץ
        report_file = self.save_report_to_file(
            full_report,
            f"gold_mine_report_{timestamp}.txt"
        )
        
        # שמור גם JSON עם כל הדאטה
        json_data = {
            'timestamp': timestamp,
            'gameweek': current_gw,
            'total_managers': len(self.managers_data),
            'differentials': differentials[:15],
            'momentum': momentum[:10],
            'template': template,
            'budget': budget[:10],
            'consistency': consistency[:10]
        }
        
        json_file = self.output_dir / f"gold_mine_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved JSON data: {json_file}")
        print(f"\n📁 All reports saved in: {self.output_dir}")
        
        return report_file, json_file


def main():
    try:
        analyzer = FPLAdvancedAnalytics()
        report_file, json_file = analyzer.generate_gold_report()
        
        print("\n" + "="*80)
        print("✅ SUCCESS! Reports generated:")
        print(f"   📄 Text report: {report_file}")
        print(f"   📊 JSON data: {json_file}")
        print("="*80)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nPlease run fpl_data_collector.py first!")
        print("הרץ קודם: python fpl_data_collector.py <LEAGUE_ID>")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()