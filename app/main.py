from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    from app.database import init_db
    await init_db()
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
