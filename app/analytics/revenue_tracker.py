"""
Revenue Tracker — Tracks revenue collected, lost, and recoverable.
"""
from app.database import fetch_all, fetch_one


class RevenueTracker:
    async def get_revenue_summary(self, days: int = 7) -> dict:
        """Total collected, total lost, recovery rate."""
        result = await fetch_one(
            "SELECT "
            "COALESCE(SUM(CASE WHEN status='paid' THEN amount ELSE 0 END), 0) as collected, "
            "COALESCE(SUM(CASE WHEN status='failed' THEN amount ELSE 0 END), 0) as lost, "
            "COALESCE(SUM(CASE WHEN status='refunded' THEN amount ELSE 0 END), 0) as refunded, "
            "COALESCE(SUM(CASE WHEN status='attempted' THEN amount ELSE 0 END), 0) as abandoned, "
            "COUNT(*) as total_count "
            "FROM payments WHERE created_at >= datetime('now', ?)",
            (f"-{days} days",)
        )
        if not result:
            return {"collected": 0, "lost": 0, "refunded": 0, "abandoned": 0}
        collected = result["collected"] or 0
        lost = result["lost"] or 0
        return {
            "collected_paise": collected,
            "collected_inr": round(collected / 100, 2),
            "lost_paise": lost,
            "lost_inr": round(lost / 100, 2),
            "refunded_inr": round((result["refunded"] or 0) / 100, 2),
            "abandoned_inr": round((result["abandoned"] or 0) / 100, 2),
            "total_count": result["total_count"] or 0
        }

    async def get_daily_revenue(self, days: int = 30) -> list:
        """Daily revenue collected and lost."""
        return await fetch_all(
            "SELECT date(created_at) as date, "
            "COALESCE(SUM(CASE WHEN status='paid' THEN amount ELSE 0 END), 0) as collected, "
            "COALESCE(SUM(CASE WHEN status='failed' THEN amount ELSE 0 END), 0) as lost "
            "FROM payments WHERE created_at >= datetime('now', ?) "
            "GROUP BY date(created_at) ORDER BY date",
            (f"-{days} days",)
        )

    async def get_revenue_by_method(self, days: int = 7) -> list:
        """Revenue per payment method."""
        return await fetch_all(
            "SELECT method, "
            "COALESCE(SUM(CASE WHEN status='paid' THEN amount ELSE 0 END), 0) as revenue, "
            "COUNT(*) as count "
            "FROM payments WHERE method IS NOT NULL AND created_at >= datetime('now', ?) "
            "GROUP BY method ORDER BY revenue DESC",
            (f"-{days} days",)
        )

    async def get_recoverable_revenue(self) -> dict:
        """Estimate how much lost revenue could be recovered."""
        result = await fetch_one(
            "SELECT COALESCE(SUM(amount), 0) as recoverable "
            "FROM payments WHERE status='failed' AND failure_reason IN ('insufficient_funds', 'timeout', 'network_error')"
        )
        total = (result["recoverable"] or 0) if result else 0
        return {
            "recoverable_paise": total,
            "recoverable_inr": round(total / 100, 2),
            "estimated_recovery_rate": 0.3,
            "estimated_recovery_inr": round(total * 0.3 / 100, 2)
        }
