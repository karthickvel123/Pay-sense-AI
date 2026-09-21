"""
PaySense AI Agent Engine — Supports Gemini 2.5 Flash function calling
with graceful fallback to an autonomous local heuristic engine when offline or keyless.
"""
import logging
from typing import Optional, List, Dict, Any
from app.agent.prompts import SYSTEM_PROMPT
import app.agent.tools as agent_tools

logger = logging.getLogger(__name__)


class PaySenseAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = 'gemini-2.5-flash'
        self.conversation_history = []
        self.client = None

        self.tool_map = {
            "analyze_payment_failures": agent_tools.analyze_payment_failures,
            "detect_revenue_leaks": agent_tools.detect_revenue_leaks,
            "recommend_retry_strategy": agent_tools.recommend_retry_strategy,
            "generate_health_report": agent_tools.generate_health_report,
            "assess_chargeback_risk": agent_tools.assess_chargeback_risk,
            "create_recovery_action": agent_tools.create_recovery_action
        }

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                self._setup_tools()
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}. Falling back to local agent.")
                self.client = None

    def _setup_tools(self):
        """Register all 6 tools as Gemini function declarations."""
        from google.genai import types
        self.tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="analyze_payment_failures",
                        description="Analyze payment failures in the given time window.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "time_window_days": types.Schema(type=types.Type.INTEGER, description="Time window in days")
                            }
                        )
                    ),
                    types.FunctionDeclaration(
                        name="detect_revenue_leaks",
                        description="Detect revenue leaks - money lost due to failures.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "time_window_days": types.Schema(type=types.Type.INTEGER, description="Time window in days")
                            }
                        )
                    ),
                    types.FunctionDeclaration(
                        name="recommend_retry_strategy",
                        description="Recommend retry strategies based on failure patterns.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "failure_type": types.Schema(type=types.Type.STRING, description="Type of failure")
                            }
                        )
                    ),
                    types.FunctionDeclaration(
                        name="generate_health_report",
                        description="Generate a comprehensive payment health scorecard.",
                    ),
                    types.FunctionDeclaration(
                        name="assess_chargeback_risk",
                        description="Assess chargeback risk for a specific payment or overall.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "payment_id": types.Schema(type=types.Type.STRING, description="Payment ID")
                            }
                        )
                    ),
                    types.FunctionDeclaration(
                        name="create_recovery_action",
                        description="Create a bounded recovery action.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "action_type": types.Schema(type=types.Type.STRING, description="Type of action: generate_payment_link, flag_for_review, schedule_retry, alert_merchant"),
                                "target_payment_id": types.Schema(type=types.Type.STRING, description="Target payment ID")
                            },
                            required=["action_type"]
                        )
                    )
                ]
            )
        ]

    async def chat(self, user_message: str) -> dict:
        """Process a user message through the agent."""
        if self.client:
            try:
                return await self._gemini_chat(user_message)
            except Exception as e:
                logger.warning(f"Gemini API error ({e}), switching to local agent.")
                return await self._local_chat(user_message)
        else:
            return await self._local_chat(user_message)

    async def _gemini_chat(self, user_message: str) -> dict:
        """Gemini function calling multi-turn loop."""
        from google.genai import types
        self.conversation_history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        tools_used = []
        reasoning = ""

        # Limit to 5 tool iterations to avoid infinite loops
        for _ in range(5):
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.conversation_history,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=self.tools
                )
            )

            if response.candidates and response.candidates[0].content:
                self.conversation_history.append(response.candidates[0].content)

            function_calls = response.function_calls or []
            if not function_calls:
                return {
                    "response": response.text or "Analysis completed.",
                    "tools_used": tools_used,
                    "reasoning": reasoning
                }

            function_responses = []
            for call in function_calls:
                tool_name = call.name
                args = call.args if call.args else {}
                tools_used.append(tool_name)

                if tool_name in self.tool_map:
                    try:
                        func = self.tool_map[tool_name]
                        result = await func(**args)
                        function_responses.append(types.Part.from_function_response(
                            name=tool_name,
                            response=result
                        ))
                    except Exception as e:
                        function_responses.append(types.Part.from_function_response(
                            name=tool_name,
                            response={"error": str(e)}
                        ))

            if function_responses:
                self.conversation_history.append(
                    types.Content(role="user", parts=function_responses)
                )

        return {
            "response": "Completed tool operations and synchronized telemetry.",
            "tools_used": tools_used,
            "reasoning": reasoning
        }

    async def _local_chat(self, user_message: str) -> dict:
        """Local autonomous agent that executes tools and generates expert reports."""
        msg_lower = user_message.lower()
        tools_used = []
        parts = []

        if any(w in msg_lower for w in ["scan", "health", "overview", "score", "status"]):
            tools_used.append("generate_health_report")
            health = await self.tool_map["generate_health_report"]()
            parts.append(
                f"### 📊 Payment Health Scorecard\n"
                f"- **Overall Health Score**: **{health.get('overall_health_score', 0)}/100**\n"
                f"- **Success Rate**: **{health.get('success_rate_percent', 0)}%** ({health.get('successful_payments', 0)} successful / {health.get('total_payments', 0)} total)\n"
                f"- **Total Revenue Processed**: **₹{health.get('total_revenue_inr', 0):,.2f}**\n"
                f"- **Average Ticket Size**: **₹{health.get('avg_ticket_size_inr', 0):,.2f}**\n"
                f"- **Top Method**: `{health.get('top_performing_method', 'N/A').upper()}` | **Worst Method**: `{health.get('worst_performing_method', 'N/A').upper()}`\n"
            )
            alerts = health.get("alerts", [])
            if alerts:
                parts.append("#### 🚨 Active Alerts:")
                for a in alerts:
                    parts.append(f"- `[{a.get('severity', 'info').upper()}]` {a.get('message', '')}")

        if any(w in msg_lower for w in ["fail", "error", "drop", "why", "timeout", "decline"]):
            tools_used.append("analyze_payment_failures")
            fail_data = await self.tool_map["analyze_payment_failures"](time_window_days=7)
            parts.append(
                f"\n### 🔍 Payment Failure Analysis (7 Days)\n"
                f"- **Total Attempts**: {fail_data.get('total_payments', 0)}\n"
                f"- **Failed Transactions**: {fail_data.get('failed_count', 0)} ({fail_data.get('failure_rate_percent', 0)}% failure rate)\n"
                f"- **Trend**: **{fail_data.get('trend', 'stable').upper()}** (prior period: {fail_data.get('previous_period_rate', 0)}%)\n"
            )
            reasons = fail_data.get("failure_by_reason", [])
            if reasons:
                parts.append("**Top Failure Reasons:**")
                for r in reasons[:4]:
                    parts.append(f"- **{r.get('reason', 'unknown').replace('_', ' ').title()}**: {r.get('count', 0)} events")

            tools_used.append("recommend_retry_strategy")
            retries = await self.tool_map["recommend_retry_strategy"]()
            recs = retries.get("recommendations", [])
            if recs:
                parts.append("\n**💡 Recommended Mitigations:**")
                for rec in recs[:3]:
                    parts.append(f"- **{rec.get('strategy')}** ({rec.get('expected_impact')} impact): {rec.get('reasoning')}")

        if any(w in msg_lower for w in ["leak", "lost", "abandon", "recover", "money", "revenue"]):
            tools_used.append("detect_revenue_leaks")
            leaks = await self.tool_map["detect_revenue_leaks"](time_window_days=7)
            parts.append(
                f"\n### 💸 Revenue Leak Audit\n"
                f"- **Total Revenue Lost**: **₹{leaks.get('total_revenue_lost_inr', 0):,.2f}**\n"
                f"- **Estimated Recoverable**: **₹{leaks.get('recoverable_amount_inr', 0):,.2f}** (via smart retries & payment links)\n"
            )
            breakdown = leaks.get("leak_breakdown", {})
            parts.append(
                f"- **Failed Payments**: ₹{breakdown.get('failed', {}).get('amount_inr', 0):,.2f}\n"
                f"- **Abandoned Checkouts**: ₹{breakdown.get('abandoned', {}).get('amount_inr', 0):,.2f}\n"
                f"- **Refunds**: ₹{breakdown.get('refunded', {}).get('amount_inr', 0):,.2f}\n"
            )

        if any(w in msg_lower for w in ["risk", "chargeback", "fraud"]):
            tools_used.append("assess_chargeback_risk")
            risk = await self.tool_map["assess_chargeback_risk"]()
            parts.append(
                f"\n### 🛡️ Chargeback & Risk Score\n"
                f"- **Overall Risk Level**: **{risk.get('risk_level', 'low').upper()}** (Score: {risk.get('overall_risk_score', 0)}/100)\n"
            )
            mitigations = risk.get("mitigation_steps", [])
            if mitigations:
                parts.append("**Active Guardrails:**")
                for m in mitigations:
                    parts.append(f"- {m}")

        if not parts:
            # Default helpful prompt
            tools_used.append("generate_health_report")
            health = await self.tool_map["generate_health_report"]()
            parts.append(
                f"Hello! I'm your **PaySense AI Operations Agent**.\n\n"
                f"**Current Status:** System is monitoring **{health.get('total_payments', 0)} transactions** with a **{health.get('success_rate_percent', 0)}% success rate**.\n\n"
                f"You can ask me to:\n"
                f"- **'Run Health Scan'** — inspect overall metrics & alerts\n"
                f"- **'Why are payments failing?'** — diagnose failure reasons & optimal retry hours\n"
                f"- **'Show revenue leaks'** — calculate lost vs recoverable revenue\n"
                f"- **'Chargeback risk?'** — assess fraud exposure"
            )

        # Log decision to SQLite
        try:
            await self.tool_map["create_recovery_action"](
                action_type="agent_analysis",
                target_payment_id="batch"
            )
            tools_used.append("create_recovery_action")
        except Exception:
            pass

        return {
            "response": "\n".join(parts),
            "tools_used": list(dict.fromkeys(tools_used)),
            "reasoning": "Executed database analytics and generated actionable recommendations."
        }

    async def autonomous_scan(self) -> dict:
        """Run an autonomous health scan without user prompt."""
        return await self.chat("Run a proactive payment health scan, detect revenue leaks, and flag any critical issues.")

    def get_conversation_history(self) -> list:
        return self.conversation_history

    def clear_history(self):
        self.conversation_history = []
