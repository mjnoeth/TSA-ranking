import json
import pandas as pd
from typing import List, Dict, Tuple, Optional

# Sample data structure representing the dual meet results parsed from the schedule
# Each meet record: {"winner": str, "loser": str, "margin": int, "is_division": bool}

class TSARanker:
    def __init__(self, teams: List[Dict], meets: List[Dict]):

        self.teams = {t["name"]: t for t in teams}
        self.meets = meets
        self.hth_matrix = {}
        self._build_hth_matrix()

    def _build_hth_matrix(self):
        for meet in self.meets:
            w, l, m = meet["winner"], meet["loser"], meet["margin"]
            self.hth_matrix[(w, l)] = m
            self.hth_matrix[(l, w)] = -m

    def get_hth_margin(self, team_a: str, team_b: str) -> Optional[int]:
        return self.hth_matrix.get((team_a, team_b), None)

    def get_copd(self, team_a: str, team_b: str) -> float:
        """Calculates Common Opponent Point Differential between two teams."""
        opponents_a = {
            m["loser"] if m["winner"] == team_a else m["winner"]
            for m in self.meets
            if m["winner"] == team_a or m["loser"] == team_a
        }
        opponents_b = {
            m["loser"] if m["winner"] == team_b else m["winner"]
            for m in self.meets
            if m["winner"] == team_b or m["loser"] == team_b
        }
        
        common = opponents_a.intersection(opponents_b)
        if not common:
            return 0.0

        copd_sum = 0
        for opp in common:
            margin_a = self.get_hth_margin(team_a, opp)
            margin_b = self.get_hth_margin(team_b, opp)
            if margin_a is not None and margin_b is not None:
                copd_sum += (margin_a - margin_b)
                
        return copd_sum / len(common)

    def calculate_objective_score(self, team_name: str) -> float:
        """
        Calculates a quantifiable rating score.
        Higher score = stronger team (higher ranking).
        """
        team = self.teams[team_name]
        
        # 1. Base Score derived from In-Division Win % and Overall Win %
        div_wins, div_losses = team["div_record"]
        div_win_pct = div_wins / (div_wins + div_losses) if (div_wins + div_losses) > 0 else 0
        
        ovr_wins, ovr_losses = team["ovr_record"]
        ovr_win_pct = ovr_wins / (ovr_wins + ovr_losses) if (ovr_wins + ovr_losses) > 0 else 0
        
        # Division Winner / Loser Bonuses
        div_bonus = 50.0 if team.get("is_div_winner") else ( -50.0 if team.get("is_div_loser") else 0.0 )

        # Baseline rating from previous rank (invert so 1 is high)
        base_rating = (100 - team["2026_rank"]) * 10
        
        # Aggregate Rating
        rating = base_rating + (div_win_pct * 100) + (ovr_win_pct * 50) + div_bonus
        return rating

    def rank_league(self) -> List[Tuple[int, str, float]]:
        """Ranks teams objectively and resolves head-to-head / COPD conflicts."""
        # Initial sorting by objective rating
        scores = {t: self.calculate_objective_score(t) for t in self.teams}
        ranked_teams = sorted(self.teams.keys(), key=lambda t: scores[t], reverse=True)

        # Bubble-pass to resolve direct HTH and COPD ties between adjacent ranks
        n = len(ranked_teams)
        for i in range(n):
            for j in range(0, n - i - 1):
                t1, t2 = ranked_teams[j], ranked_teams[j+1]
                
                # Check HTH
                hth = self.get_hth_margin(t1, t2)
                if hth is not None:
                    # If t2 beat t1 directly, swap them
                    if hth < 0:
                        ranked_teams[j], ranked_teams[j+1] = ranked_teams[j+1], ranked_teams[j]
                else:
                    # Check COPD if no direct HTH
                    copd = self.get_copd(t1, t2)
                    if copd < -10.0:  # Clear COPD advantage to t2
                        ranked_teams[j], ranked_teams[j+1] = ranked_teams[j+1], ranked_teams[j]

        return [(idx + 1, team, scores[team]) for idx, team in enumerate(ranked_teams)]

# Example execution template
if __name__ == "__main__":
    print("TSA Objective Ranking Algorithm Initialized.")
