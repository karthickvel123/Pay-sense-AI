# 🧠 PaySense AI — Agentic Revenue Recovery & Payment Intelligence

> An AI-powered payment operations agent that autonomously monitors payment health, detects revenue leaks, and takes bounded recovery actions — built with Razorpay APIs + Google Gemini.

**Built for the [Razorpay AI Builders](https://razorpay.com/ai-builders/) program.**

---

## 🎯 What Problem Does This Solve?

Indian merchants lose **₹2,800 Cr+ annually** to failed payments, abandoned checkouts, and preventable chargebacks. Most merchants discover these leaks only when reviewing monthly statements — days or weeks too late.

**PaySense AI** is an autonomous agent that:
- 🔍 **Continuously monitors** your payment ecosystem in real-time
- 📊 **Detects revenue leaks** — failed payments, abandoned orders, recurring failure patterns
- 🤖 **Diagnoses root causes** — bank declines, timeouts, insufficient funds, fraud flags
- 💡 **Recommends recovery strategies** — optimal retry timing, payment method switching, customer re-engagement
- ⚡ **Takes bounded actions** — generates payment links, flags high-risk transactions, schedules retries
- 📝 **Maintains audit trails** — every AI decision is logged with reasoning and confidence

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PaySense AI Agent                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Conversational│  │ Autonomous   │  │ Decision      │  │
│  │ Interface    │  │ Monitor      │  │ Engine        │  │
│  │ (Chat UI)    │  │ (Health Scan)│  │ (Gemini LLM)  │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                   │          │
│  ┌──────▼─────────────────▼───────────────────▼───────┐  │
│  │              Tool / Action Layer (6 Tools)          │  │
│  │  🔧 analyze_payment_failures                       │  │
│  │  🔧 detect_revenue_leaks                           │  │
│  │  🔧 recommend_retry_strategy                       │  │
│  │  🔧 generate_health_report                         │  │
│  │  🔧 assess_chargeback_risk                         │  │
│  │  🔧 create_recovery_action                         │  │
│  └────────────────────────┬───────────────────────────┘  │
│  ┌────────────────────────▼───────────────────────────┐  │
│  │     Data Layer (SQLite + Razorpay Test APIs)        │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack
| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | Python + FastAPI | Async, fast, production-grade |
| AI Engine | Google Gemini 2.5 Flash (Function Calling) | Best-in-class agentic capabilities |
| Database | SQLite (aiosqlite) | Zero-config, portable |
| Frontend | Vanilla HTML/CSS/JS + Chart.js | No framework bloat, fast load |
| Payments | Razorpay Test Mode API | Real integration, not mocked |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- A [Razorpay Test Account](https://dashboard.razorpay.com/signup) (free, instant)
- A [Google Gemini API Key](https://aistudio.google.com/apikey) (free tier works)

### Setup

```bash
# 1. Clone and navigate
cd paysense-ai

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

# 5. Edit .env with your keys
# RAZORPAY_KEY_ID=rzp_test_xxxxx
# RAZORPAY_KEY_SECRET=your_secret
# GEMINI_API_KEY=your_gemini_key
```

### Run

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser.

### First Steps
1. Click **"Simulate Payments"** to generate 200 realistic test transactions
2. Watch the dashboard populate with metrics, charts, and alerts
3. Chat with the AI agent: *"Why are my payments failing?"*
4. Try: *"Show me revenue leaks"* or *"What's my chargeback risk?"*
5. Click **"Run Health Scan"** for an autonomous analysis

---

## 🤖 AI Agent — Function Calling in Action

The agent uses **Gemini 2.5 Flash** with 6 registered tools. Here's how a typical interaction works:

```
User: "Why are my UPI payments failing?"

Agent thinks → calls analyze_payment_failures(time_window_days=7)
Agent thinks → calls recommend_retry_strategy(failure_type="timeout")
Agent responds:

  "Based on analysis of the last 7 days:

   🔴 Your UPI failure rate is 18.3% (27 out of 147 UPI payments)
   
   Top failure reasons:
   • Timeout: 12 failures (44%) — likely PSP node issues
   • Bank declined: 8 failures (30%) — customer bank-side
   • Network error: 7 failures (26%) — intermittent connectivity
   
   📋 Recommendations:
   1. Implement 15-minute retry for timeout failures (expected 25% recovery)
   2. Suggest card/netbanking for customers with 2+ UPI failures
   3. Peak failure hours are 10:00-11:00 — avoid batch retries then"
```

Every tool call is **logged in the audit trail** and visible in the dashboard.

---

## 📊 Dashboard Features

- **4 Key Metrics**: Revenue, Success Rate, Revenue Lost, Health Score
- **Payment Trends**: 30-day line chart (paid vs failed)
- **Failure Breakdown**: Doughnut chart by failure reason
- **Revenue by Method**: Bar chart comparing UPI, Card, Netbanking, Wallet
- **Risk Distribution**: Low/Medium/High risk payment breakdown
- **AI Alerts**: Real-time alerts generated from payment anomalies
- **Agent Decision Log**: Full audit trail of every AI decision

---

## 🛡️ Why This Matters for Fintech

1. **Bounded AI** — The agent can suggest and execute recovery actions, but destructive operations require explicit confirmation. Every action is auditable.
2. **Compliance-Ready** — Full decision audit trail with timestamps, reasoning, and confidence scores.
3. **Real API Integration** — Not a demo with fake data. Connects to Razorpay's actual test APIs.
4. **Production Architecture** — Async Python, proper error handling, graceful degradation when APIs fail.

---

## 📁 Project Structure

```
paysense-ai/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Environment configuration
│   ├── database.py              # SQLite async operations
│   ├── razorpay_client.py       # Razorpay SDK wrapper
│   ├── agent/
│   │   ├── engine.py            # Gemini agent with function calling loop
│   │   ├── tools.py             # 6 database-backed analysis tools
│   │   └── prompts.py           # Expert system prompt
│   ├── analytics/
│   │   ├── failure_analyzer.py  # Payment failure pattern analysis
│   │   ├── revenue_tracker.py   # Revenue tracking & leak detection
│   │   └── risk_scorer.py       # Chargeback risk scoring
│   ├── simulator/
│   │   └── payment_simulator.py # Realistic test data generator
│   └── routers/
│       ├── payments.py          # Payment CRUD + simulation
│       ├── agent.py             # Chat & autonomous scan
│       └── dashboard.py         # Dashboard data endpoints
├── static/
│   ├── index.html               # Dashboard + Chat UI
│   ├── styles.css               # Dark fintech theme
│   └── app.js                   # Frontend logic
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔮 Future Enhancements
- Webhook listener for real-time Razorpay payment events
- Multi-merchant support with tenant isolation
- Scheduled autonomous scans with email/Slack alerts
- Integration with Razorpay Route for split payment analysis
- Custom ML model for payment success prediction

---

## 👤 Author

Built for the **Razorpay AI Builders** program — demonstrating end-to-end AI product engineering in fintech.

## 📄 License

MIT
