#!/usr/bin/env python3
"""
FPL Transfer Recommendations Engine
מנוע המלצות להעברות - קבל המלצות קונקרטיות!
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class TransferRecommendationEngine:
    def __init__(self, data_dir: str = "fpl_data"):
        self.data_dir = Path(data_dir)
        self.bootstrap_data = self.load_latest_bootstrap_data()
        self.managers_data = self.load_latest_managers_data()
        
        self.players_map = {p['id']: p for p in self.bootstrap_data['elements']}
        self.teams_map = {t['id']: t['name'] for t in self.bootstrap_data['teams']}
    
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
    
    def get_my_team(self, manager_name: str = None) -> Dict:
        """קבל את הקבוצה שלך"""
        if manager_name:
            for manager_id, data in self.managers_data.items():
                if manager_name.lower() in data['manager_info']['player_name'].lower():
                    return data
        
        # אם לא מצאנו, קח את הראשון
        return list(self.managers_data.values())[0]
    
    def calculate_player_score(self, player: Dict) -> float:
        """חשב ציון איכות לשחקן על בסיס סטטיסטיקות"""
        score = 0.0
        
        # Form (משקל גבוה)
        form = float(player.get('form', 0))
        score += form * 3
        
        # Points per game
        ppg = float(player.get('points_per_game', 0))
        score += ppg * 2
        
        # ICT Index (Influence, Creativity, Threat)
        ict = float(player.get('ict_index', 0))
        score += ict / 10
        
        # Selected by % (פופולריות)
        selected = float(player.get('selected_by_percent', 0))
        score += selected / 5
        
        # Minutes played %
        minutes = player.get('minutes', 0)
        score += (minutes / 90) / 10
        
        return score
    
    def find_best_replacements(self, player_to_replace: Dict, budget: float, 
                               position: str, exclude_ids: List[int]) -> List[Dict]:
        """מצא תחליפים אופטימליים לשחקן"""
        position_map = {'GKP': 1, 'DEF': 2, 'MID': 3, 'FWD': 4}
        position_id = position_map.get(position, 0)
        
        candidates = []
        for player in self.bootstrap_data['elements']:
            if player['element_type'] != position_id:
                continue
            if player['id'] in exclude_ids:
                continue
            
            price = player['now_cost'] / 10
            if price > budget:
                continue
            
            # חשב ציון
            score = self.calculate_player_score(player)
            
            candidates.append({
                'id': player['id'],
                'name': player['web_name'],
                'full_name': f"{player['first_name']} {player['second_name']}",
                'team': self.teams_map.get(player['team'], 'Unknown'),
                'price': price,
                'form': float(player.get('form', 0)),
                'total_points': player['total_points'],
                'ppg': float(player.get('points_per_game', 0)),
                'selected_by': float(player.get('selected_by_percent', 0)),
                'score': score,
                'status': player.get('status', 'a')  # a=available, i=injured, etc.
            })
        
        # מיון לפי ציון
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:10]
    
    def get_transfer_recommendations(self, manager_name: str = None) -> Dict:
        """קבל המלצות העברות ממוקדות"""
        my_team = self.get_my_team(manager_name)
        
        current_picks = my_team['current_picks']['picks']
        my_player_ids = [pick['element'] for pick in current_picks]
        
        # חשב תקציב זמין
        latest_history = my_team['history']['current'][-1]
        bank = latest_history.get('bank', 0) / 10
        
        print(f"\n💼 Your Budget: £{bank}m in the bank\n")
        
        recommendations = {
            'underperformers': [],
            'suggested_transfers': []
        }
        
        # מצא שחקנים חלשים
        my_players = []
        for pick in current_picks:
            player = self.players_map.get(pick['element'])
            if player:
                score = self.calculate_player_score(player)
                my_players.append({
                    'id': player['id'],
                    'name': player['web_name'],
                    'position': ['GKP', 'DEF', 'MID', 'FWD'][player['element_type'] - 1],
                    'price': player['now_cost'] / 10,
                    'form': float(player.get('form', 0)),
                    'total_points': player['total_points'],
                    'score': score,
                    'is_starting': pick['position'] <= 11
                })
        
        # מיין לפי ציון (הכי נמוכים = candidates for transfer out)
        my_players.sort(key=lambda x: x['score'])
        
        # 3 השחקנים הכי חלשים
        underperformers = my_players[:3]
        recommendations['underperformers'] = underperformers
        
        # מצא תחליפים לכל אחד
        for underperformer in underperformers:
            budget_for_replacement = bank + underperformer['price']
            
            replacements = self.find_best_replacements(
                underperformer,
                budget_for_replacement,
                underperformer['position'],
                my_player_ids
            )
            
            if replacements:
                recommendations['suggested_transfers'].append({
                    'out': underperformer,
                    'in_options': replacements[:5]  # Top 5 options
                })
        
        return recommendations
    
    def print_transfer_report(self, manager_name: str = None):
        """הדפס דוח המלצות העברות"""
        print("\n" + "="*80)
        print("🔄 TRANSFER RECOMMENDATIONS REPORT")
        print("דוח המלצות העברות")
        print("="*80 + "\n")
        
        recs = self.get_transfer_recommendations(manager_name)
        
        # 1. Underperformers
        print("⚠️  UNDERPERFORMING PLAYERS - שחקנים חלשים בקבוצה שלך")
        print("-" * 80)
        print(f"{'Player':<20} {'Pos':<6} {'Price':<10} {'Form':<8} {'Points':<8} {'Score':<8}")
        print("-" * 80)
        
        for player in recs['underperformers']:
            print(f"{player['name']:<20} {player['position']:<6} £{player['price']:<9.1f}m "
                  f"{player['form']:<8.1f} {player['total_points']:<8} {player['score']:<8.1f}")
        
        # 2. Suggested Transfers
        print("\n\n💡 SUGGESTED TRANSFERS - המלצות העברות")
        print("=" * 80)
        
        for i, transfer in enumerate(recs['suggested_transfers'], 1):
            out_player = transfer['out']
            print(f"\nOption {i}: Transfer OUT {out_player['name']} ({out_player['position']}) - £{out_player['price']}m")
            print("-" * 80)
            print(f"{'Transfer IN':<20} {'Team':<15} {'Price':<10} {'Form':<8} {'PPG':<8} {'Own%':<8}")
            print("-" * 80)
            
            for replacement in transfer['in_options']:
                status_icon = "✅" if replacement['status'] == 'a' else "⚠️ "
                print(f"{status_icon} {replacement['name']:<18} {replacement['team']:<15} "
                      f"£{replacement['price']:<9.1f}m {replacement['form']:<8.1f} "
                      f"{replacement['ppg']:<8.1f} {replacement['selected_by']:<8.1f}%")
            
            # חשב פוטנציאל רווח/הפסד
            if transfer['in_options']:
                best_option = transfer['in_options'][0]
                price_diff = best_option['price'] - out_player['price']
                form_diff = best_option['form'] - out_player['form']
                
                print(f"\n   💰 Price difference: {'+' if price_diff >= 0 else ''}{price_diff:.1f}m")
                print(f"   📊 Form difference: {'+' if form_diff >= 0 else ''}{form_diff:.1f}")
        
        print("\n" + "="*80)
        print("💡 TIP: Don't take hits unless the transfer will gain you 8+ points!")
        print("💡 טיפ: אל תקח hits אלא אם ההעברה תרוויח לך 8+ נקודות!")
        print("="*80 + "\n")


def main():
    import sys
    
    try:
        engine = TransferRecommendationEngine()
        
        # אם יש שם מנהל בארגומנטים
        manager_name = None
        if len(sys.argv) > 1:
            manager_name = " ".join(sys.argv[1:])
            print(f"\n🔍 Searching for manager: {manager_name}")
        
        engine.print_transfer_report(manager_name)
        
        print("\n📝 Usage tip:")
        print("   python transfer_recommendations.py \"Your Name\"")
        print("   python transfer_recommendations.py")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nPlease run fpl_data_collector.py first!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
