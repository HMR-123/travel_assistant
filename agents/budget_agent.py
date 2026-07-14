# 新增：预算代理模块
import logging
from typing import Any, Dict

from .base_agent import OpenAIBaseAgent
from states import PlanningStatus, TravelInfo

logger = logging.getLogger(__name__)



# 预算代理
class BudgetAgent(OpenAIBaseAgent):
    async def estimate(self, state: TravelInfo) -> Dict[str, Any]:
        logger.info("BudgetAgent: generating budget estimates for %s", state.destination)
        system = (
            "You are a travel budget planner. Reply in strict JSON with keys: currency, total_budget, daily_budget, categories, summary. "
            "Each category should include name and estimated_cost."
        )
        user = (
            f"Estimate a realistic travel budget for a {state.duration}-day trip to {state.destination}. "
            f"The traveler prefers {state.preferences.get('travel_style', 'moderate')} travel, "
            f"interest in {state.preferences.get('interests', 'local culture and landmarks')}, "
            f"and a budget level of {state.preferences.get('budget_level', 'mid-range')}. "
            "Please include lodging, meals, transportation, attractions, and miscellaneous costs. "
            "Return the result as JSON."
        )

        try:
            raw = await self._chat(system, user)
            data = self._parse_json(raw)
            budget = self._normalize_budget(data)
        except Exception as exc:
            logger.exception("BudgetAgent failed")
            budget = self._fallback_budget(state)

        return {"budget_estimate": budget, "status": PlanningStatus.BUDGET.value}

    # 预算预估
    def _normalize_budget(self, data: Any) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError("Budget response must be a JSON object")

        categories = data.get("categories")
        if not isinstance(categories, list):
            categories = []

        return {
            "currency": str(data.get("currency", "CNY")),
            "total_budget": data.get("total_budget", 0),
            "daily_budget": data.get("daily_budget", 0),
            "categories": categories,
            "summary": str(data.get("summary", "Please budget for transportation, meals, lodging, and local fees.")),
        }

    # 获取预算信息
    def _fallback_budget(self, state: TravelInfo) -> Dict[str, Any]:
        base = 1200 if state.preferences.get("budget_level") == "high" else 700
        daily = base if state.preferences.get("budget_level") == "mid-range" else base * 0.75
        total = daily * max(1, state.duration)
        return {
            "currency": "CNY",
            "total_budget": int(total),
            "daily_budget": int(daily),
            "categories": [
                {"name": "Lodging", "estimated_cost": int(daily * 0.4)},
                {"name": "Meals", "estimated_cost": int(daily * 0.25)},
                {"name": "Local transportation", "estimated_cost": int(daily * 0.15)},
                {"name": "Attractions & tickets", "estimated_cost": int(daily * 0.15)},
                {"name": "Miscellaneous", "estimated_cost": int(daily * 0.05)},
            ],
            "summary": (
                "根据旅行天数和偏好，估算了含住宿、餐饮、交通、门票与杂费的每日和总预算。"
            ),
        }
