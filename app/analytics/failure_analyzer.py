"""
Failure Analyzer — Analyzes payment failure patterns from the database.
"""
from app.database import fetch_all, fetch_one


class FailureAnalyzer:
    async def get_failure_summary(self, days: int = 7) -> dict:
        """Overall failure statistics."""
        result = await fetch_one(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed, "
            "SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) as paid "
            "FROM payments WHERE created_at >= datetime('now', ?)",
            (f"-{days} days",)
        )
        if not result:
            return {"total": 0, "failed": 0, "paid": 0, "failure_rate": 0.0, "success_rate": 0.0}
        total = result.get("total", 0) or 0
        failed = result.get("failed", 0) or 0
        paid = result.get("paid", 0) or 0
        return {
            "total": total,
            "failed": failed,
            "paid": paid,
            "failure_rate": round(failed / total * 100, 2) if total > 0 else 0,
            "success_rate": round(paid / total * 100, 2) if total > 0 else 0
        }

    async def get_failure_by_reason(self, days: int = 7) -> list:
        """Breakdown by failure reason with counts."""
        return await fetch_all(
            "SELECT failure_reason as reason, COUNT(*) as count "
            "FROM payments WHERE status='failed' AND created_at >= datetime('now', ?) "
            "GROUP BY failure_reason ORDER BY count DESC",
            (f"-{days} days",)
        )

    async def get_failure_by_method(self, days: int = 7) -> list:
        """Breakdown by payment method."""
        return await fetch_all(
            "SELECT method, COUNT(*) as total, "
            "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed, "
            "ROUND(SUM(CASE WHEN status='failed' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as failure_rate "
            "FROM payments WHERE created_at >= datetime('now', ?) AND method IS NOT NULL "
            "GROUP BY method ORDER BY failed DESC",
            (f"-{days} days",)
        )

    async def get_failure_trends(self, days: int = 30) -> list:
        """Daily failure and success counts for trend analysis."""
        return await fetch_all(
            "SELECT date(created_at) as date, COUNT(*) as total, "
            "SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) as paid, "
            "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed "
            "FROM payments WHERE created_at >= datetime('now', ?) "
            "GROUP BY date(created_at) ORDER BY date",
            (f"-{days} days",)
        )

    async def get_repeat_failures(self, min_count: int = 2) -> list:
        """Customers with recurring failures."""
        return await fetch_all(
            "SELECT customer_email, COUNT(*) as fail_count, SUM(amount) as total_lost "
            "FROM payments WHERE status='failed' "
            "GROUP BY customer_email HAVING fail_count >= ? ORDER BY fail_count DESC LIMIT 20",
            (min_count,)
        )
