#!/usr/bin/env python3
"""
FPL Weekly Summary - גרסה מתקדמת
סיכום שבועי חכם עם תחזיות AI ושליחה לוואטסאפ

תכונות:
- ביצועים מול הממוצע העולמי
- תחזיות למחזורים הבאים (עם Claude AI)
- המלצות העברות אישיות לכל מאמן
- ניתוח קפטנים ודיפרנשיאלים
- שליחה אוטומטית לוואטסאפ דרך Twilio
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

# אופציונלי - ייובאו רק אם קיימים
try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


@dataclass
class ManagerAnalysis:
    """ניתוח מפורט של מאמן"""
    name: str
    team_name: str
    gw_points: int
    total_points: int
    overall_rank: int
    rank_change: int
    rank_change_pct: float
    transfers: int
    hits: int
    bench_points: int
    bank: float
    team_value: float
    captain_name: str
    captain_points: int
    starting_xi: List[Dict]
    bench: List[Dict]
    chips_remaining: List[str]
    chips_used: List[str]
    vs_world_avg: float
    vs_world_avg_5gw: float
    form_trend: str  # "עולה", "יורד", "יציב"
    weakest_players: List[Dict]
    transfer_suggestions: List[Dict]


class FPLWeeklySummary:
    """מחלקה ראשית לסיכום השבועי"""
    
    def __init__(self, data_dir: str = "fpl_data", config_file: str = "config.json"):
        self.data_dir = Path(data_dir)
        self.output_dir = self.data_dir / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # טעינת קונפיגורציה
        self.config = self._load_config(config_file)
        
        # טעינת נתונים
        print("📥 טוען נתונים...")
        self.managers_data = self._load_latest_file("managers_detailed_*.json")
        self.bootstrap_data = self._load_latest_file("bootstrap_data_*.json")
        self.live_data = self._load_latest_file("live_gw*.json")
        self.league_data = self._load_latest_file("league_*.json")
        
        if not self.managers_data or not self.bootstrap_data:
            raise FileNotFoundError("❌ לא נמצאו קבצי נתונים. הרץ קודם: python src/fpl_data_collector.py <LEAGUE_ID>")
        
        # מפות עזר
        self.players_map = {p['id']: p for p in self.bootstrap_data.get('elements', [])}
        self.teams_map = {t['id']: t for t in self.bootstrap_data.get('teams', [])}
        self.positions_map = {1: 'שוער', 2: 'מגן', 3: 'קשר', 4: 'חלוץ'}
        
        # נקודות במחזור הנוכחי
        self.gw_points_map = {}
        if self.live_data and 'elements' in self.live_data:
            for elem in self.live_data['elements']:
                self.gw_points_map[elem['id']] = elem.get('stats', {}).get('total_points', 0)
        
        # ממוצעים עולמיים
        self.gw_averages = {}
        self.gw_highest = {}
        for event in self.bootstrap_data.get('events', []):
            gw_id = event['id']
            if event.get('average_entry_score'):
                self.gw_averages[gw_id] = event['average_entry_score']
            if event.get('highest_score'):
                self.gw_highest[gw_id] = event['highest_score']
        
        # מחזור נוכחי
        self.current_gw = self._get_current_gw()
        self.league_name = self.league_data.get('league', {}).get('name', 'הליגה שלנו')
        
        # Claude AI client (אם זמין)
        self.claude_client = None
        if CLAUDE_AVAILABLE and self.config.get('claude_api_key'):
            self.claude_client = Anthropic(api_key=self.config['claude_api_key'])
        
        # Twilio client (אם זמין)
        self.twilio_client = None
        if TWILIO_AVAILABLE and self.config.get('twilio_account_sid'):
            self.twilio_client = TwilioClient(
                self.config['twilio_account_sid'],
                self.config['twilio_auth_token']
            )
        
        print(f"✅ נתונים נטענו בהצלחה - מחזור {self.current_gw}")
    
    def _load_config(self, config_file: str) -> dict:
        """טעינת קונפיגורציה מקובץ או משתני סביבה"""
        config = {
            'claude_api_key': os.environ.get('ANTHROPIC_API_KEY', ''),
            'twilio_account_sid': os.environ.get('TWILIO_ACCOUNT_SID', ''),
            'twilio_auth_token': os.environ.get('TWILIO_AUTH_TOKEN', ''),
            'twilio_from_number': os.environ.get('TWILIO_FROM_NUMBER', ''),
            'whatsapp_to_number': os.environ.get('WHATSAPP_TO_NUMBER', ''),
        }
        
        # נסה לטעון מקובץ
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                config.update(file_config)
        
        return config
    
    def _load_latest_file(self, pattern: str) -> dict:
        """טעינת הקובץ האחרון שתואם לתבנית"""
        files = list(self.data_dir.glob(pattern))
        if not files:
            return {}
        latest = max(files, key=lambda p: p.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_current_gw(self) -> int:
        """מציאת המחזור הנוכחי"""
        for event in self.bootstrap_data.get('events', []):
            if event.get('is_current'):
                return event['id']
        # אם אין current, קח את האחרון שהסתיים
        for event in reversed(self.bootstrap_data.get('events', [])):
            if event.get('finished'):
                return event['id']
        return 1
    
    def _get_player_info(self, player_id: int) -> dict:
        """מידע על שחקן"""
        player = self.players_map.get(player_id, {})
        team = self.teams_map.get(player.get('team', 0), {})
        return {
            'id': player_id,
            'name': player.get('web_name', 'לא ידוע'),
            'full_name': f"{player.get('first_name', '')} {player.get('second_name', '')}",
            'team': team.get('short_name', '???'),
            'team_full': team.get('name', 'לא ידוע'),
            'position': self.positions_map.get(player.get('element_type', 0), 'לא ידוע'),
            'price': player.get('now_cost', 0) / 10,
            'form': float(player.get('form', 0)),
            'points_per_game': float(player.get('points_per_game', 0)),
            'total_points': player.get('total_points', 0),
            'goals': player.get('goals_scored', 0),
            'assists': player.get('assists', 0),
            'clean_sheets': player.get('clean_sheets', 0),
            'selected_by_percent': float(player.get('selected_by_percent', 0)),
            'gw_points': self.gw_points_map.get(player_id, 0),
            'status': player.get('status', 'a'),
            'news': player.get('news', ''),
        }
    
    def analyze_manager(self, manager_id: str, manager_data: dict) -> Optional[ManagerAnalysis]:
        """ניתוח מעמיק של מאמן"""
        info = manager_data.get('manager_info', {})
        history = manager_data.get('history', {}).get('current', [])
        picks_data = manager_data.get('current_picks', {})
        picks = picks_data.get('picks', [])
        
        # מצא מחזור נוכחי וקודם
        gw_current = None
        gw_previous = None
        recent_gws = []
        
        for gw in history:
            if gw['event'] == self.current_gw:
                gw_current = gw
            elif gw['event'] == self.current_gw - 1:
                gw_previous = gw
            if gw['event'] >= self.current_gw - 4:
                recent_gws.append(gw)
        
        if not gw_current:
            return None
        
        # חישוב שינוי דירוג
        rank_change = 0
        rank_change_pct = 0
        if gw_previous:
            prev_rank = gw_previous.get('overall_rank', 0)
            curr_rank = gw_current.get('overall_rank', 0)
            if prev_rank and curr_rank:
                rank_change = prev_rank - curr_rank
                rank_change_pct = (rank_change / prev_rank) * 100 if prev_rank else 0
        
        # ניתוח הרכב
        starting_xi = []
        bench = []
        captain_name = None
        captain_points = 0
        
        for pick in picks:
            player_info = self._get_player_info(pick['element'])
            player_info['multiplier'] = pick.get('multiplier', 1)
            player_info['is_captain'] = pick.get('is_captain', False)
            player_info['is_vice'] = pick.get('is_vice_captain', False)
            player_info['actual_points'] = player_info['gw_points'] * player_info['multiplier']
            
            if pick.get('is_captain'):
                captain_name = player_info['name']
                captain_points = player_info['actual_points']
            
            if pick['position'] <= 11:
                starting_xi.append(player_info)
            else:
                bench.append(player_info)
        
        # נקודות ספסל
        bench_points = sum(p['gw_points'] for p in bench)
        
        # ביצועים מול הממוצע העולמי
        world_avg = self.gw_averages.get(self.current_gw, 50)
        vs_world_avg = gw_current['points'] - world_avg
        
        # ביצועים ב-5 מחזורים אחרונים מול הממוצע
        vs_world_avg_5gw = 0
        if recent_gws:
            diffs = []
            for gw in recent_gws:
                gw_avg = self.gw_averages.get(gw['event'], 50)
                diffs.append(gw['points'] - gw_avg)
            vs_world_avg_5gw = sum(diffs) / len(diffs)
        
        # מגמת פורמה
        form_trend = "יציב"
        if len(recent_gws) >= 3:
            recent_points = [gw['points'] for gw in sorted(recent_gws, key=lambda x: x['event'])]
            if recent_points[-1] > recent_points[0] + 10:
                form_trend = "עולה 📈"
            elif recent_points[-1] < recent_points[0] - 10:
                form_trend = "יורד 📉"
        
        # צ'יפים
        chips_data = manager_data.get('history', {}).get('chips', [])
        chips_used_after_reset = [c['name'] for c in chips_data if c.get('event', 0) >= 20]
        all_chips = ['wildcard', 'freehit', 'bboost', '3xc']
        chips_remaining = [c for c in all_chips if c not in chips_used_after_reset]
        
        # שחקנים חלשים (להמלצות העברה)
        weakest = sorted(starting_xi, key=lambda x: x['form'])[:3]
        weakest_players = [
            {'name': p['name'], 'team': p['team'], 'form': p['form'], 'price': p['price']}
            for p in weakest if p['form'] < 4
        ]
        
        # המלצות העברה
        transfer_suggestions = self._generate_transfer_suggestions(starting_xi, gw_current.get('bank', 0) / 10)
        
        return ManagerAnalysis(
            name=info.get('player_name', 'לא ידוע'),
            team_name=info.get('team_name', 'לא ידוע'),
            gw_points=gw_current['points'],
            total_points=gw_current['total_points'],
            overall_rank=gw_current.get('overall_rank', 0),
            rank_change=rank_change,
            rank_change_pct=rank_change_pct,
            transfers=gw_current.get('event_transfers', 0),
            hits=gw_current.get('event_transfers_cost', 0),
            bench_points=bench_points,
            bank=gw_current.get('bank', 0) / 10,
            team_value=gw_current.get('value', 1000) / 10,
            captain_name=captain_name or 'לא ידוע',
            captain_points=captain_points,
            starting_xi=starting_xi,
            bench=bench,
            chips_remaining=chips_remaining,
            chips_used=chips_used_after_reset,
            vs_world_avg=vs_world_avg,
            vs_world_avg_5gw=vs_world_avg_5gw,
            form_trend=form_trend,
            weakest_players=weakest_players,
            transfer_suggestions=transfer_suggestions,
        )
    
    def _generate_transfer_suggestions(self, current_team: List[Dict], bank: float) -> List[Dict]:
        """יצירת המלצות העברה"""
        suggestions = []
        
        # מצא שחקנים חלשים בקבוצה
        weak_players = [p for p in current_team if p['form'] < 4 and p['status'] != 'a']
        weak_players += [p for p in current_team if p['form'] < 3]
        
        current_ids = {p['id'] for p in current_team}
        
        for weak in weak_players[:2]:
            budget = bank + weak['price']
            position_type = {'שוער': 1, 'מגן': 2, 'קשר': 3, 'חלוץ': 4}.get(weak['position'], 0)
            
            # מצא תחליפים טובים
            candidates = []
            for player in self.bootstrap_data.get('elements', []):
                if player['element_type'] != position_type:
                    continue
                if player['id'] in current_ids:
                    continue
                if player['now_cost'] / 10 > budget:
                    continue
                if player.get('status', 'a') != 'a':
                    continue
                
                form = float(player.get('form', 0))
                if form < 5:
                    continue
                
                candidates.append({
                    'name': player['web_name'],
                    'team': self.teams_map.get(player['team'], {}).get('short_name', '???'),
                    'price': player['now_cost'] / 10,
                    'form': form,
                    'selected_by': float(player.get('selected_by_percent', 0)),
                })
            
            if candidates:
                best = sorted(candidates, key=lambda x: x['form'], reverse=True)[0]
                suggestions.append({
                    'out': weak['name'],
                    'out_form': weak['form'],
                    'in': best['name'],
                    'in_team': best['team'],
                    'in_form': best['form'],
                    'in_price': best['price'],
                })
        
        return suggestions
    
    def _find_differentials(self, all_managers: List[ManagerAnalysis]) -> List[Dict]:
        """מציאת דיפרנשיאלים שהצליחו"""
        player_owners = defaultdict(list)
        
        for m in all_managers:
            for p in m.starting_xi:
                player_owners[p['name']].append({
                    'owner': m.name,
                    'points': p['gw_points']
                })
        
        differentials = []
        for player, owners in player_owners.items():
            if len(owners) == 1 and owners[0]['points'] >= 6:
                differentials.append({
                    'player': player,
                    'points': owners[0]['points'],
                    'owner': owners[0]['owner']
                })
        
        return sorted(differentials, key=lambda x: x['points'], reverse=True)
    
    def _get_captain_analysis(self, all_managers: List[ManagerAnalysis]) -> Dict:
        """ניתוח קפטנים"""
        captain_stats = defaultdict(lambda: {'count': 0, 'points': 0, 'managers': []})
        
        for m in all_managers:
            cap = m.captain_name
            captain_stats[cap]['count'] += 1
            captain_stats[cap]['points'] = m.captain_points
            captain_stats[cap]['managers'].append(m.name)
        
        # מצא את הבחירה הטובה והגרועה ביותר
        best_captain = max(captain_stats.items(), key=lambda x: x[1]['points'])
        worst_captain = min(captain_stats.items(), key=lambda x: x[1]['points'])
        most_popular = max(captain_stats.items(), key=lambda x: x[1]['count'])
        
        return {
            'stats': dict(captain_stats),
            'best': {'name': best_captain[0], **best_captain[1]},
            'worst': {'name': worst_captain[0], **worst_captain[1]},
            'most_popular': {'name': most_popular[0], **most_popular[1]},
        }
    
    def _get_top_gw_players(self, limit: int = 10) -> List[Dict]:
        """השחקנים הטובים ביותר במחזור"""
        players_with_points = []
        
        for player_id, points in self.gw_points_map.items():
            if points >= 5:
                player = self._get_player_info(player_id)
                player['gw_points'] = points
                players_with_points.append(player)
        
        return sorted(players_with_points, key=lambda x: x['gw_points'], reverse=True)[:limit]
    
    def _generate_ai_predictions(self, all_managers: List[ManagerAnalysis]) -> str:
        """יצירת תחזיות עם Claude AI"""
        if not self.claude_client:
            return self._generate_basic_predictions(all_managers)
        
        try:
            # הכן נתונים לפרומפט
            summary_data = {
                'gameweek': self.current_gw,
                'remaining_gws': 38 - self.current_gw,
                'managers': [
                    {
                        'name': m.name,
                        'total_points': m.total_points,
                        'rank': m.overall_rank,
                        'form': m.form_trend,
                        'chips_remaining': m.chips_remaining,
                        'vs_avg': m.vs_world_avg_5gw,
                    }
                    for m in all_managers
                ],
                'world_avg': self.gw_averages.get(self.current_gw, 50),
            }
            
            prompt = f"""אתה מומחה FPL (Fantasy Premier League). נתח את הנתונים הבאים ותן תחזיות קצרות בעברית:

נתוני הליגה:
{json.dumps(summary_data, ensure_ascii=False, indent=2)}

תן:
1. תחזית קצרה למחזורים הקרובים (2-3 משפטים)
2. המלצה אסטרטגית אחת לגבי צ'יפים
3. שחקן אחד שכדאי לשים עליו עין

תענה בעברית, בקצרה (עד 150 מילים)."""

            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"⚠️ שגיאה ב-Claude API: {e}")
            return self._generate_basic_predictions(all_managers)
    
    def _generate_basic_predictions(self, all_managers: List[ManagerAnalysis]) -> str:
        """תחזיות בסיסיות ללא AI"""
        lines = []
        
        remaining_gws = 38 - self.current_gw
        
        # מצא את המוביל והפער
        by_total = sorted(all_managers, key=lambda x: x.total_points, reverse=True)
        leader = by_total[0]
        
        if len(by_total) > 1:
            gap = leader.total_points - by_total[1].total_points
            lines.append(f"עם פער של {gap} נקודות ו-{remaining_gws} מחזורים, המרוץ עדיין פתוח.")
        
        # המלצת צ'יפים
        dgw_hint = ""
        if self.current_gw < 26:
            dgw_hint = "מחזור כפול 26 מתקרב - שמרו את ה-Bench Boost או Triple Captain!"
        elif self.current_gw < 37:
            dgw_hint = "סוף העונה מתקרב - זה הזמן להשתמש בצ'יפים שנשארו!"
        
        if dgw_hint:
            lines.append(dgw_hint)
        
        # שחקן לשים עליו עין
        top_form_players = sorted(
            self.bootstrap_data.get('elements', []),
            key=lambda x: float(x.get('form', 0)),
            reverse=True
        )[:5]
        
        if top_form_players:
            hot_player = top_form_players[0]
            lines.append(f"🔥 שחקן חם: {hot_player['web_name']} עם פורמה של {hot_player['form']}")
        
        return "\n".join(lines)
    
    def generate_summary(self) -> str:
        """יצירת הסיכום המלא"""
        print("📊 מנתח נתונים...")
        
        # נתח את כל המאמנים
        all_managers = []
        for manager_id, manager_data in self.managers_data.items():
            analysis = self.analyze_manager(manager_id, manager_data)
            if analysis:
                all_managers.append(analysis)
        
        if not all_managers:
            return "❌ לא נמצאו נתונים על מאמנים"
        
        # מיונים
        by_gw_points = sorted(all_managers, key=lambda x: x.gw_points, reverse=True)
        by_total = sorted(all_managers, key=lambda x: x.total_points, reverse=True)
        
        # סטטיסטיקות
        league_avg = sum(m.gw_points for m in all_managers) / len(all_managers)
        world_avg = self.gw_averages.get(self.current_gw, 50)
        world_highest = self.gw_highest.get(self.current_gw, 0)
        
        # ניתוחים
        differentials = self._find_differentials(all_managers)
        captain_analysis = self._get_captain_analysis(all_managers)
        top_gw_players = self._get_top_gw_players(5)
        
        # בניית הסיכום
        lines = []
        
        # כותרת
        lines.append(f"🏆 סיכום מחזור {self.current_gw} - {self.league_name} 🏆")
        lines.append("")
        
        # ═══════════════════════════════════════
        # תמונת המצב
        # ═══════════════════════════════════════
        lines.append("═" * 40)
        lines.append("📊 תמונת המצב")
        lines.append("═" * 40)
        lines.append("")
        lines.append(f"ממוצע הליגה: {league_avg:.1f} נקודות")
        lines.append(f"ממוצע עולמי: {world_avg} נקודות")
        if world_highest:
            lines.append(f"הניקוד הגבוה בעולם: {world_highest} נקודות")
        
        league_vs_world = league_avg - world_avg
        if league_vs_world > 0:
            lines.append(f"✅ הליגה שלנו מעל הממוצע העולמי ב-{league_vs_world:.1f} נקודות!")
        else:
            lines.append(f"📉 הליגה שלנו מתחת לממוצע העולמי ב-{abs(league_vs_world):.1f} נקודות")
        lines.append("")
        
        # ═══════════════════════════════════════
        # מוביל השבוע
        # ═══════════════════════════════════════
        lines.append("═" * 40)
        leader = by_gw_points[0]
        lines.append(f"👑 מוביל השבוע: {leader.name}")
        lines.append("═" * 40)
        lines.append("")
        lines.append(f"📈 {leader.gw_points} נקודות במחזור")
        
        if leader.rank_change > 0:
            lines.append(f"🚀 עלייה של {leader.rank_change:,} מקומות בדירוג העולמי!")
        
        lines.append(f"👑 קפטן: {leader.captain_name} ({leader.captain_points} נק')")
        
        # דיפרנשיאלים של המוביל
        leader_diffs = [d for d in differentials if d['owner'] == leader.name]
        if leader_diffs:
            lines.append("")
            lines.append("🎯 הדיפרנשיאלים שעשו את ההבדל:")
            for d in leader_diffs[:3]:
                lines.append(f"   • {d['player']} - {d['points']} נק'")
        lines.append("")
        
        # ═══════════════════════════════════════
        # קרב הקפטנים
        # ═══════════════════════════════════════
        lines.append("═" * 40)
        lines.append("🎯 קרב הקפטנים")
        lines.append("═" * 40)
        lines.append("")
        
        cap = captain_analysis
        lines.append(f"🏆 הבחירה הטובה: {cap['best']['name']} ({cap['best']['points']} נק')")
        lines.append(f"   בחרו בו: {', '.join(cap['best']['managers'])}")
        
        if cap['worst']['points'] < cap['best']['points'] - 10:
            lines.append(f"😢 הבחירה הפחות טובה: {cap['worst']['name']} ({cap['worst']['points']} נק')")
        
        # פירוט כל הקפטנים
        lines.append("")
        for cap_name, stats in sorted(cap['stats'].items(), key=lambda x: x[1]['points'], reverse=True):
            lines.append(f"   {cap_name}: {stats['points']} נק' ({stats['count']} מאמנים)")
        lines.append("")
        
        # ═══════════════════════════════════════
        # דיפרנשיאלים
        # ═══════════════════════════════════════
        if differentials:
            lines.append("═" * 40)
            lines.append("💎 דיפרנשיאלים שהרוויחו")
            lines.append("═" * 40)
            lines.append("")
            for d in differentials[:5]:
                lines.append(f"• {d['player']} ({d['points']} נק') - רק ל-{d['owner']}")
            lines.append("")
        
        # ═══════════════════════════════════════
        # השחקנים החמים במחזור
        # ═══════════════════════════════════════
        lines.append("═" * 40)
        lines.append("🔥 השחקנים החמים במחזור")
        lines.append("═" * 40)
        lines.append("")
        for i, p in enumerate(top_gw_players[:5], 1):
            lines.append(f"{i}. {p['name']} ({p['team']}) - {p['gw_points']} נק'")
        lines.append("")
        
        # ═══════════════════════════════════════
        # ביצועים מול הממוצע העולמי
        # ═══════════════════════════════════════
        lines.append("═" * 40)
        lines.append("📈 ביצועים מול העולם (5 מחזורים)")
        lines.append("═" * 40)
        lines.append("")
        
        above_avg = [(m.name, m.vs_world_avg_5gw) for m in all_managers if m.vs_world_avg_5gw > 3]
        below_avg = [(m.name, m.vs_world_avg_5gw) for m in all_managers if m.vs_world_avg_5gw < -3]
        
        if above_avg:
            lines.append("✅ מעל הממוצע בעקביות:")
            for name, diff in sorted(above_avg, key=lambda x: x[1], reverse=True):
                lines.append(f"   • {name}: +{diff:.1f} לשבוע")
        
        if below_avg:
            lines.append("📉 מתחת לממוצע:")
            for name, diff in sorted(below_avg, key=lambda x: x[1]):
                lines.append(f"   • {name}: {diff:.1f} לשבוע")
        lines.append("")
        
        # ═══════════════════════════════════════
        # המלצות העברות אישיות
        # ═══════════════════════════════════════
        lines.append("═" * 40)
        lines.append("🔄 המלצות העברות אישיות")
        lines.append("═" * 40)
        lines.append("")
        
        for m in by_total:
            if m.transfer_suggestions:
                lines.append(f"💡 {m.name}:")
                for sug in m.transfer_suggestions[:1]:
                    lines.append(f"   החלף: {sug['out']} (פורמה {sug['out_form']:.1f})")
                    lines.append(f"   ← {sug['in']} ({sug['in_team']}, פורמה {sug['in_form']:.1f}, £{sug['in_price']}m)")
                lines.append("")
        
        # ═══════════════════════════════════════
        # מצב הצ'יפים
        # ═══════════════════════════════════════
        lines.append("═" * 40)
        lines.append("🎰 מצב הצ'יפים")
        lines.append("═" * 40)
        lines.append("")
        
        chip_names = {'wildcard': 'WC', 'freehit': 'FH', 'bboost': 'BB', '3xc': 'TC'}
        for m in by_total:
            remaining = [chip_names.get(c, c) for c in m.chips_remaining]
            if remaining:
                lines.append(f"{m.name}: {', '.join(remaining)}")
            else:
                lines.append(f"{m.name}: ❌ אין צ'יפים")
        lines.append("")
        
        # ═══════════════════════════════════════
        # טבלת הליגה
        # ═══════════════════════════════════════
        lines.append("═" * 40)
        lines.append("📊 טבלת הליגה")
        lines.append("═" * 40)
        lines.append("")
        
        for i, m in enumerate(by_total, 1):
            rank_str = self._format_rank(m.overall_rank)
            trend = "⬆️" if m.rank_change > 0 else ("⬇️" if m.rank_change < 0 else "➡️")
            lines.append(f"{i}. {m.name} - {m.total_points:,} נק' ({rank_str}) {trend}")
        lines.append("")
        
        # ═══════════════════════════════════════
        # תחזיות ומבט קדימה
        # ═══════════════════════════════════════
        lines.append("═" * 40)
        lines.append("🔮 מבט קדימה")
        lines.append("═" * 40)
        lines.append("")
        
        predictions = self._generate_ai_predictions(all_managers) if self.claude_client else self._generate_basic_predictions(all_managers)
        lines.append(predictions)
        lines.append("")
        
        # סיום
        lines.append("═" * 40)
        remaining_gws = 38 - self.current_gw
        lines.append(f"⚽ עוד {remaining_gws} מחזורים - הכל פתוח! ⚽")
        lines.append("═" * 40)
        
        return "\n".join(lines)
    
    def _format_rank(self, rank: int) -> str:
        """פורמט דירוג"""
        if rank >= 1000000:
            return f"{rank/1000000:.1f}M"
        elif rank >= 1000:
            return f"{rank/1000:.0f}K"
        return f"{rank:,}"
    
    def save_summary(self) -> Path:
        """שמירת הסיכום לקובץ"""
        summary = self.generate_summary()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        filename = self.output_dir / f"weekly_summary_GW{self.current_gw}_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"\n💾 נשמר: {filename}")
        return filename, summary
    
    def send_to_whatsapp(self, message: str) -> bool:
        """שליחה לוואטסאפ דרך Twilio"""
        if not self.twilio_client:
            print("⚠️ Twilio לא מוגדר. הגדר את המפתחות ב-config.json או משתני סביבה.")
            return False
        
        try:
            from_number = f"whatsapp:{self.config['twilio_from_number']}"
            to_number = f"whatsapp:{self.config['whatsapp_to_number']}"
            
            # WhatsApp מגביל הודעות ל-1600 תווים, נפצל אם צריך
            max_length = 1500
            messages = []
            
            if len(message) <= max_length:
                messages = [message]
            else:
                # פיצול לפי שורות
                lines = message.split('\n')
                current_msg = ""
                for line in lines:
                    if len(current_msg) + len(line) + 1 > max_length:
                        messages.append(current_msg)
                        current_msg = line
                    else:
                        current_msg += "\n" + line if current_msg else line
                if current_msg:
                    messages.append(current_msg)
            
            # שלח את כל ההודעות
            for i, msg in enumerate(messages, 1):
                self.twilio_client.messages.create(
                    body=msg,
                    from_=from_number,
                    to=to_number
                )
                print(f"✅ נשלחה הודעה {i}/{len(messages)}")
            
            return True
            
        except Exception as e:
            print(f"❌ שגיאה בשליחה לוואטסאפ: {e}")
            return False
    
    def run(self, send_whatsapp: bool = True) -> str:
        """הרצה מלאה - יצירת סיכום ושליחה"""
        print("🚀 מתחיל סיכום שבועי...")
        print("")
        
        # יצירת ושמירת הסיכום
        filename, summary = self.save_summary()
        
        # הדפסה למסך
        print("\n" + "=" * 50)
        print(summary)
        print("=" * 50 + "\n")
        
        # שליחה לוואטסאפ
        if send_whatsapp and self.twilio_client:
            print("📱 שולח לוואטסאפ...")
            self.send_to_whatsapp(summary)
        
        return summary


def create_config_template():
    """יצירת תבנית קובץ קונפיגורציה"""
    config = {
        "claude_api_key": "YOUR_ANTHROPIC_API_KEY",
        "twilio_account_sid": "YOUR_TWILIO_ACCOUNT_SID",
        "twilio_auth_token": "YOUR_TWILIO_AUTH_TOKEN",
        "twilio_from_number": "+14155238886",
        "whatsapp_to_number": "+972XXXXXXXXX",
    }
    
    with open("config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ נוצר קובץ config.json - ערוך אותו עם המפתחות שלך")


def main():
    import sys
    
    # בדוק אם צריך ליצור קונפיגורציה
    if len(sys.argv) > 1 and sys.argv[1] == '--setup':
        create_config_template()
        print("\n📝 הדרכה:")
        print("1. הירשם ל-Twilio: https://www.twilio.com/try-twilio")
        print("2. הפעל WhatsApp Sandbox: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
        print("3. הירשם ל-Anthropic: https://console.anthropic.com/")
        print("4. ערוך את config.json עם המפתחות שלך")
        print("5. הרץ: python src/fpl_weekly_summary.py")
        return
    
    try:
        # בדוק אם יש קונפיגורציה
        if not Path("config.json").exists():
            print("⚠️ לא נמצא קובץ config.json")
            print("   הרץ: python src/fpl_weekly_summary.py --setup")
            print("   או המשך ללא WhatsApp ו-AI...")
            print("")
        
        # הרץ את הסיכום
        app = FPLWeeklySummary()
        
        # בדוק אם לשלוח לוואטסאפ
        send_whatsapp = '--no-whatsapp' not in sys.argv
        
        app.run(send_whatsapp=send_whatsapp)
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\nהרץ קודם: python src/fpl_data_collector.py <LEAGUE_ID>")
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
