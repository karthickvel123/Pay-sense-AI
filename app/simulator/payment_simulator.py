import random
import uuid
import datetime
import json
from app.database import execute_query, init_db

class PaymentSimulator:
    async def generate_payment_history(self, num_payments: int = 200) -> list:
        await init_db()
        
        statuses = ["paid", "failed", "attempted", "refunded"]
        status_weights = [0.72, 0.15, 0.08, 0.05]
        
        failure_reasons = ["bank_declined", "timeout", "insufficient_funds", "network_error", "fraud_flagged"]
        failure_weights = [0.35, 0.25, 0.20, 0.10, 0.10]
        
        methods = ["upi", "card", "netbanking", "wallet"]
        method_weights = [0.45, 0.30, 0.15, 0.10]
        
        generated_data = []
        
        # Base repeat customer tracking
        customer_emails = [f"customer{i}@example.com" for i in range(50)]
        customer_phones = [f"+9198765{str(i).zfill(5)}" for i in range(50)]
        
        for _ in range(num_payments):
            status = random.choices(statuses, weights=status_weights)[0]
            method = random.choices(methods, weights=method_weights)[0] if status != "attempted" else None
            
            amount = random.randint(100, 50000) * 100 # paise
            
            customer_idx = random.randint(0, len(customer_emails) - 1)
            email = customer_emails[customer_idx]
            phone = customer_phones[customer_idx]
            
            # Generate realistic timestamp within last 30 days
            days_ago = random.randint(0, 30)
            # Bias towards business hours (9 AM to 6 PM)
            hour = int(random.choices(
                list(range(24)), 
                weights=[1]*9 + [5]*10 + [2]*5
            )[0])
            
            timestamp = datetime.datetime.now() - datetime.timedelta(days=days_ago, hours=hour, minutes=random.randint(0, 59))
            
            id_val = f"pay_{uuid.uuid4().hex[:14]}"
            order_id = f"order_{uuid.uuid4().hex[:14]}"
            
            failure_reason = None
            error_code = None
            if status == "failed":
                failure_reason = random.choices(failure_reasons, weights=failure_weights)[0]
                error_code = f"ERR_{failure_reason.upper()}"
            
            notes = json.dumps({"source": "simulator"})
            
            # Insert to DB
            query = '''
                INSERT INTO payments 
                (id, razorpay_order_id, razorpay_payment_id, amount, status, method, failure_reason, error_code, customer_email, customer_phone, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                id_val, order_id, id_val if status != "attempted" else None, amount, 
                status, method, failure_reason, error_code, email, phone, notes, 
                timestamp.strftime('%Y-%m-%d %H:%M:%S'), timestamp.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            await execute_query(query, params)
            
            generated_data.append({
                "id": id_val,
                "status": status,
                "amount": amount
            })
            
        return generated_data
