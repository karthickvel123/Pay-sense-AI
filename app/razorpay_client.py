"""
Razorpay API Client Wrapper — High performance async client using httpx.
Directly communicates with Razorpay REST v1 APIs using HTTP Basic Auth.
Completely avoids pkg_resources deprecation issues in modern Python environments.
"""
import httpx
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://api.razorpay.com/v1"


class RazorpayClient:
    def __init__(self, key_id: str, key_secret: str):
        self.key_id = key_id
        self.key_secret = key_secret
        self.auth = (key_id, key_secret)

    async def create_order(self, amount: int, currency: str = 'INR', notes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new Razorpay order (amount in paise)."""
        payload = {
            "amount": amount,
            "currency": currency,
            "notes": notes or {}
        }
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{BASE_URL}/orders",
                    auth=self.auth,
                    json=payload,
                    timeout=15.0
                )
                if res.status_code in (200, 201):
                    return {"status": "success", "data": res.json()}
                else:
                    logger.error(f"Razorpay order error: {res.text}")
                    return {"status": "error", "error": res.json().get("error", {}).get("description", res.text)}
        except Exception as e:
            logger.error(f"Exception creating Razorpay order: {e}")
            return {"status": "error", "error": str(e)}

    async def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch order details by order_id."""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{BASE_URL}/orders/{order_id}",
                    auth=self.auth,
                    timeout=15.0
                )
                if res.status_code == 200:
                    return {"status": "success", "data": res.json()}
                return {"status": "error", "error": res.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch payment details by payment_id."""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{BASE_URL}/payments/{payment_id}",
                    auth=self.auth,
                    timeout=15.0
                )
                if res.status_code == 200:
                    return {"status": "success", "data": res.json()}
                return {"status": "error", "error": res.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def fetch_payments_for_order(self, order_id: str) -> List[Dict[str, Any]]:
        """Fetch all payments associated with an order."""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{BASE_URL}/orders/{order_id}/payments",
                    auth=self.auth,
                    timeout=15.0
                )
                if res.status_code == 200:
                    return {"status": "success", "data": res.json().get("items", [])}
                return {"status": "error", "error": res.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def capture_payment(self, payment_id: str, amount: int, currency: str = 'INR') -> Dict[str, Any]:
        """Capture an authorized payment."""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{BASE_URL}/payments/{payment_id}/capture",
                    auth=self.auth,
                    json={"amount": amount, "currency": currency},
                    timeout=15.0
                )
                if res.status_code == 200:
                    return {"status": "success", "data": res.json()}
                return {"status": "error", "error": res.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def refund_payment(self, payment_id: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """Issue a full or partial refund."""
        payload = {}
        if amount:
            payload["amount"] = amount
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{BASE_URL}/payments/{payment_id}/refund",
                    auth=self.auth,
                    json=payload,
                    timeout=15.0
                )
                if res.status_code == 200:
                    return {"status": "success", "data": res.json()}
                return {"status": "error", "error": res.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def fetch_all_payments(self, count: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Fetch merchant's recent payments from Razorpay."""
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{BASE_URL}/payments",
                    auth=self.auth,
                    params={"count": count, "skip": skip},
                    timeout=15.0
                )
                if res.status_code == 200:
                    return {"status": "success", "data": res.json().get("items", [])}
                return {"status": "error", "error": res.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}
