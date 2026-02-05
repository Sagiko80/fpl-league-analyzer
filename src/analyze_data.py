#!/usr/bin/env python3
"""
FPL Data Analysis Examples
דוגמאות לניתוח הדאטה שנאסף
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class FPLAnalyzer:
    def __init__(self, data_dir: str = "fpl_data"):
        self.data_dir = Path(data_dir)
        
    def load_latest_managers_data(self) -> Dict:
        """טען את הדאטה האחרון של המנהלים"""
        manager_files = list(self.data_dir.glob("managers_detailed_*.json"))
        if not manager_files:
            raise FileNotFoundError("לא נמצאו קבצי מנהלים")
        
        latest_file = max(manager_files, key=lambda p: p.stat().st_mtime)
        print(f"טוען קובץ: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_latest_bootstrap_data(self) -> Dict:
        """טען את הדאטה הגלובלי האחרון"""
        bootstrap_files = list(self.data_dir.glob("bootstrap_data_*.json"))
        if not bootstrap_files:
            raise FileNotFoundError("לא נמצאו קבצי bootstrap")
        
        latest_file = max(bootstrap_files, key=lambda p: p.stat().st_mtime)
        print(f"טוען קובץ: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_league_standings(self) -> List[Dict]:
        """קבל את הדירוג של הליגה ממוין"""
        managers_data = self.load_latest_managers_data()
        
        standings = []
        for manager_id, data in managers_data.items():
            standings.append({
                'rank': len(standings) + 1,  # נעדכן בהמשך
                'player_name': data['manager_info']['player_name'],
                'team_name': data['manager_info']['team_name'],
                'total_points': data['manager_info']['total_points']
            })
        
        # מיון לפי נקודות
        standings.sort(key=lambda x: x['total_points'], reverse=True)
        
        # עדכון דירוג
        for idx, manager in enumerate(standings, 1):
            manager['rank'] = idx
        
        return standings
    
    def get_top_performers_this_week(self, top_n: int = 5) -> List[Dict]:
        """מצא את המנהלים עם הכי הרבה נקודות במחזור הנוכחי"""
        managers_data = self.load_latest_managers_data()
        
        weekly_scores = []
        for manager_id, data in managers_data.items():
            if data['history']['current']:
                latest_gw = data['history']['current'][-1]
                weekly_scores.append({
                    'player_name': data['manager_info']['player_name'],
                    'team_name': data['manager_info']['team_name'],
                    'gameweek': latest_gw['event'],
                    'points': latest_gw['points'],
                    'rank': latest_gw.get('rank', 'N/A')
                })
        
        weekly_scores.sort(key=lambda x: x['points'], reverse=True)
        return weekly_scores[:top_n]
    
    def get_most_captained_players(self) -> List[Dict]:
        """מצא את השחקנים הכי פופולריים לקפטן בליגה"""
        managers_data = self.load_latest_managers_data()
        bootstrap_data = self.load_latest_bootstrap_data()
        
        # מפה של ID שחקן לשם
        players_map = {p['id']: p['web_name'] for p in bootstrap_data['elements']}
        
        captain_counts = {}
        for manager_id, data in managers_data.items():
            picks = data['current_picks']['picks']
            for pick in picks:
                if pick['is_captain']:
                    player_id = pick['element']
                    player_name = players_map.get(player_id, f"Unknown ({player_id})")
                    captain_counts[player_name] = captain_counts.get(player_name, 0) + 1
        
        result = [
            {'player': player, 'count': count}
            for player, count in captain_counts.items()
        ]
        result.sort(key=lambda x: x['count'], reverse=True)
        
        return result
    
    def get_most_owned_players(self) -> List[Dict]:
        """מצא את השחקנים הכי פופולריים בליגה"""
        managers_data = self.load_latest_managers_data()
        bootstrap_data = self.load_latest_bootstrap_data()
        
        players_map = {p['id']: p['web_name'] for p in bootstrap_data['elements']}
        
        ownership_counts = {}
        for manager_id, data in managers_data.items():
            picks = data['current_picks']['picks']
            for pick in picks:
                player_id = pick['element']
                player_name = players_map.get(player_id, f"Unknown ({player_id})")
                ownership_counts[player_name] = ownership_counts.get(player_name, 0) + 1
        
        result = [
            {'player': player, 'owned_by': count}
            for player, count in ownership_counts.items()
        ]
        result.sort(key=lambda x: x['owned_by'], reverse=True)
        
        return result[:20]  # Top 20
    
    def get_transfer_activity(self) -> List[Dict]:
        """נתח את פעילות ההעברות"""
        managers_data = self.load_latest_managers_data()
        
        transfer_data = []
        for manager_id, data in managers_data.items():
            if data['history']['current']:
                latest_gw = data['history']['current'][-1]
                transfer_data.append({
                    'player_name': data['manager_info']['player_name'],
                    'transfers': latest_gw.get('event_transfers', 0),
                    'cost': latest_gw.get('event_transfers_cost', 0),
                    'bank': latest_gw.get('bank', 0) / 10  # מחולק ב-10 כי זה מיוצג בעשיריות
                })
        
        return transfer_data
    
    def print_league_report(self):
        """הדפס דוח מלא של הליגה"""
        print("\n" + "="*70)
        print("📊 FPL League Analysis Report | דוח ניתוח ליגת FPL")
        print("="*70 + "\n")
        
        # 1. טבלת דירוג
        print("🏆 League Standings | דירוג הליגה")
        print("-" * 70)
        standings = self.get_league_standings()
        print(f"{'Rank':<6} {'Manager':<25} {'Team':<25} {'Points':<10}")
        print("-" * 70)
        for manager in standings:
            print(f"{manager['rank']:<6} {manager['player_name']:<25} "
                  f"{manager['team_name']:<25} {manager['total_points']:<10}")
        
        # 2. ביצועים במחזור הנוכחי
        print("\n\n⚡ Top Performers This Week | מובילים במחזור הנוכחי")
        print("-" * 70)
        top_gw = self.get_top_performers_this_week()
        if top_gw:
            print(f"Gameweek: {top_gw[0]['gameweek']}")
            print(f"{'Manager':<30} {'Team':<25} {'Points':<10}")
            print("-" * 70)
            for manager in top_gw:
                print(f"{manager['player_name']:<30} {manager['team_name']:<25} "
                      f"{manager['points']:<10}")
        
        # 3. קפטנים פופולריים
        print("\n\n👑 Most Popular Captains | קפטנים פופולריים")
        print("-" * 70)
        captains = self.get_most_captained_players()
        print(f"{'Player':<40} {'Times Captained':<20}")
        print("-" * 70)
        for cap in captains[:10]:
            print(f"{cap['player']:<40} {cap['count']:<20}")
        
        # 4. שחקנים בבעלות
        print("\n\n⭐ Most Owned Players | שחקנים בבעלות הגבוהה")
        print("-" * 70)
        owned = self.get_most_owned_players()
        print(f"{'Player':<40} {'Owned By':<20}")
        print("-" * 70)
        for player in owned[:10]:
            print(f"{player['player']:<40} {player['owned_by']} managers")
        
        # 5. פעילות העברות
        print("\n\n🔄 Transfer Activity | פעילות העברות")
        print("-" * 70)
        transfers = self.get_transfer_activity()
        active_transferers = [t for t in transfers if t['transfers'] > 0]
        if active_transferers:
            print(f"{'Manager':<30} {'Transfers':<15} {'Cost':<10} {'Bank':<10}")
            print("-" * 70)
            for t in sorted(active_transferers, key=lambda x: x['transfers'], reverse=True):
                print(f"{t['player_name']:<30} {t['transfers']:<15} "
                      f"{t['cost']:<10} £{t['bank']:.1f}m")
        else:
            print("No transfers made this week")
        
        print("\n" + "="*70)
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")


def main():
    """הפעל ניתוח דוגמה"""
    try:
        analyzer = FPLAnalyzer()
        analyzer.print_league_report()
        
        print("\n💡 Tip: You can extend this script with more analyses!")
        print("טיפ: אפשר להרחיב את הסקריפט עם עוד ניתוחים!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please run fpl_data_collector.py first to collect data.")
        print("בבקשה הרץ קודם את fpl_data_collector.py כדי לאסוף דאטה.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
