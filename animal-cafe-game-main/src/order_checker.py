# order_checker.py - Validates player-assembled orders and awards points
# Owner: Sana
from src.constants import POINTS_PERFECT, POINTS_GOOD, POINTS_MISS


class OrderChecker:
    # Checks whether the player's assembled order matches the customer's request.

    def __init__(self):
        # Running totals for the current round.
        self.total_score = 0
        self.orders_completed = 0
        self.orders_missed = 0

    def _evaluate_order(self, required_ingredients: list, player_ingredients: list,
                        patience_ratio: float) -> dict:
        # Compare player's assembled ingredients against the required ones.
        required_set = set(required_ingredients)
        player_set = set(player_ingredients)

        if player_set == required_set:
            # Perfect match — bonus points for serving quickly
            bonus = int(POINTS_PERFECT * patience_ratio * 0.5)
            points = POINTS_PERFECT + bonus
            result = "perfect"
            message = f"Perfect! +{points} pts"
        elif required_set.issubset(player_set) or player_set.issubset(required_set):
            # Partial match (missing or extra ingredient)
            points = POINTS_GOOD
            result = "good"
            missing = required_set - player_set
            extra = player_set - required_set
            parts = []
            if missing:
                parts.append(f"Missing: {', '.join(missing)}")
            if extra:
                parts.append(f"Extra: {', '.join(extra)}")
            message = f"Close! +{points} pts. " + " | ".join(parts)
        else:
            # Wrong order (ingredients do not substantially overlap).
            points = POINTS_MISS
            result = "miss"
            message = f"Wrong order! {points} pts"

        return {"result": result, "points": points, "message": message}

    def preview_check_order(self, required_ingredients: list, player_ingredients: list,
                            patience_ratio: float) -> dict:
        # Preview score/result for matching without mutating totals.
        return self._evaluate_order(required_ingredients, player_ingredients, patience_ratio)

    def check_order(self, required_ingredients: list, player_ingredients: list,
                    patience_ratio: float) -> dict:
        # Apply order result to score and completion counters.
        # Evaluate first, then commit to score/counter changes.
        outcome = self._evaluate_order(required_ingredients, player_ingredients, patience_ratio)
        self.total_score += outcome["points"]

        if outcome["result"] in ("perfect", "good"):
            self.orders_completed += 1
        else:
            self.orders_missed += 1

        return outcome

    def customer_left_without_serving(self):
        # Called when a customer's patience runs out.
        # Miss penalty applies if customer leaves before being served.
        self.total_score += POINTS_MISS
        self.orders_missed += 1

    def get_summary(self) -> dict:
        # Return end-of-game stats.
        total = self.orders_completed + self.orders_missed
        accuracy = (self.orders_completed / total * 100) if total > 0 else 0
        return {
            "score": self.total_score,
            "completed": self.orders_completed,
            "missed": self.orders_missed,
            "accuracy": round(accuracy, 1),
        }
