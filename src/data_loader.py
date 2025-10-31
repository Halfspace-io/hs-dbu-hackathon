"""Data loader for football event and tracking data."""
from pathlib import Path
from typing import Optional, Union, List, Tuple
import pandas as pd

from src.configs.directories import Directories
from src.configs.static import MATCH_ID_TO_PATH
from src.utils import extract_half_and_time_passed_in_half, _timestamp_helper


class DataLoader:
    """Load event and tracking data with filtering capabilities."""
    
    def __init__(self):
        """Initialize DataLoader with directory paths."""
        self.directories = Directories()
        self.events_df = self._load_events_data()
    
    def _get_competition_from_path(self, path: str) -> str:
        """Extract competition name from match path."""
        if path.startswith("H_EURO2024"):
            return "H_EURO2024"
        elif path.startswith("Q_EURO2025"):
            return "Q_EURO2025"
        elif path.startswith("U21_EURO2025"):
            return "U21_EURO2025"
        return "Unknown"
    
    def _load_events_data(self) -> pd.DataFrame:
        """Load the main events CSV file and add competition column."""
        events_path = self.directories.DATA_PATH / "events.csv"
        df = pd.read_csv(events_path)
        
        # Add competition column
        df['competition'] = df['matchId'].map(
            lambda match_id: self._get_competition_from_path(MATCH_ID_TO_PATH.get(match_id, ""))
        )
        
        return df
        
    def get_competitions(self) -> List[str]:
        """Get list of available competitions."""
        return ["H_EURO2024", "Q_EURO2025", "U21_EURO2025"]
    
    def get_teams_by_competition(self, competition: str) -> List[str]:
        """Get list of teams for a specific competition."""
        if self.events_df is None:
            return []
        
        # Filter by competition based on match IDs
        competition_matches = [
            match_id for match_id, path in MATCH_ID_TO_PATH.items() 
            if path.startswith(competition)
        ]
        
        competition_events = self.events_df[
            self.events_df['matchId'].isin(competition_matches)
        ]
        
        return sorted(competition_events['teamName'].unique().tolist())
    
    def get_all_teams(self) -> List[str]:
        """Get list of all available teams across all competitions."""
        if self.events_df is None:
            return []
        return sorted(self.events_df['teamName'].unique().tolist())
    
    def load_event_matches(
        self, 
        competition: Optional[str] = None,
        team: Optional[str] = None,
        max_number_of_matches: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Load events data with optional filtering.
        
        Args:
            competition: Filter by competition ("H_EURO2024", "Q_EURO2025", "U21_EURO2025")
            team: Filter by team name (e.g., "Germany", "Spain")
            max_number_of_matches: Limit to a maximum number of matches
            
        Returns:
            Filtered events DataFrame
        """
        if self.events_df is None:
            raise ValueError("Events data not loaded")
        
        df = self.events_df.copy()
        
        # Filter by competition
        if competition:
            if competition not in self.get_competitions():
                raise ValueError(f"Invalid competition. Available: {self.get_competitions()}")
            
            competition_matches = [
                match_id for match_id, path in MATCH_ID_TO_PATH.items() 
                if path.startswith(competition)
            ]
            df = df[df['matchId'].isin(competition_matches)]
        
        # Filter by team (include all events from matches where the team plays)
        if team:
            available_teams = self.get_teams_by_competition(competition) if competition else self.get_all_teams()
            matching_team = [t for t in available_teams if t.startswith(team)]
            if not matching_team:
                raise ValueError(f"Team '{team}' not found. Available teams: {available_teams}")
            # Get all match IDs where the specified team played
            team_matches = df[df['teamName'] == matching_team[0]]['matchId'].unique()
            # Filter to include all events from those matches (both teams)
            df = df[df['matchId'].isin(team_matches)]
        # limit to max number of matches
        if max_number_of_matches is not None:
            unique_matches = df['matchId'].unique()[:max_number_of_matches]
            df = df[df['matchId'].isin(unique_matches)]
        
        return df
    

    def load_tracking_data(
        self, 
        match_id: int, 
        home_or_away: str = "both"
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Load tracking data for a specific match.
        
        Args:
            match_id: Match ID from events data
            home_or_away: "home", "away", or "both"
            
        Returns:
            Tracking DataFrame(s)
        """
        if match_id not in MATCH_ID_TO_PATH:
            raise ValueError(f"Match ID {match_id} not found")
        
        match_path = self.directories.DATA_PATH / MATCH_ID_TO_PATH[match_id]
        
        if not match_path.exists():
            raise FileNotFoundError(f"Match directory not found: {match_path}")
        
        tracking_files = {
            "home": match_path / "home.csv",
            "away": match_path / "away.csv"
        }
        
        # Check if files exist
        for side, file_path in tracking_files.items():
            if not file_path.exists():
                raise FileNotFoundError(f"Tracking file not found: {file_path}")
        
        if home_or_away == "both":
            home_df = pd.read_csv(tracking_files["home"])
            away_df = pd.read_csv(tracking_files["away"])
            return home_df, away_df
        elif home_or_away in ["home", "away"]:
            return pd.read_csv(tracking_files[home_or_away])
        else:
            raise ValueError("home_or_away must be 'home', 'away', or 'both'")
    
    
    def get_tracking_from_events_data(self, df_event: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get tracking data corresponding to the provided event data.
        
        For each event, finds the closest tracking frame and returns
        home and away tracking DataFrames.
        
        Args:
            df_event: DataFrame with event data containing columns:
                     matchId, matchPeriod, matchTimestamp, and other event info
                     
        Returns:
            Tuple of (home_tracking_df, away_tracking_df) containing:
                - home_tracking_df: Home team tracking data
                - away_tracking_df: Away team tracking data
        """
        if df_event.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        all_home_tracking = []
        all_away_tracking = []
        
        # Group events by match to minimize I/O
        for match_id in df_event['matchId'].unique():
            match_events = df_event[df_event['matchId'] == match_id].copy()
            
            try:
                # Load tracking data for this match
                tracking_result = self.load_tracking_data(match_id, "both")
                if isinstance(tracking_result, tuple):
                    home_tracking, away_tracking = tracking_result
                else:
                    raise ValueError(f"Expected tuple for match {match_id}")
                
                # Process each event in this match
                for event_idx, event_row in match_events.iterrows():
                    try:
                        # Extract half and time from event
                        half, time_passed_in_half = extract_half_and_time_passed_in_half(event_row)
                        
                        if half is None:
                            continue  # Skip events with invalid periods
                        
                        # Find closest tracking frame for home team
                        closest_timestamp = _timestamp_helper(half, time_passed_in_half, home_tracking)
                        
                        # Get home team tracking data for this timestamp
                        home_frame = home_tracking[
                            (home_tracking["half"] == half) & 
                            (home_tracking["time_passed_in_half"] == closest_timestamp)
                        ]
                        
                        # Get away team tracking data for this timestamp
                        away_frame = away_tracking[
                            (away_tracking["half"] == half) & 
                            (away_tracking["time_passed_in_half"] == closest_timestamp)
                        ]
                        
                        if home_frame.empty or away_frame.empty:
                            continue  # Skip if no tracking data found
                        
                        # Add event_id to the tracking frames for reference
                        home_frame_copy = home_frame.copy()
                        away_frame_copy = away_frame.copy()
                        
                        home_frame_copy['event_id'] = event_row['eventId']
                        away_frame_copy['event_id'] = event_row['eventId']
                        
                        all_home_tracking.append(home_frame_copy)
                        all_away_tracking.append(away_frame_copy)
                        
                    except Exception as e:
                        print(f"Warning: Could not process event {event_idx} in match {match_id}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Warning: Could not load tracking data for match {match_id}: {e}")
                continue
        
        if not all_home_tracking or not all_away_tracking:
            return pd.DataFrame(), pd.DataFrame()
        
        # Combine all tracking data
        combined_home_tracking = pd.concat(all_home_tracking, ignore_index=True)
        combined_away_tracking = pd.concat(all_away_tracking, ignore_index=True)
        
        return combined_home_tracking, combined_away_tracking
    
