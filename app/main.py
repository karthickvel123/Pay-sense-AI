from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    from app.database import init_db, fetch_one
    await init_db()

    # Auto-seed realistic transactions if the database is fresh/empty
    try:
        count_row = await fetch_one("SELECT COUNT(*) as count FROM payments")
        if not count_row or (count_row.get("count") or 0) == 0:
            from app.simulator.payment_simulator import PaymentSimulator
            simulator = PaymentSimulator()
            await simulator.generate_payment_history(num_payments=150)

            from app.agent.tools import create_recovery_action
            await create_recovery_action(
                action_type="initial_baseline_scan",
                target_payment_id="system_init"
            )
    except Exception as e:
        print(f"Auto-seed warning: {e}")

    yield

app = FastAPI(
    title='PaySense AI',
    description='Agentic Revenue Recovery & Payment Intelligence',
    version='1.0.0',
    lifespan=lifespan
)

# Include routers
from app.routers import payments, agent, dashboard
app.include_router(payments.router)
app.include_router(agent.router)
app.include_router(dashboard.router)

# Serve static files
os.makedirs('static', exist_ok=True)
app.mount('/static', StaticFiles(directory='static'), name='static')

@app.get('/')
async def root():
    return FileResponse('static/index.html')

@app.get('/styles.css')
async def styles():
    return FileResponse('static/styles.css', media_type='text/css')

@app.get('/app.js')
async def script():
    return FileResponse('static/app.js', media_type='application/javascript')
