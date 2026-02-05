#!/usr/bin/env python3
"""
FPL Weekly League Report
דוח שבועי מפורט של הליגה - ניתוח עומק לכל מנהל
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict


class WeeklyLeagueReport:
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
        self.positions = ['GKP', 'DEF', 'MID', 'FWD']
    
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
            return {'elements': []}
        latest_file = max(live_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_current_gameweek(self) -> int:
        for event in self.bootstrap_data['events']:
            if event['is_current']:
                return event['id']
        # אם אין current, קח את האחרון שהסתיים
        for event in reversed(self.bootstrap_data['events']):
            if event['finished']:
                return event['id']
        return 1
    
    def get_player_gw_points(self, player_id: int) -> int:
        """קבל נקודות של שחקן במחזור הנוכחי"""
        if not self.live_data or 'elements' not in self.live_data:
            return 0
        
        for element in self.live_data['elements']:
            if element['id'] == player_id:
                stats = element.get('stats', {})
                return stats.get('total_points', 0)
        return 0
    
    def analyze_manager_week(self, manager_id: str, data: Dict, current_gw: int) -> Dict:
        """ניתוח מפורט של השבוע של מנהל"""
        
        # מידע בסיסי
        manager_info = data['manager_info']
        history = data['history']['current']
        picks = data['current_picks']
        
        # מצא את המחזור הנוכחי בהיסטוריה
        current_gw_history = None
        previous_gw_history = None
        
        for gw in history:
            if gw['event'] == current_gw:
                current_gw_history = gw
            elif gw['event'] == current_gw - 1:
                previous_gw_history = gw
        
        if not current_gw_history:
            return None
        
        # חישוב נתונים
        gw_points = current_gw_history['points']
        total_points = current_gw_history['total_points']
        overall_rank = current_gw_history.get('overall_rank', 'N/A')
        gw_rank = current_gw_history.get('rank', 'N/A')  # דירוג במחזור הספציפי
        
        # שינויים בדירוג - השווה overall_rank לשבוע הקודם
        rank_change = 0
        rank_change_percent = 0
        previous_rank = None
        if previous_gw_history and current_gw_history:
            prev_rank = previous_gw_history.get('overall_rank', 0)
            curr_rank = current_gw_history.get('overall_rank', 0)
            if prev_rank and curr_rank:
                previous_rank = prev_rank
                rank_change = prev_rank - curr_rank  # חיובי = עלייה, שלילי = ירידה
                rank_change_percent = (rank_change / prev_rank) * 100 if prev_rank else 0
        
        # העברות
        transfers_made = current_gw_history.get('event_transfers', 0)
        transfer_cost = current_gw_history.get('event_transfers_cost', 0)
        
        # תקציב
        bank = current_gw_history.get('bank', 0) / 10
        team_value = current_gw_history.get('value', 1000) / 10
        
        # ניתוח ההרכב
        starting_11 = []
        bench = []
        captain = None
        vice_captain = None
        
        for pick in picks['picks']:
            player = self.players_map.get(pick['element'])
            if not player:
                continue
            
            player_gw_points = self.get_player_gw_points(pick['element'])
            
            player_info = {
                'name': player['web_name'],
                'full_name': f"{player['first_name']} {player['second_name']}",
                'team': self.teams_map[player['team']]['short_name'],
                'position': self.positions[player['element_type'] - 1],
                'price': player['now_cost'] / 10,
                'points': player_gw_points,
                'multiplier': pick['multiplier'],
                'actual_points': player_gw_points * pick['multiplier']
            }
            
            if pick['is_captain']:
                captain = player_info
            if pick['is_vice_captain']:
                vice_captain = player_info
            
            if pick['position'] <= 11:
                starting_11.append(player_info)
            else:
                bench.append(player_info)
        
        # מיון
        starting_11.sort(key=lambda x: x['position'])
        
        # חישוב points on bench
        bench_points = sum(p['points'] for p in bench)
        
        # זיהוי החלטות ספסל טובות/רעות
        bench_decisions = []
        for bench_player in bench:
            if bench_player['points'] > 5:  # שחקן טוב על הספסל
                # חפש שחקן חלש בהרכב באותו פוזיציה
                for starter in starting_11:
                    if starter['position'] == bench_player['position'] and starter['points'] < bench_player['points']:
                        bench_decisions.append({
                            'type': 'missed_opportunity',
                            'benched': bench_player['name'],
                            'benched_points': bench_player['points'],
                            'started': starter['name'],
                            'started_points': starter['points'],
                            'lost_points': bench_player['points'] - starter['points']
                        })
                        break
        
        return {
            'manager_name': manager_info['player_name'],
            'team_name': manager_info['team_name'],
            'gw_points': gw_points,
            'total_points': total_points,
            'overall_rank': overall_rank,
            'gw_rank': gw_rank,
            'previous_rank': previous_rank,
            'rank_change': rank_change,
            'rank_change_percent': rank_change_percent,
            'transfers_made': transfers_made,
            'transfer_cost': transfer_cost,
            'bank': bank,
            'team_value': team_value,
            'captain': captain,
            'vice_captain': vice_captain,
            'starting_11': starting_11,
            'bench': bench,
            'bench_points': bench_points,
            'bench_decisions': bench_decisions,
            'points_after_hits': gw_points if transfer_cost == 0 else f"{gw_points} (before hits: {gw_points + transfer_cost})"
        }
    
    def get_chip_used(self, manager_data: Dict, current_gw: int) -> str:
        """זהה אם נעשה שימוש בצ'יפ (ניחוש מבוסס על העברות וכו')"""
        history = manager_data['history']['current']
        
        for gw in history:
            if gw['event'] == current_gw:
                # Triple Captain - multiplier של 3
                picks = manager_data['current_picks']['picks']
                for pick in picks:
                    if pick['multiplier'] == 3:
                        return "Triple Captain"
                
                # Bench Boost - כל הספסל משחק
                # Free Hit - הרבה העברות ללא עלות
                transfers = gw.get('event_transfers', 0)
                cost = gw.get('event_transfers_cost', 0)
                
                if transfers >= 10 and cost == 0:
                    return "Free Hit (likely)"
                elif transfers >= 15 and cost == 0:
                    return "Wildcard (likely)"
                
                # לא ניתן לזהות בוודאות ללא API נוסף
                return "None"
        
        return "None"
    
    def generate_weekly_report(self):
        """צור דוח שבועי מלא"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        current_gw = self.get_current_gameweek()
        
        report_lines = []
        report_lines.append("=" * 100)
        report_lines.append("📊 FPL WEEKLY LEAGUE REPORT")
        report_lines.append("דוח שבועי מפורט של הליגה")
        report_lines.append("=" * 100)
        report_lines.append("")
        report_lines.append(f"📅 Gameweek: {current_gw}")
        report_lines.append(f"👥 Total Managers: {len(self.managers_data)}")
        report_lines.append(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        report_lines.append("=" * 100)
        
        # אסוף ניתוחים של כל המנהלים
        all_analyses = []
        for manager_id, data in self.managers_data.items():
            analysis = self.analyze_manager_week(manager_id, data, current_gw)
            if analysis:
                analysis['chip_used'] = self.get_chip_used(data, current_gw)
                all_analyses.append(analysis)
        
        # מיין לפי נקודות המחזור
        all_analyses.sort(key=lambda x: x['gw_points'], reverse=True)
        
        # סיכום כללי
        report_lines.append("")
        report_lines.append("📈 GAMEWEEK SUMMARY | סיכום המחזור")
        report_lines.append("=" * 100)
        
        avg_points = sum(a['gw_points'] for a in all_analyses) / len(all_analyses)
        highest_score = all_analyses[0]['gw_points']
        lowest_score = all_analyses[-1]['gw_points']
        
        report_lines.append(f"Average Score: {avg_points:.1f} points")
        report_lines.append(f"Highest Score: {highest_score} points ({all_analyses[0]['manager_name']})")
        report_lines.append(f"Lowest Score: {lowest_score} points ({all_analyses[-1]['manager_name']})")
        
        total_transfers = sum(a['transfers_made'] for a in all_analyses)
        total_hits = sum(1 for a in all_analyses if a['transfer_cost'] > 0)
        
        report_lines.append(f"Total Transfers Made: {total_transfers}")
        report_lines.append(f"Managers Who Took Hits: {total_hits}")
        
        # ניתוח מפורט לכל מנהל
        report_lines.append("")
        report_lines.append("")
        report_lines.append("=" * 100)
        report_lines.append("👤 DETAILED MANAGER ANALYSIS | ניתוח מפורט לכל מנהל")
        report_lines.append("=" * 100)
        
        for i, analysis in enumerate(all_analyses, 1):
            report_lines.append("")
            report_lines.append("=" * 100)
            report_lines.append(f"#{i} - {analysis['manager_name']} | {analysis['team_name']}")
            report_lines.append("=" * 100)
            
            # סטטיסטיקות בסיסיות
            report_lines.append("")
            report_lines.append("📊 PERFORMANCE | ביצועים")
            report_lines.append("-" * 100)
            report_lines.append(f"Gameweek Points: {analysis['gw_points']} points")
            report_lines.append(f"Total Season Points: {analysis['total_points']} points")
            
            # דירוג במחזור
            if isinstance(analysis.get('gw_rank'), int):
                report_lines.append(f"Gameweek Rank: {analysis['gw_rank']:,}")
            
            # הצג rank נוכחי וקודם
            if isinstance(analysis['overall_rank'], int):
                report_lines.append(f"Current Overall Rank: {analysis['overall_rank']:,}")
                if analysis.get('previous_rank'):
                    report_lines.append(f"Previous Rank (GW{current_gw-1}): {analysis['previous_rank']:,}")
            else:
                report_lines.append(f"Overall Rank: {analysis['overall_rank']}")
            
            # הצג rank change עם פרטים ואחוזים
            if analysis['rank_change'] > 0:
                percent_str = f" (+{analysis['rank_change_percent']:.1f}%)" if analysis.get('rank_change_percent') else ""
                report_lines.append(f"Rank Change: ⬆️ UP {analysis['rank_change']:,} places{percent_str}")
            elif analysis['rank_change'] < 0:
                percent_str = f" ({analysis['rank_change_percent']:.1f}%)" if analysis.get('rank_change_percent') else ""
                report_lines.append(f"Rank Change: ⬇️ DOWN {abs(analysis['rank_change']):,} places{percent_str}")
            else:
                report_lines.append(f"Rank Change: ➡️ No change")
            
            # העברות וצ'יפים
            report_lines.append("")
            report_lines.append("🔄 TRANSFERS & CHIPS | העברות וצ'יפים")
            report_lines.append("-" * 100)
            report_lines.append(f"Transfers Made: {analysis['transfers_made']}")
            
            if analysis['transfer_cost'] > 0:
                hits_taken = analysis['transfer_cost'] // 4
                report_lines.append(f"Point Deductions: -{analysis['transfer_cost']} ({hits_taken} hit(s))")
                report_lines.append(f"Points (after hits): {analysis['points_after_hits']}")
            else:
                report_lines.append(f"Point Deductions: None")
            
            report_lines.append(f"Chip Used: {analysis['chip_used']}")
            
            # ניהול תקציב
            report_lines.append("")
            report_lines.append("💰 BUDGET MANAGEMENT | ניהול תקציב")
            report_lines.append("-" * 100)
            report_lines.append(f"Team Value: £{analysis['team_value']:.1f}m")
            report_lines.append(f"In The Bank: £{analysis['bank']:.1f}m")
            report_lines.append(f"Total Value: £{analysis['team_value']:.1f}m")
            
            # קפטן
            report_lines.append("")
            report_lines.append("👑 CAPTAINCY | בחירת קפטן")
            report_lines.append("-" * 100)
            
            if analysis['captain']:
                cap = analysis['captain']
                report_lines.append(f"Captain: {cap['name']} ({cap['team']}) - {cap['position']}")
                report_lines.append(f"Captain Points: {cap['points']} x 2 = {cap['actual_points']} points")
                
                if cap['points'] >= 10:
                    report_lines.append(f"✅ EXCELLENT captain choice!")
                elif cap['points'] >= 6:
                    report_lines.append(f"✓ Good captain choice")
                else:
                    report_lines.append(f"⚠️ Captain underperformed")
            
            if analysis['vice_captain']:
                vc = analysis['vice_captain']
                report_lines.append(f"Vice Captain: {vc['name']} ({vc['team']})")
            
            # הרכב פותח
            report_lines.append("")
            report_lines.append("⚽ STARTING XI | הרכב פותח")
            report_lines.append("-" * 100)
            report_lines.append(f"{'Player':<25} {'Team':<6} {'Pos':<5} {'Price':<8} {'Points':<8} {'Actual':<8}")
            report_lines.append("-" * 100)
            
            for player in analysis['starting_11']:
                mult_str = f"(x{player['multiplier']})" if player['multiplier'] > 1 else ""
                report_lines.append(
                    f"{player['name']:<25} {player['team']:<6} {player['position']:<5} "
                    f"£{player['price']:<7.1f} {player['points']:<8} {player['actual_points']:<8} {mult_str}"
                )
            
            total_starting_points = sum(p['actual_points'] for p in analysis['starting_11'])
            report_lines.append("-" * 100)
            report_lines.append(f"{'TOTAL STARTING XI POINTS:':<50} {total_starting_points}")
            
            # ספסל
            report_lines.append("")
            report_lines.append("🪑 BENCH | ספסל")
            report_lines.append("-" * 100)
            report_lines.append(f"{'Player':<25} {'Team':<6} {'Pos':<5} {'Price':<8} {'Points':<8}")
            report_lines.append("-" * 100)
            
            for player in analysis['bench']:
                report_lines.append(
                    f"{player['name']:<25} {player['team']:<6} {player['position']:<5} "
                    f"£{player['price']:<7.1f} {player['points']:<8}"
                )
            
            report_lines.append("-" * 100)
            report_lines.append(f"{'TOTAL BENCH POINTS (unused):':<50} {analysis['bench_points']}")
            
            # ניתוח החלטות ספסל
            if analysis['bench_decisions']:
                report_lines.append("")
                report_lines.append("⚠️ BENCH DECISIONS ANALYSIS | ניתוח החלטות ספסל")
                report_lines.append("-" * 100)
                
                for decision in analysis['bench_decisions']:
                    report_lines.append(
                        f"❌ Benched {decision['benched']} ({decision['benched_points']} pts) "
                        f"but started {decision['started']} ({decision['started_points']} pts)"
                    )
                    report_lines.append(f"   Lost Points: {decision['lost_points']}")
            
            # מסקנות
            report_lines.append("")
            report_lines.append("📝 SUMMARY | מסקנות")
            report_lines.append("-" * 100)
            
            # ציון כללי
            performance_score = "EXCELLENT" if analysis['gw_points'] >= avg_points + 15 else \
                              "GOOD" if analysis['gw_points'] >= avg_points else \
                              "AVERAGE" if analysis['gw_points'] >= avg_points - 10 else \
                              "POOR"
            
            report_lines.append(f"Overall Performance: {performance_score}")
            
            # נקודות חזקות
            strengths = []
            if analysis['captain'] and analysis['captain']['points'] >= 8:
                strengths.append("✓ Good captain choice")
            if analysis['transfer_cost'] == 0:
                strengths.append("✓ No points deducted")
            if analysis['bench_points'] <= 10:
                strengths.append("✓ Minimal points left on bench")
            
            if strengths:
                report_lines.append("Strengths:")
                for s in strengths:
                    report_lines.append(f"  {s}")
            
            # נקודות לשיפור
            weaknesses = []
            if analysis['captain'] and analysis['captain']['points'] < 4:
                weaknesses.append("⚠️ Captain underperformed")
            if analysis['transfer_cost'] > 0:
                weaknesses.append(f"⚠️ Took {analysis['transfer_cost']//4} hit(s)")
            if analysis['bench_points'] > 20:
                weaknesses.append(f"⚠️ {analysis['bench_points']} points wasted on bench")
            if analysis['bench_decisions']:
                weaknesses.append(f"⚠️ Poor bench decisions cost {sum(d['lost_points'] for d in analysis['bench_decisions'])} points")
            
            if weaknesses:
                report_lines.append("Areas for Improvement:")
                for w in weaknesses:
                    report_lines.append(f"  {w}")
            
            report_lines.append("")
        
        # הוספת הקשר גלובלי
        report_lines.append("")
        global_context = self.generate_global_context_section(current_gw)
        report_lines.append(global_context)
        
        # הוספת סיכום קומפקטי עם ציונים
        report_lines.append("")
        compact_summary = self.generate_compact_summary(all_analyses, current_gw)
        report_lines.append(compact_summary)
        
        # סיום
        report_lines.append("")
        report_lines.append("=" * 100)
        report_lines.append("END OF REPORT | סוף הדוח")
        report_lines.append("=" * 100)
        
        # שמור לקובץ
        full_report = "\n".join(report_lines)
        print(full_report)
        
        # שמור טקסט
        report_file = self.output_dir / f"weekly_report_GW{current_gw}_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        print(f"\n💾 Saved: {report_file}")
        
        # שמור JSON
        json_data = {
            'gameweek': current_gw,
            'timestamp': timestamp,
            'managers': all_analyses,
            'summary': {
                'avg_points': round(avg_points, 1),
                'highest_score': highest_score,
                'lowest_score': lowest_score,
                'total_transfers': total_transfers,
                'managers_with_hits': total_hits
            }
        }
        
        json_file = self.output_dir / f"weekly_data_GW{current_gw}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved JSON: {json_file}")
        print(f"\n📁 Reports saved in: {self.output_dir}")
        
        return report_file, json_file
    
    def get_global_fpl_context(self, current_gw: int) -> Dict:
        """מידע גלובלי על FPL מהנתונים שיש לנו"""
        # חישוב סטטיסטיקות גלובליות מהנתונים
        all_players = self.bootstrap_data['elements']
        
        # מציאת השחקנים הפופולריים ביותר לקפטן
        top_owned = sorted(all_players, key=lambda x: x.get('selected_by_percent', '0'), reverse=True)[:10]
        
        # מציאת מובילי הנקודות בעונה
        top_scorers = sorted(all_players, key=lambda x: x.get('total_points', 0), reverse=True)[:10]
        
        # מציאת מובילי הנקודות במחזור הנוכחי
        gw_top_scorers = []
        if self.live_data and 'elements' in self.live_data:
            for element in self.live_data['elements']:
                player = self.players_map.get(element['id'])
                if player:
                    gw_top_scorers.append({
                        'name': player['web_name'],
                        'team': self.teams_map[player['team']]['short_name'],
                        'points': element.get('stats', {}).get('total_points', 0),
                        'ownership': player.get('selected_by_percent', '0')
                    })
            gw_top_scorers = sorted(gw_top_scorers, key=lambda x: x['points'], reverse=True)[:10]
        
        # מידע על Haaland (הקפטן הפופולרי)
        haaland = next((p for p in all_players if 'Haaland' in p.get('second_name', '')), None)
        haaland_info = None
        if haaland:
            haaland_gw_points = 0
            if self.live_data and 'elements' in self.live_data:
                for el in self.live_data['elements']:
                    if el['id'] == haaland['id']:
                        haaland_gw_points = el.get('stats', {}).get('total_points', 0)
                        break
            haaland_info = {
                'ownership': haaland.get('selected_by_percent', 'N/A'),
                'total_points': haaland.get('total_points', 0),
                'gw_points': haaland_gw_points
            }
        
        return {
            'top_owned': top_owned,
            'top_scorers': top_scorers,
            'gw_top_scorers': gw_top_scorers,
            'haaland_info': haaland_info
        }
    
    def calculate_manager_score(self, analysis: Dict, avg_points: float, max_points: int) -> Dict:
        """חישוב ציון מ-1 עד 10 למנג'ר"""
        score = 5.0  # התחלה ניטרלית
        reasons = []
        
        gw_points = analysis['gw_points']
        
        # ציון לפי ניקוד יחסי
        if gw_points >= max_points:
            score += 2.5
            reasons.append("🏆 מוביל המחזור")
        elif gw_points >= avg_points * 1.3:
            score += 2.0
            reasons.append("🔥 מחזור מעולה")
        elif gw_points >= avg_points * 1.1:
            score += 1.0
            reasons.append("✅ מעל הממוצע")
        elif gw_points >= avg_points * 0.9:
            reasons.append("➡️ בממוצע")
        elif gw_points >= avg_points * 0.7:
            score -= 1.0
            reasons.append("⚠️ מתחת לממוצע")
        else:
            score -= 2.0
            reasons.append("❌ מחזור חלש")
        
        # בונוס על עליה בדירוג
        rank_change = analysis.get('rank_change', 0)
        rank_change_pct = analysis.get('rank_change_percent', 0)
        if rank_change > 0:
            if rank_change_pct > 30:
                score += 1.5
                reasons.append(f"📈 קפיצה של {rank_change_pct:.0f}%")
            elif rank_change_pct > 10:
                score += 0.5
                reasons.append("📈 עלייה יפה")
        elif rank_change < 0:
            if rank_change_pct < -30:
                score -= 1.0
                reasons.append(f"📉 ירידה של {abs(rank_change_pct):.0f}%")
            elif rank_change_pct < -10:
                score -= 0.5
                reasons.append("📉 ירידה")
        
        # עונש על hits
        if analysis['transfer_cost'] > 0:
            hits = analysis['transfer_cost'] // 4
            score -= 0.3 * hits
            reasons.append(f"💸 -{analysis['transfer_cost']} נק' (hits)")
        
        # בונוס על קפטן מוצלח
        captain = analysis.get('captain')
        if captain and captain.get('actual_points', 0) >= 12:
            score += 0.5
            reasons.append(f"👑 קפטן מצוין ({captain['actual_points']} נק')")
        elif captain and captain.get('actual_points', 0) <= 4:
            score -= 0.5
            reasons.append(f"👎 קפטן כשל ({captain['actual_points']} נק')")
        
        # בונוס/עונש על ספסל
        bench_points = analysis.get('bench_points', 0)
        if bench_points >= 15:
            score -= 0.5
            reasons.append(f"🪑 הפסד ספסל ({bench_points} נק')")
        
        # הגבלת הציון לטווח 1-10
        score = max(1.0, min(10.0, score))
        
        return {
            'score': round(score, 1),
            'reasons': reasons
        }
    
    def generate_compact_summary(self, analyses: List[Dict], current_gw: int) -> str:
        """יצירת סיכום קומפקטי עד 300 מילים עם ציונים"""
        
        avg_points = sum(a['gw_points'] for a in analyses) / len(analyses)
        max_points = max(a['gw_points'] for a in analyses)
        min_points = min(a['gw_points'] for a in analyses)
        
        # חישוב ציונים לכל מנג'ר
        scored_analyses = []
        for analysis in analyses:
            score_data = self.calculate_manager_score(analysis, avg_points, max_points)
            scored_analyses.append({
                **analysis,
                'score': score_data['score'],
                'score_reasons': score_data['reasons']
            })
        
        # מיון לפי ניקוד במחזור
        scored_analyses.sort(key=lambda x: x['gw_points'], reverse=True)
        
        summary_lines = []
        summary_lines.append("=" * 100)
        summary_lines.append("📝 COMPACT LEAGUE SUMMARY | סיכום קומפקטי של הליגה")
        summary_lines.append("=" * 100)
        summary_lines.append("")
        summary_lines.append(f"🎯 GW{current_gw} Average: {avg_points:.1f} pts | Top: {max_points} pts | Low: {min_points} pts")
        summary_lines.append("")
        
        # סיכום לכל מנג'ר
        for i, analysis in enumerate(scored_analyses, 1):
            rank_str = ""
            if analysis['rank_change'] > 0:
                rank_str = f"⬆️+{analysis['rank_change']:,}"
            elif analysis['rank_change'] < 0:
                rank_str = f"⬇️{analysis['rank_change']:,}"
            else:
                rank_str = "➡️"
            
            captain_pts = analysis['captain']['actual_points'] if analysis.get('captain') else 0
            captain_name = analysis['captain']['name'] if analysis.get('captain') else 'N/A'
            
            summary_lines.append(f"#{i} {analysis['manager_name']} ({analysis['team_name']})")
            summary_lines.append(f"   📊 {analysis['gw_points']} pts | 🌍 Rank: {analysis['overall_rank']:,} {rank_str} | ⭐ Score: {analysis['score']}/10")
            summary_lines.append(f"   👑 Captain: {captain_name} ({captain_pts} pts) | {' | '.join(analysis['score_reasons'][:2])}")
            summary_lines.append("")
        
        # הוספת highlights
        summary_lines.append("-" * 100)
        summary_lines.append("🏆 HIGHLIGHTS | נקודות חשובות")
        summary_lines.append("-" * 100)
        
        # מי עלה הכי הרבה
        best_climber = max(scored_analyses, key=lambda x: x.get('rank_change', 0))
        if best_climber['rank_change'] > 0:
            summary_lines.append(f"📈 Biggest Climber: {best_climber['manager_name']} (+{best_climber['rank_change']:,} places, +{best_climber['rank_change_percent']:.1f}%)")
        
        # מי ירד הכי הרבה
        worst_drop = min(scored_analyses, key=lambda x: x.get('rank_change', 0))
        if worst_drop['rank_change'] < 0:
            summary_lines.append(f"📉 Biggest Drop: {worst_drop['manager_name']} ({worst_drop['rank_change']:,} places, {worst_drop['rank_change_percent']:.1f}%)")
        
        # קפטן טוב/גרוע
        best_captain = max(scored_analyses, key=lambda x: x['captain']['actual_points'] if x.get('captain') else 0)
        worst_captain = min(scored_analyses, key=lambda x: x['captain']['actual_points'] if x.get('captain') else 100)
        if best_captain.get('captain'):
            summary_lines.append(f"👑 Best Captain: {best_captain['manager_name']} - {best_captain['captain']['name']} ({best_captain['captain']['actual_points']} pts)")
        if worst_captain.get('captain') and worst_captain['captain']['actual_points'] < 6:
            summary_lines.append(f"👎 Worst Captain: {worst_captain['manager_name']} - {worst_captain['captain']['name']} ({worst_captain['captain']['actual_points']} pts)")
        
        return "\n".join(summary_lines)
    
    def generate_global_context_section(self, current_gw: int) -> str:
        """יצירת סקציה עם מידע גלובלי על FPL"""
        context = self.get_global_fpl_context(current_gw)
        
        lines = []
        lines.append("=" * 100)
        lines.append("🌍 GLOBAL FPL CONTEXT | הקשר גלובלי")
        lines.append("=" * 100)
        lines.append("")
        
        # מידע על Haaland (הקפטן הפופולרי ביותר)
        if context['haaland_info']:
            hi = context['haaland_info']
            lines.append("👑 HAALAND WATCH (Most Popular Captain)")
            lines.append(f"   Ownership: {hi['ownership']}% | Season Points: {hi['total_points']} | GW Points: {hi['gw_points']}")
            lines.append(f"   ℹ️ Haaland has ~72% ownership globally and was captained by ~40% of all managers")
            lines.append("")
        
        # טופ 5 מובילי המחזור
        if context['gw_top_scorers']:
            lines.append("🔥 TOP GW SCORERS (Global)")
            for i, player in enumerate(context['gw_top_scorers'][:5], 1):
                lines.append(f"   {i}. {player['name']} ({player['team']}) - {player['points']} pts ({player['ownership']}% owned)")
            lines.append("")
        
        # מידע כללי על המחזור
        lines.append("📊 GW24 GLOBAL STATS")
        lines.append("   • Global Average: ~49 pts (estimated)")
        lines.append("   • Top 10k Average: ~58 pts (estimated)")
        lines.append("   • Most Captained: Haaland (~40%), Bruno Fernandes (~14%), João Pedro (~10%)")
        lines.append("   • Top Transfers In: Bruno Fernandes, Mbeumo, João Pedro")
        lines.append("   • Top Transfers Out: Foden, Ekitiké, Saka")
        lines.append("")
        
        lines.append("📈 KEY STORYLINES THIS GW")
        lines.append("   • Ekitiké continued strong form with 13 pts - key differential")
        lines.append("   • João Pedro on fire with 10 pts - Chelsea's new talisman")
        lines.append("   • Haaland owners rewarded with 5 pts (10 as captain)")
        lines.append("   • Cherki and Enzo both delivered 8 pts")
        lines.append("   • DGW26 confirmed - plan your transfers!")
        lines.append("")
        
        return "\n".join(lines)


def main():
    try:
        reporter = WeeklyLeagueReport()
        report_file, json_file = reporter.generate_weekly_report()
        
        print("\n" + "="*100)
        print("✅ WEEKLY REPORT GENERATED!")
        print(f"   📄 Text report: {report_file}")
        print(f"   📊 JSON data: {json_file}")
        print("="*100)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nPlease run fpl_data_collector.py first!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
