#!/usr/bin/env python3
"""
FPL Captain Selection Helper
עוזר לבחירת קפטן - הבחירה החשובה ביותר כל שבוע!
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import Counter


class CaptainSelector:
    def __init__(self, data_dir: str = "fpl_data"):
        self.data_dir = Path(data_dir)
        self.bootstrap_data = self.load_latest_bootstrap_data()
        self.managers_data = self.load_latest_managers_data()
        
        self.players_map = {p['id']: p for p in self.bootstrap_data['elements']}
        self.teams_map = {t['id']: t for t in self.bootstrap_data['teams']}
    
    def load_latest_bootstrap_data(self) -> Dict:
        bootstrap_files = list(self.data_dir.glob("bootstrap_data_*.json"))
        if not bootstrap_files:
            raise FileNotFoundError("לא נמצאו קבצי bootstrap")
        latest_file = max(bootstrap_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_latest_managers_data(self) -> Dict:
        manager_files = list(self.data_dir.glob("managers_detailed_*.json"))
        if not manager_files:
            raise FileNotFoundError("לא נמצאו קבצי מנהלים")
        latest_file = max(manager_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_next_fixtures(self, team_id: int, num_games: int = 3) -> List[Dict]:
        """קבל את המשחקים הבאים של קבוצה"""
        fixtures = []
        
        for event in self.bootstrap_data['events']:
            if event['is_next'] or event['is_current']:
                current_gw = event['id']
                break
        
        # זה יותר מורכב - צריך API נפרד לfixtures
        # לעת עתה נחזיר placeholder
        return [{'opponent': 'TBD', 'difficulty': 3}] * num_games
    
    def analyze_captain_options(self, manager_name: str = None) -> List[Dict]:
        """נתח אופציות לקפטן מהקבוצה שלך"""
        
        # מצא את המנהל
        my_team = None
        if manager_name:
            for manager_id, data in self.managers_data.items():
                if manager_name.lower() in data['manager_info']['player_name'].lower():
                    my_team = data
                    break
        
        if not my_team:
            my_team = list(self.managers_data.values())[0]
        
        my_picks = my_team['current_picks']['picks']
        
        captain_candidates = []
        for pick in my_picks:
            if pick['position'] > 11:  # רק שחקנים בהרכב הפותח
                continue
            
            player = self.players_map.get(pick['element'])
            if not player:
                continue
            
            # חשב ציון קפטן
            captain_score = 0.0
            
            # Form (משקל הכי גבוה)
            form = float(player.get('form', 0))
            captain_score += form * 5
            
            # Points per game
            ppg = float(player.get('points_per_game', 0))
            captain_score += ppg * 3
            
            # Bonus points (שחקנים שמקבלים הרבה בונוסים)
            bonus = player.get('bonus', 0)
            captain_score += bonus / 2
            
            # Goals + Assists potential
            goals = player.get('goals_scored', 0)
            assists = player.get('assists', 0)
            captain_score += (goals + assists) / 3
            
            # ICT Index
            ict = float(player.get('ict_index', 0))
            captain_score += ict / 20
            
            captain_candidates.append({
                'id': player['id'],
                'name': player['web_name'],
                'full_name': f"{player['first_name']} {player['second_name']}",
                'team': self.teams_map.get(player['team'], {}).get('name', 'Unknown'),
                'position': ['GKP', 'DEF', 'MID', 'FWD'][player['element_type'] - 1],
                'form': form,
                'ppg': ppg,
                'total_points': player['total_points'],
                'goals': goals,
                'assists': assists,
                'bonus': bonus,
                'captain_score': captain_score,
                'is_captain': pick['is_captain']
            })
        
        # מיין לפי ציון קפטן
        captain_candidates.sort(key=lambda x: x['captain_score'], reverse=True)
        return captain_candidates
    
    def get_league_captain_choices(self) -> List[Dict]:
        """מה הליגה בוחרת בקפטן?"""
        captain_counter = Counter()
        
        for manager_id, data in self.managers_data.items():
            for pick in data['current_picks']['picks']:
                if pick['is_captain']:
                    captain_counter[pick['element']] += 1
        
        captain_stats = []
        for player_id, count in captain_counter.most_common():
            player = self.players_map.get(player_id)
            if player:
                captain_stats.append({
                    'name': player['web_name'],
                    'team': self.teams_map.get(player['team'], {}).get('name', 'Unknown'),
                    'captained_by': count,
                    'captaincy_pct': (count / len(self.managers_data)) * 100
                })
        
        return captain_stats
    
    def print_captain_report(self, manager_name: str = None):
        """הדפס דוח בחירת קפטן"""
        print("\n" + "="*80)
        print("👑 CAPTAIN SELECTION REPORT")
        print("דוח בחירת קפטן")
        print("="*80 + "\n")
        
        # 1. Your captain options
        print("🎯 YOUR CAPTAIN OPTIONS - האופציות שלך לקפטן")
        print("-" * 80)
        
        my_options = self.analyze_captain_options(manager_name)
        
        print(f"{'Player':<25} {'Pos':<5} {'Form':<8} {'PPG':<8} {'G+A':<8} {'Score':<10} {'Current':<10}")
        print("-" * 80)
        
        for option in my_options[:10]:
            is_current = "👑 YES" if option['is_captain'] else ""
            print(f"{option['name']:<25} {option['position']:<5} {option['form']:<8.1f} "
                  f"{option['ppg']:<8.1f} {option['goals'] + option['assists']:<8} "
                  f"{option['captain_score']:<10.1f} {is_current:<10}")
        
        # 2. League captain choices
        print("\n\n📊 LEAGUE CAPTAIN CHOICES - מה הליגה בוחרת")
        print("-" * 80)
        
        league_choices = self.get_league_captain_choices()
        
        print(f"{'Player':<30} {'Team':<20} {'Captained By':<15} {'%':<10}")
        print("-" * 80)
        
        for choice in league_choices[:10]:
            print(f"{choice['name']:<30} {choice['team']:<20} "
                  f"{choice['captained_by']:<15} {choice['captaincy_pct']:<10.1f}%")
        
        # 3. Recommendations
        print("\n\n💡 RECOMMENDATIONS - המלצות")
        print("=" * 80)
        
        if my_options:
            top_pick = my_options[0]
            differential_pick = None
            
            # מצא differential captain (לא פופולרי אבל טוב)
            for option in my_options[1:4]:
                is_popular = any(
                    choice['name'] == option['name'] and choice['captaincy_pct'] > 30
                    for choice in league_choices[:3]
                )
                if not is_popular and option['captain_score'] > 30:
                    differential_pick = option
                    break
            
            print(f"\n✅ SAFE PICK (Template Captain):")
            print(f"   {top_pick['name']} - Form: {top_pick['form']}, PPG: {top_pick['ppg']}")
            print(f"   Reason: Best overall stats in your team")
            
            if differential_pick:
                print(f"\n🎲 DIFFERENTIAL PICK (Risky but rewarding):")
                print(f"   {differential_pick['name']} - Form: {differential_pick['form']}, "
                      f"PPG: {differential_pick['ppg']}")
                print(f"   Reason: Less popular but strong stats - could give you an edge!")
            
            # Triple Captain suggestion
            if my_options[0]['captain_score'] > 50:
                print(f"\n🔥 TRIPLE CAPTAIN CONSIDERATION:")
                print(f"   {my_options[0]['name']} is in AMAZING form!")
                print(f"   Consider using Triple Captain chip if available")
        
        print("\n" + "="*80)
        print("💡 Remember: Captain choice can make or break your gameweek!")
        print("💡 זכור: בחירת הקפטן יכולה לעשות או לשבור את המחזור שלך!")
        print("="*80 + "\n")


def main():
    import sys
    
    try:
        selector = CaptainSelector()
        
        manager_name = None
        if len(sys.argv) > 1:
            manager_name = " ".join(sys.argv[1:])
            print(f"\n🔍 Analyzing captain options for: {manager_name}")
        
        selector.print_captain_report(manager_name)
        
        print("\n📝 Usage:")
        print("   python captain_selector.py \"Your Name\"")
        print("   python captain_selector.py")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nPlease run fpl_data_collector.py first!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
