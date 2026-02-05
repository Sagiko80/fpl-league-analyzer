#!/usr/bin/env python3
"""
FPL WhatsApp Weekly Summary
סיכום שבועי מפורט לקבוצת הוואטסאפ
"""

import json
from pathlib import Path
from datetime import datetime


class WhatsAppSummary:
    def __init__(self, data_dir: str = "fpl_data"):
        self.data_dir = Path(data_dir)
        self.output_dir = self.data_dir / "reports"
        self.output_dir.mkdir(exist_ok=True)
        
        self.managers_data = self.load_latest_file("managers_detailed_*.json")
        self.bootstrap_data = self.load_latest_file("bootstrap_data_*.json")
        self.live_data = self.load_latest_file("live_gw*.json")
        
        self.players_map = {p['id']: p for p in self.bootstrap_data['elements']}
        self.points_map = {e['id']: e['stats']['total_points'] for e in self.live_data.get('elements', [])}
        
        # ממוצעים עולמיים לפי מחזור
        self.gw_averages = {}
        for event in self.bootstrap_data['events']:
            if event.get('average_entry_score'):
                self.gw_averages[event['id']] = event['average_entry_score']
    
    def load_latest_file(self, pattern: str) -> dict:
        files = list(self.data_dir.glob(pattern))
        if not files:
            return {}
        latest = max(files, key=lambda p: p.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_current_gw(self) -> int:
        for event in self.bootstrap_data['events']:
            if event['is_current']:
                return event['id']
        for event in reversed(self.bootstrap_data['events']):
            if event['finished']:
                return event['id']
        return 1
    
    def get_manager_data(self, manager_data: dict, current_gw: int) -> dict:
        """מחלץ נתונים על מנג'ר"""
        info = manager_data['manager_info']
        history = manager_data.get('history', {}).get('current', [])
        picks = manager_data.get('current_picks', {}).get('picks', [])
        
        gw_current = None
        gw_previous = None
        for gw in history:
            if gw['event'] == current_gw:
                gw_current = gw
            elif gw['event'] == current_gw - 1:
                gw_previous = gw
        
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
                rank_change_pct = (rank_change / prev_rank) * 100
        
        # מציאת קפטן
        captain_name = None
        captain_pts = 0
        for p in picks:
            if p.get('is_captain'):
                player = self.players_map.get(p['element'], {})
                captain_name = player.get('web_name', 'Unknown')
                captain_pts = self.points_map.get(p['element'], 0) * 2
        
        # נקודות ספסל
        bench_pts = gw_current.get('points_on_bench', 0)
        
        # שחקנים בהרכב
        starting_xi = []
        bench = []
        for p in picks:
            player = self.players_map.get(p['element'], {})
            pts = self.points_map.get(p['element'], 0)
            player_info = {
                'name': player.get('web_name', 'Unknown'),
                'pts': pts,
                'is_captain': p.get('is_captain', False)
            }
            if p['position'] <= 11:
                starting_xi.append(player_info)
            else:
                bench.append(player_info)
        
        return {
            'name': info['player_name'],
            'team': info['team_name'],
            'gw_pts': gw_current['points'],
            'total_pts': gw_current['total_points'],
            'overall_rank': gw_current.get('overall_rank', 0),
            'rank_change': rank_change,
            'rank_change_pct': rank_change_pct,
            'transfers': gw_current.get('event_transfers', 0),
            'hits': gw_current.get('event_transfers_cost', 0),
            'bench_pts': bench_pts,
            'bank': gw_current.get('bank', 0) / 10,
            'value': gw_current.get('value', 0) / 10,
            'captain_name': captain_name,
            'captain_pts': captain_pts,
            'starting_xi': starting_xi,
            'bench': bench
        }
    
    def get_differentials(self, all_managers: list) -> list:
        """מציאת דיפרנשיאלים שהצליחו"""
        player_owners = {}
        
        for m in all_managers:
            for p in m['starting_xi']:
                name = p['name']
                if name not in player_owners:
                    player_owners[name] = {'pts': p['pts'], 'owners': []}
                player_owners[name]['owners'].append(m['name'])
        
        differentials = []
        for player, data in player_owners.items():
            if len(data['owners']) == 1 and data['pts'] >= 6:
                differentials.append({
                    'player': player,
                    'pts': data['pts'],
                    'owner': data['owners'][0]
                })
        
        return sorted(differentials, key=lambda x: x['pts'], reverse=True)
    
    def get_chips_status(self, manager_data: dict) -> dict:
        """מצב צ'יפים מאז מחזור 19"""
        chips_used = manager_data.get('history', {}).get('chips', [])
        used_after_19 = [c['name'] for c in chips_used if c.get('event', 0) > 19]
        
        remaining = []
        if 'wildcard' not in used_after_19:
            remaining.append('WC')
        if 'freehit' not in used_after_19:
            remaining.append('FH')
        if 'bboost' not in used_after_19:
            remaining.append('BB')
        if '3xc' not in used_after_19:
            remaining.append('TC')
        
        return {
            'used': used_after_19,
            'remaining': remaining,
            'count': len(remaining)
        }
    
    def get_historical_best(self, manager_data: dict) -> dict:
        """הישג הכי טוב בהיסטוריה"""
        past = manager_data.get('history', {}).get('past', [])
        if not past:
            return None
        
        best = min(past, key=lambda x: x['rank'])
        return {
            'season': best['season_name'],
            'rank': best['rank'],
            'points': best['total_points']
        }
    
    def get_performance_vs_average(self, manager_data: dict, current_gw: int) -> dict:
        """ביצועים מול הממוצע העולמי ב-5 שבועות אחרונים"""
        history = manager_data.get('history', {}).get('current', [])
        
        diffs = []
        for gw_num in range(current_gw - 4, current_gw + 1):
            for gw in history:
                if gw['event'] == gw_num:
                    pts = gw['points']
                    avg = self.gw_averages.get(gw_num, 50)
                    diffs.append(pts - avg)
                    break
        
        total_diff = sum(diffs) if diffs else 0
        avg_diff = total_diff / len(diffs) if diffs else 0
        
        return {
            'diffs': diffs,
            'total': total_diff,
            'avg': avg_diff
        }
    
    def generate_summary(self) -> str:
        """יצירת הסיכום המלא"""
        current_gw = self.get_current_gw()
        gw_avg = self.gw_averages.get(current_gw, 50)
        
        # איסוף נתונים על כל המנג'רים
        all_managers = []
        for manager_id, manager_data in self.managers_data.items():
            data = self.get_manager_data(manager_data, current_gw)
            if data:
                data['chips'] = self.get_chips_status(manager_data)
                data['history_best'] = self.get_historical_best(manager_data)
                data['vs_average'] = self.get_performance_vs_average(manager_data, current_gw)
                all_managers.append(data)
        
        # מיון לפי נקודות המחזור
        all_managers.sort(key=lambda x: x['gw_pts'], reverse=True)
        
        # מיון לפי סה"כ נקודות לטבלה
        by_total = sorted(all_managers, key=lambda x: x['total_pts'], reverse=True)
        
        # ממוצע הליגה
        league_avg = sum(m['gw_pts'] for m in all_managers) / len(all_managers)
        
        # דיפרנשיאלים
        differentials = self.get_differentials(all_managers)
        
        # בניית הסיכום
        lines = []
        
        lines.append(f"🏆 סיכום מחזור {current_gw} - ליגת SOCCER SHIRT 🏆")
        lines.append("")
        lines.append("─" * 50)
        lines.append("")
        lines.append("📊 תמונת המצב")
        lines.append("")
        lines.append(f"ממוצע הליגה השבוע הגיע ל-{league_avg:.1f} נקודות.")
        lines.append(f"הממוצע העולמי עמד על {gw_avg} נקודות.")
        top_pts = all_managers[0]['gw_pts']
        bottom_pts = all_managers[-1]['gw_pts']
        lines.append(f"הפער בין המוביל לאחרון בליגה עמד על {top_pts - bottom_pts} נקודות.")
        lines.append("")
        
        # מוביל השבוע
        leader = all_managers[0]
        lines.append("─" * 50)
        lines.append("")
        lines.append(f"👑 מוביל השבוע: {leader['name']} עם {leader['gw_pts']} נקודות")
        lines.append("")
        
        if leader['rank_change'] > 0:
            lines.append(f"{leader['name']} הפגין שבוע יוצא מן הכלל.")
            lines.append(f"עלייה של {leader['rank_change']:,} מקומות בדירוג העולמי, שיפור של {leader['rank_change_pct']:.0f} אחוז תוך שבוע אחד.")
        
        # דיפרנשיאלים של המוביל
        leader_diffs = [d for d in differentials if d['owner'] == leader['name']]
        if leader_diffs:
            lines.append("")
            lines.append("מה עשה נכון? הדיפרנשיאלים שלו עבדו בצורה מושלמת.")
            for d in leader_diffs[:3]:
                lines.append(f"{d['player']} הביא {d['pts']} נקודות.")
        
        if leader['hits'] == 0:
            # ספירת העברות ללא היטס בעונה
            for manager_id, manager_data in self.managers_data.items():
                if manager_data['manager_info']['player_name'] == leader['name']:
                    history = manager_data.get('history', {}).get('current', [])
                    total_transfers = sum(gw.get('event_transfers', 0) for gw in history)
                    total_hits = sum(gw.get('event_transfers_cost', 0) for gw in history)
                    if total_hits == 0:
                        lines.append("")
                        lines.append(f"נתון מרשים: {leader['name']} ביצע {total_transfers} העברות מתחילת העונה בלי לקחת היט אחד. אפס נקודות מינוס כל העונה.")
        
        lines.append("")
        
        # קרב הקפטנים
        lines.append("─" * 50)
        lines.append("")
        lines.append("🎯 קרב הקפטנים")
        lines.append("")
        
        captain_stats = {}
        for m in all_managers:
            cap = m['captain_name']
            if cap not in captain_stats:
                captain_stats[cap] = {'count': 0, 'pts': m['captain_pts'], 'managers': []}
            captain_stats[cap]['count'] += 1
            captain_stats[cap]['managers'].append(m['name'])
        
        for cap, stats in sorted(captain_stats.items(), key=lambda x: x[1]['count'], reverse=True):
            if stats['count'] > 1:
                lines.append(f"{stats['count']} מנהלים בחרו ב{cap} כקפטן וקיבלו {stats['pts']} נקודות.")
            else:
                lines.append(f"{stats['managers'][0]} בחר ב{cap} וקיבל {stats['pts']} נקודות.")
        
        lines.append("")
        
        # דיפרנשיאלים
        if differentials:
            lines.append("─" * 50)
            lines.append("")
            lines.append("🎯 הדיפרנשיאלים שהרוויחו השבוע")
            lines.append("")
            lines.append("השחקנים הייחודיים עשו את ההבדל הגדול:")
            lines.append("")
            for d in differentials[:6]:
                lines.append(f"{d['player']} הביא {d['pts']} נקודות ל{d['owner']} בלבד.")
            lines.append("")
            lines.append("מי שהחזיק את אותם שחקנים כמו כולם קיבל תוצאות בינוניות.")
            lines.append("")
        
        # המטפסים
        climbers = sorted(all_managers, key=lambda x: x['rank_change'], reverse=True)[:3]
        lines.append("─" * 50)
        lines.append("")
        lines.append("📈 המטפסים של השבוע")
        lines.append("")
        for m in climbers:
            if m['rank_change'] > 0:
                lines.append(f"{m['name']} קפץ {m['rank_change']:,} מקומות עם {m['gw_pts']} נקודות.")
                # פרטים על השחקנים הטובים
                top_players = sorted(m['starting_xi'], key=lambda x: x['pts'], reverse=True)[:4]
                players_str = ", ".join([f"{p['name']} עם {p['pts']}" for p in top_players])
                lines.append(f"השחקנים שתרמו: {players_str}.")
                if m['hits'] == 0 and m['transfers'] <= 1:
                    lines.append(f"העברה אחת בלבד ובלי היטס.")
                lines.append("")
        
        # מי נפגע
        fallers = sorted(all_managers, key=lambda x: x['rank_change'])[:3]
        lines.append("─" * 50)
        lines.append("")
        lines.append("📉 מי נפגע השבוע")
        lines.append("")
        for m in fallers:
            if m['rank_change'] < 0:
                lines.append(f"{m['name']} איבד {abs(m['rank_change']):,} מקומות עם {m['gw_pts']} נקודות בלבד.")
                # שחקנים שלא סיפקו
                bad_players = [p for p in m['starting_xi'] if p['pts'] <= 2 and not p['is_captain']]
                if bad_players:
                    bad_str = ", ".join([f"{p['name']} הביא {p['pts']}" for p in bad_players[:3]])
                    lines.append(f"שחקנים שאכזבו: {bad_str}.")
                lines.append("")
        
        # אסונות ספסל
        bench_disasters = [(m['name'], m['bench_pts'], m['bench']) for m in all_managers if m['bench_pts'] >= 6]
        if bench_disasters:
            bench_disasters.sort(key=lambda x: x[1], reverse=True)
            lines.append("─" * 50)
            lines.append("")
            lines.append("🔴 אסונות הספסל")
            lines.append("")
            for name, pts, bench in bench_disasters[:4]:
                bench_details = ", ".join([f"{p['name']} עם {p['pts']}" for p in bench if p['pts'] > 0])
                lines.append(f"{name} השאיר {pts} נקודות על הספסל: {bench_details}.")
            lines.append("")
        
        # ביצועים מול הממוצע העולמי
        lines.append("─" * 50)
        lines.append("")
        lines.append("📈 ביצועים מול הממוצע העולמי ב-5 שבועות אחרונים")
        lines.append("")
        
        # הצגת הממוצעים העולמיים
        gw_range = range(current_gw - 4, current_gw + 1)
        avgs_str = ", ".join([f"מחזור {gw} עם {self.gw_averages.get(gw, 50)}" for gw in gw_range])
        lines.append(f"הממוצעים העולמיים היו: {avgs_str}.")
        lines.append("")
        
        above_avg = [(m['name'], m['vs_average']['total'], m['vs_average']['avg']) for m in all_managers if m['vs_average']['avg'] > 2]
        below_avg = [(m['name'], m['vs_average']['total'], m['vs_average']['avg']) for m in all_managers if m['vs_average']['avg'] < -1]
        
        if above_avg:
            above_avg.sort(key=lambda x: x[1], reverse=True)
            lines.append("מי מעל הממוצע העולמי בעקביות:")
            for name, total, avg in above_avg[:5]:
                lines.append(f"{name} עם סך של פלוס {total} נקודות מעל הממוצע, ממוצע של פלוס {avg:.1f} לשבוע.")
            lines.append("")
        
        if below_avg:
            below_avg.sort(key=lambda x: x[1])
            lines.append("מי מתחת לממוצע העולמי:")
            for name, total, avg in below_avg:
                lines.append(f"{name} עם מינוס {abs(total)} נקודות, ממוצע של מינוס {abs(avg):.1f} לשבוע.")
            lines.append("")
        
        # מצב צ'יפים
        lines.append("─" * 50)
        lines.append("")
        lines.append("🎰 מצב הצ'יפים מאז האיפוס במחזור 19")
        lines.append("")
        
        full_chips = [m['name'] for m in all_managers if m['chips']['count'] == 4]
        if full_chips:
            lines.append(f"רוב הליגה עדיין מחזיקה את כל 4 הצ'יפים: {', '.join(full_chips)}.")
            lines.append(f"{len(full_chips)} מנהלים עם תחמושת מלאה.")
            lines.append("")
        
        # מי השתמש בצ'יפים
        for m in all_managers:
            if m['chips']['used']:
                used_str = ", ".join(m['chips']['used'])
                remaining_str = ", ".join(m['chips']['remaining']) if m['chips']['remaining'] else "אין"
                if m['chips']['count'] <= 2:
                    lines.append(f"{m['name']} השתמש ב{used_str}. נשארו לו: {remaining_str}.")
        lines.append("")
        
        # כסף בבנק
        rich = sorted(all_managers, key=lambda x: x['bank'], reverse=True)[:3]
        poor = min(all_managers, key=lambda x: x['value'])
        
        lines.append("─" * 50)
        lines.append("")
        lines.append("💰 כסף בבנק")
        lines.append("")
        for m in rich:
            if m['bank'] >= 3:
                lines.append(f"{m['name']} יושב על {m['bank']:.1f} מיליון בבנק.")
        lines.append("")
        lines.append(f"{poor['name']} עם קבוצה בשווי {poor['value']:.1f} מיליון בלבד, הנמוכה בליגה.")
        lines.append("")
        
        # פינת היסטוריה
        notable_history = []
        for m in all_managers:
            if m['history_best'] and m['history_best']['rank'] < 100000:
                notable_history.append((m['name'], m['history_best'], m['overall_rank']))
        
        if notable_history:
            lines.append("─" * 50)
            lines.append("")
            lines.append("📚 פינת ההיסטוריה")
            lines.append("")
            for name, best, current_rank in sorted(notable_history, key=lambda x: x[1]['rank']):
                lines.append(f"{name} סיים ב{best['season']} במקום {best['rank']:,} בעולם.")
                if current_rank > 1000000:
                    lines.append(f"היום הוא במקום {current_rank/1000000:.1f} מיליון.")
                else:
                    lines.append(f"היום הוא במקום {current_rank:,}.")
                lines.append("")
        
        # טבלת הליגה
        lines.append("─" * 50)
        lines.append("")
        lines.append("📊 טבלת הליגה")
        lines.append("")
        for i, m in enumerate(by_total, 1):
            rank_str = f"{m['overall_rank']/1000000:.1f} מיליון" if m['overall_rank'] >= 1000000 else f"{m['overall_rank']:,}"
            lines.append(f"{i}. {m['name']} - {m['total_pts']:,} נקודות, דירוג {rank_str}")
        lines.append("")
        
        # סיום
        lines.append("─" * 50)
        lines.append("")
        gap_1_2 = by_total[0]['total_pts'] - by_total[1]['total_pts']
        gap_3_8 = by_total[2]['total_pts'] - by_total[7]['total_pts'] if len(by_total) > 7 else 0
        
        lines.append(f"הפער בין מקום ראשון לשני: {gap_1_2} נקודות בלבד.")
        if gap_3_8:
            lines.append(f"הפער בין מקום שלישי לשמיני: {gap_3_8} נקודות בלבד.")
        lines.append("")
        remaining_gws = 38 - current_gw
        lines.append(f"עוד {remaining_gws} מחזורים והכל פתוח.")
        lines.append("")
        lines.append("מחזור כפול 26 מתקרב. מי שמתכנן נכון עם הצ'יפים יכול לסגור פערים גדולים.")
        lines.append("")
        
        return "\n".join(lines)
    
    def save_summary(self) -> Path:
        """שמירת הסיכום לקובץ"""
        summary = self.generate_summary()
        current_gw = self.get_current_gw()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        filename = self.output_dir / f"whatsapp_summary_GW{current_gw}_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(summary)
        print()
        print(f"💾 נשמר בקובץ: {filename}")
        
        return filename


def main():
    try:
        generator = WhatsAppSummary()
        generator.save_summary()
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
