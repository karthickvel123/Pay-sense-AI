from fastapi import APIRouter
from app.analytics.failure_analyzer import FailureAnalyzer
from app.analytics.revenue_tracker import RevenueTracker
from app.analytics.risk_scorer import RiskScorer

router = APIRouter(prefix='/api/dashboard', tags=['dashboard'])

failure_analyzer = FailureAnalyzer()
revenue_tracker = RevenueTracker()
risk_scorer = RiskScorer()

@router.get('/overview')
async def get_overview() -> dict:
    revenue = await revenue_tracker.get_revenue_summary()
    failures = await failure_analyzer.get_failure_summary()
    return {
        "revenue": revenue,
        "failures": failures
    }

@router.get('/failures')
async def get_failures_data() -> dict:
    reasons = await failure_analyzer.get_failure_by_reason()
    methods = await failure_analyzer.get_failure_by_method()
    return {
        "by_reason": reasons,
        "by_method": methods
    }

@router.get('/revenue')
async def get_revenue_data() -> dict:
    summary = await revenue_tracker.get_revenue_summary()
    by_method = await revenue_tracker.get_revenue_by_method()
    return {
        "summary": summary,
        "by_method": by_method
    }

@router.get('/trends')
async def get_trends() -> dict:
    failure_trends = await failure_analyzer.get_failure_trends()
    revenue_trends = await revenue_tracker.get_daily_revenue()
    return {
        "failures": failure_trends,
        "revenue": revenue_trends
    }

@router.get('/leaks')
async def get_leaks() -> dict:
    recoverable = await revenue_tracker.get_recoverable_revenue()
    return {"recoverable_estimate": recoverable}

@router.get('/risk')
async def get_risk() -> dict:
    distribution = await risk_scorer.get_risk_distribution()
    return {"distribution": distribution}
