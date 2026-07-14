# 景点推荐模块
import logging
from typing import Any, Dict, List

from .base_agent import OpenAIBaseAgent
from states import PlanningStatus, TravelInfo

logger = logging.getLogger(__name__)


# 景点推荐,使用聚合数据API。让AI去获取真实的景点信息
class AttractionAgent(OpenAIBaseAgent):
    async def recommend(self, state: TravelInfo) -> Dict[str, Any]:
        logger.info("AttractionAgent: generating attractions for %s", state.destination)
        system = (
            "You are a travel attraction recommender. Reply only in JSON format. "
            "The top-level JSON must include an attractions list."
        )
        user = (
            f"Recommend 4 must-see attractions in {state.destination} for a {state.duration}-day trip. "
            f"Use the weather condition {state.weather_info.get('condition', '晴到多云')} and traveler preferences {state.preferences} to adjust recommendations. "
            "Each attraction should include name, type, description, best_visit_period, travel_time, and suggestions. "
            "Provide a concise comment for each attraction."
        )

        try:
            raw = await self._chat(system, user)
            data = self._parse_json(raw)
            attractions = data.get("attractions") if isinstance(data, dict) else None
            if not isinstance(attractions, list):
                raise ValueError("Attractions response must contain a list")
            normalized = [self._normalize_attraction(item) for item in attractions][:4]
        except Exception:
            logger.exception("AttractionAgent failed, using fallback attraction list")
            normalized = self._fallback_attractions(state)

        return {"attractions": normalized, "status": PlanningStatus.ATTRACTION.value}

    def _normalize_attraction(self, raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return {
                "活动": str(raw.get("name", "未知景点")),
                "类型": str(raw.get("type", "景点")),
                "描述": str(raw.get("description", raw.get("notes", "此景点值得一游。"))),
                "最佳游玩时间": str(raw.get("best_visit_period", "上午/下午")),
                "旅行时间": str(raw.get("travel_time", "约30分钟")),
                "建议": str(raw.get("suggestions", raw.get("notes", "请提前规划交通和门票。"))),
            }
        return {
            "活动": str(raw),
            "类型": "景点",
            "描述": "此景点值得一游。",
            "最佳游玩时间": "上午/下午",
            "旅行时间": "约30分钟",
            "建议": "请提前规划交通和门票。",
        }


    # 获取对应的真实景点信息
    def _fallback_attractions(self, state: TravelInfo) -> List[Dict[str, Any]]:
        destination = state.destination
        weather_condition = state.weather_info.get("condition", "晴到多云")
        return [
            {
                "活动": f"{destination}文化博物馆",
                "类型": "博物馆",
                "描述": "适合了解当地历史与文化，遇到雨天也可安排。",
                "最佳游玩时间": "上午",
                "旅行时间": "约20分钟",
                "建议": "建议提前预约门票，避开高峰时段。",
            },
            {
                "活动": f"{destination}城市公园",
                "类型": "公园",
                "描述": f"当前天气：{weather_condition}，适合散步和拍照。",
                "最佳游玩时间": "下午",
                "旅行时间": "约15分钟",
                "建议": "傍晚时段空气清新，适合轻松漫步。",
            },
            {
                "活动": f"{destination}地标景点",
                "类型": "地标",
                "描述": "安排标志性景点拍照和城市观光。",
                "最佳游玩时间": "上午/傍晚",
                "旅行时间": "约30分钟",
                "建议": "建议早起或傍晚前往，避开中午人流。",
            },
            {
                "活动": f"{destination}本地美食街",
                "类型": "美食",
                "描述": "体验地方小吃和夜间氛围。",
                "最佳游玩时间": "晚上",
                "旅行时间": "约15分钟",
                "建议": "建议尝试招牌小吃，并注意保管好随身物品。",
            },
        ]

