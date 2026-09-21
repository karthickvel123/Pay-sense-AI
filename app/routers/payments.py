"""
Payments router — CRUD endpoints for payment operations and simulation.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import fetch_all, fetch_one
from app.razorpay_client import RazorpayClient
from app.simulator.payment_simulator import PaymentSimulator
from app.config import settings

router = APIRouter(prefix='/api/payments', tags=['payments'])
simulator = PaymentSimulator()


def get_razorpay_client() -> RazorpayClient:
    """Get Razorpay client (may not be configured)."""
    if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
        return RazorpayClient(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    return None


class OrderRequest(BaseModel):
    amount: int
    currency: str = 'INR'


class SimulateRequest(BaseModel):
    count: int = 200


@router.post('/orders')
async def create_order(order: OrderRequest) -> dict:
    """Create a new order via Razorpay API."""
    client = get_razorpay_client()
    if not client:
        return {"status": "error", "error": "Razorpay not configured. Add keys to .env"}
    return await client.create_order(amount=order.amount, currency=order.currency)


@router.get('/orders/{order_id}')
async def get_order(order_id: str) -> dict:
    """Fetch order details from Razorpay."""
    client = get_razorpay_client()
    if not client:
        return {"status": "error", "error": "Razorpay not configured"}
    return await client.fetch_order(order_id)


@router.get('/')
async def list_payments() -> list:
    """List all payments from the local database."""
    return await fetch_all(
        "SELECT id, razorpay_order_id, amount, status, method, failure_reason, "
        "customer_email, created_at FROM payments ORDER BY created_at DESC LIMIT 100"
    )


@router.get('/{payment_id}')
async def get_payment(payment_id: str) -> dict:
    """Get a single payment by ID."""
    payment = await fetch_one("SELECT * FROM payments WHERE id=?", (payment_id,))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return dict(payment)


@router.post('/simulate')
async def simulate_payments(data: SimulateRequest = SimulateRequest()) -> dict:
    """Generate simulated payment data for demo purposes."""
    try:
        results = await simulator.generate_payment_history(num_payments=data.count)
        paid = sum(1 for r in results if r["status"] == "paid")
        failed = sum(1 for r in results if r["status"] == "failed")
        return {
            "status": "success",
            "message": f"Generated {len(results)} payments ({paid} paid, {failed} failed)",
            "count": len(results)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
