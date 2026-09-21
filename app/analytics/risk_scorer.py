"""
Risk Scorer — Scores payments for chargeback/fraud risk.
"""
from app.database import fetch_all, fetch_one


class RiskScorer:
    async def score_payment(self, payment_data: dict) -> dict:
        """Score a single payment for risk. Returns score 0-100 and factors."""
        score = 10
        factors = []

        amount = payment_data.get("amount", 0)
        if amount > 2000000:  # > ₹20,000
            score += 30
            factors.append({"factor": "high_value", "detail": f"Amount ₹{amount/100:.0f} exceeds ₹20,000"})
        elif amount > 1000000:  # > ₹10,000
            score += 15
            factors.append({"factor": "elevated_value", "detail": f"Amount ₹{amount/100:.0f} exceeds ₹10,000"})

        if payment_data.get("method") == "card":
            score += 15
            factors.append({"factor": "card_payment", "detail": "Card payments carry higher chargeback risk"})

        if payment_data.get("status") == "failed":
            score += 20
            factors.append({"factor": "failed_transaction", "detail": "Previously failed — higher risk on retry"})

        return {"score": min(score, 100), "level": "low" if score < 30 else "medium" if score < 60 else "high", "factors": factors}

    async def get_high_risk_payments(self, threshold: int = 70) -> list:
        """Get payments that are high-risk based on amount and method heuristics."""
        return await fetch_all(
            "SELECT id, amount, method, status, customer_email, created_at "
            "FROM payments WHERE amount > 2000000 AND method='card' "
            "ORDER BY amount DESC LIMIT 20"
        )

    async def get_risk_distribution(self) -> dict:
        """Distribution of risk levels across all payments."""
        # Compute risk based on amount thresholds since we don't store risk_score
        low = await fetch_one("SELECT COUNT(*) as count FROM payments WHERE amount <= 1000000")
        medium = await fetch_one("SELECT COUNT(*) as count FROM payments WHERE amount > 1000000 AND amount <= 2000000")
        high = await fetch_one("SELECT COUNT(*) as count FROM payments WHERE amount > 2000000")

        return {
            "low": (low["count"] if low else 0),
            "medium": (medium["count"] if medium else 0),
            "high": (high["count"] if high else 0)
        }
