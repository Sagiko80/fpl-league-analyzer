#!/usr/bin/env python3
"""
FPL Data Collector
Collects data from Fantasy Premier League API for:
1. Private league data (all managers in the league)
2. Global/bootstrap data (all players, teams, gameweeks)
3. Current gameweek data (even if not finished)
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class FPLDataCollector:
    BASE_URL = "https://fantasy.premierleague.com/api"
    
    def __init__(self, league_id: int, output_dir: str = "fpl_data"):
        self.league_id = league_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        
    def get_bootstrap_data(self) -> Dict:
        """Get global FPL data including all players, teams, and gameweeks"""
        print("Fetching bootstrap-static data...")
        response = self.session.get(f"{self.BASE_URL}/bootstrap-static/")
        response.raise_for_status()
        return response.json()
    
    def get_current_gameweek(self, bootstrap_data: Dict) -> int:
        """Get current gameweek number"""
        for event in bootstrap_data['events']:
            if event['is_current']:
                return event['id']
        # If no current gameweek, return the next one
        for event in bootstrap_data['events']:
            if event['is_next']:
                return event['id']
        return 1
    
    def get_league_standings(self) -> Dict:
        """Get private league standings"""
        print(f"Fetching league {self.league_id} standings...")
        response = self.session.get(
            f"{self.BASE_URL}/leagues-classic/{self.league_id}/standings/"
        )
        response.raise_for_status()
        return response.json()
    
    def get_manager_history(self, manager_id: int) -> Dict:
        """Get manager's full season history"""
        print(f"Fetching manager {manager_id} history...")
        response = self.session.get(f"{self.BASE_URL}/entry/{manager_id}/history/")
        response.raise_for_status()
        time.sleep(0.5)  # Rate limiting
        return response.json()
    
    def get_manager_gameweek_picks(self, manager_id: int, gameweek: int) -> Dict:
        """Get manager's picks for a specific gameweek"""
        print(f"Fetching manager {manager_id} picks for GW{gameweek}...")
        response = self.session.get(
            f"{self.BASE_URL}/entry/{manager_id}/event/{gameweek}/picks/"
        )
        response.raise_for_status()
        time.sleep(0.5)  # Rate limiting
        return response.json()
    
    def get_gameweek_live_data(self, gameweek: int) -> Dict:
        """Get live data for a specific gameweek"""
        print(f"Fetching live data for GW{gameweek}...")
        response = self.session.get(f"{self.BASE_URL}/event/{gameweek}/live/")
        response.raise_for_status()
        return response.json()
    
    def collect_all_data(self):
        """Main function to collect all data"""
        timestamp = datetime.now().isoformat()
        print(f"\n{'='*60}")
        print(f"FPL Data Collection Started: {timestamp}")
        print(f"{'='*60}\n")
        
        try:
            # 1. Get bootstrap data (global data)
            bootstrap_data = self.get_bootstrap_data()
            current_gw = self.get_current_gameweek(bootstrap_data)
            print(f"Current Gameweek: {current_gw}\n")
            
            # Save bootstrap data
            bootstrap_file = self.output_dir / f"bootstrap_data_{timestamp.split('T')[0]}.json"
            with open(bootstrap_file, 'w', encoding='utf-8') as f:
                json.dump(bootstrap_data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved bootstrap data to {bootstrap_file}\n")
            
            # 2. Get league standings
            league_data = self.get_league_standings()
            league_file = self.output_dir / f"league_{self.league_id}_{timestamp.split('T')[0]}.json"
            with open(league_file, 'w', encoding='utf-8') as f:
                json.dump(league_data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved league standings to {league_file}\n")
            
            # 3. Get current gameweek live data
            live_data = self.get_gameweek_live_data(current_gw)
            live_file = self.output_dir / f"live_gw{current_gw}_{timestamp.split('T')[0]}.json"
            with open(live_file, 'w', encoding='utf-8') as f:
                json.dump(live_data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved live GW{current_gw} data to {live_file}\n")
            
            # 4. Get detailed data for each manager in the league
            managers_data = {}
            standings = league_data['standings']['results']
            
            print(f"Collecting data for {len(standings)} managers...\n")
            for standing in standings:
                manager_id = standing['entry']
                manager_name = standing['entry_name']
                player_name = standing['player_name']
                
                print(f"Processing: {player_name} ({manager_name})")
                
                # Get manager history
                history = self.get_manager_history(manager_id)
                
                # Get current gameweek picks
                picks = self.get_manager_gameweek_picks(manager_id, current_gw)
                
                managers_data[manager_id] = {
                    'manager_info': {
                        'id': manager_id,
                        'player_name': player_name,
                        'team_name': manager_name,
                        'total_points': standing['total']
                    },
                    'history': history,
                    'current_picks': picks
                }
                
                print(f"✓ Completed {player_name}\n")
            
            # Save all managers data
            managers_file = self.output_dir / f"managers_detailed_{timestamp.split('T')[0]}.json"
            with open(managers_file, 'w', encoding='utf-8') as f:
                json.dump(managers_data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved detailed managers data to {managers_file}\n")
            
            # 5. Create summary
            summary = {
                'collection_timestamp': timestamp,
                'current_gameweek': current_gw,
                'league_id': self.league_id,
                'league_name': league_data['league']['name'],
                'total_managers': len(standings),
                'files_created': {
                    'bootstrap_data': str(bootstrap_file),
                    'league_standings': str(league_file),
                    'live_gameweek_data': str(live_file),
                    'managers_detailed': str(managers_file)
                }
            }
            
            summary_file = self.output_dir / f"summary_{timestamp.split('T')[0]}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"{'='*60}")
            print(f"Collection Complete!")
            print(f"{'='*60}")
            print(f"Total files created: 5")
            print(f"Output directory: {self.output_dir}")
            print(f"{'='*60}\n")
            
            return summary
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error during data collection: {e}")
            raise
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            raise


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fpl_data_collector.py <league_id>")
        print("\nExample: python fpl_data_collector.py 123456")
        print("\nTo find your league ID:")
        print("1. Go to your league page on fantasy.premierleague.com")
        print("2. The URL will look like: .../leagues/123456/standings/c")
        print("3. The number (123456) is your league ID")
        sys.exit(1)
    
    league_id = int(sys.argv[1])
    
    collector = FPLDataCollector(league_id=league_id)
    collector.collect_all_data()


if __name__ == "__main__":
    main()
