# 行程规划模块
import logging
import json
from typing import Any, Dict, List

from .base_agent import OpenAIBaseAgent
from states import PlanningStatus, TravelInfo

logger = logging.getLogger(__name__)


# 行程规划
class ItineraryAgent(OpenAIBaseAgent):
    async def plan(self, state: TravelInfo) -> Dict[str, Any]:
        logger.info("ItineraryAgent: crafting itinerary for %s", state.destination)
        system = (
            "You are a travel itinerary planner. Reply only in JSON with a top-level itinerary object. "
            "For morning/afternoon/evening/meals/transport/travel_tips, return natural Chinese text, not JSON objects or JSON-formatted strings."
        )
        user = (
            f"Design a {state.duration}-day itinerary for {state.destination} based on these attractions: {state.attractions}. "
            f"Use weather information {state.weather_info} and traveler preferences {state.preferences}. "
            "Each day should include date, morning, afternoon, evening, transport, meal suggestions, and travel tips. "
            "Also provide general transport and dining recommendations for the trip."
        )

        try:
            raw = await self._chat(system, user)  # 获取AI生成的行程信息
            data = self._parse_json(raw)# 解析json数据
            itinerary = data.get("itinerary") if isinstance(data, dict) else None# 获取行程信息
            if not isinstance(itinerary, dict):
                raise ValueError("Itinerary response must contain an itinerary object")
            itinerary = self._normalize_itinerary(itinerary)
        except Exception:
            logger.exception("ItineraryAgent failed, using fallback itinerary")
            itinerary = self._fallback_itinerary(state)
        # 返回结果
        return {"itinerary": itinerary, "status": PlanningStatus.ITINERARY.value}

    # 规划阶段
    def _normalize_itinerary(self, raw: Any) -> Dict[str, Any]:
        if not isinstance(raw, dict):# 判断是否为字典
            raise ValueError("Itinerary must be a dict")

        days = raw.get("days") or raw.get("schedule") or []# 获取行程信息
        if not isinstance(days, list):
            days = []

        return {
            "summary": str(raw.get("summary", "请参考以下每日行程安排。")),
            "transport_recommendation": str(raw.get("transport_recommendation", raw.get("transport_advice", "推荐使用地铁、出租车或步行，避免高峰拥堵。"))),
            "dining_recommendation": str(raw.get("dining_recommendation", raw.get("meal_advice", "建议选择当地特色餐厅，并提前预订热门餐厅。"))),
            "days": [self._normalize_day(day, index + 1) for index, day in enumerate(days)],
        }

    def _normalize_day(self, raw: Any, index: int) -> Dict[str, Any]:
        if not isinstance(raw, dict):# 判断是否为字典
            return {
                "date": f"Day {index}",
                "morning": "自由活动",
                "afternoon": "自由活动",
                "evening": "推荐品尝当地美食",
                "transport": "地铁/出租车",
                "meals": "本地餐饮",
                "travel_tips": "根据当天天气适度调整。",
            }

        def format_json_object(parsed: Any) -> str:
            if not isinstance(parsed, dict):
                return str(parsed)

            activity = parsed.get('activity') or parsed.get('活动')
            description = parsed.get('description') or parsed.get('描述')
            travel_time = parsed.get('travel_time') or parsed.get('持续时间') or parsed.get('旅行时间')
            weather_advice = parsed.get('weather_advice') or parsed.get('天气建议')
            transport = parsed.get('transport') or parsed.get('交通')
            meals = parsed.get('meals') or parsed.get('餐饮')
            suggestions = parsed.get('suggestions') or parsed.get('建议') or parsed.get('notes')

            parts = []
            if activity:# 判断是否为活动
                parts.append(f"活动：{activity}")
            if description:
                parts.append(f"描述：{description}")
            if travel_time:
                parts.append(f"持续时间：{travel_time}")
            if weather_advice:
                parts.append(f"天气建议：{weather_advice}")
            if transport:
                parts.append(f"交通：{transport}")
            if meals:
                parts.append(f"餐饮：{meals}")
            if suggestions:
                parts.append(f"建议：{suggestions}")

            return '； '.join(parts) if parts else str(parsed)

        def parse_field(value: Any) -> str:# 解析字段
            if isinstance(value, dict):
                return format_json_object(value)
            if isinstance(value, list):
                return '； '.join(str(item) for item in value)
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict):
                        return format_json_object(parsed)
                    if isinstance(parsed, list):
                        return '； '.join(str(item) for item in parsed)
                    return str(parsed)
                except json.JSONDecodeError:
                    return str(value)
            return str(value)

        return {
            "date": str(raw.get("date", f"Day {index}")),
            "morning": parse_field(raw.get("morning", "自由活动")),
            "afternoon": parse_field(raw.get("afternoon", "自由活动")),
            "evening": parse_field(raw.get("evening", "推荐品尝当地美食")),
            "transport": parse_field(raw.get("transport", "地铁/出租车")),
            "meals": parse_field(raw.get("meals", "本地餐饮")),
            "travel_tips": parse_field(raw.get("travel_tips", raw.get("notes", "视天气情况灵活调整。"))),
        }

    def _fallback_itinerary(self, state: TravelInfo) -> Dict[str, Any]:# 获取默认行程信息
        days: List[Dict[str, Any]] = []
        attractions = state.attractions or []# 获取景点信息
        for index in range(state.duration):# 遍历每一天
            attraction = attractions[index] if index < len(attractions) else {"name": "当地自由活动"}
            days.append(# 生成每一天的行程信息
                {
                    "date": f"第{index + 1}天",
                    "morning": f"前往{attraction.get('name')}参观",
                    "afternoon": "体验本地美食与文化街区",
                    "evening": "推荐夜市或轻松休憩",
                    "transport": "地铁或出租车",
                    "meals": "午餐和晚餐安排本地餐厅",
                    "travel_tips": "若遇雨天请备好雨具，合理调整室内外活动。",
                }
            )

        return {
            "summary": "这是基于景点推荐的默认日程安排，可根据实际情况适度调整。",
            "transport_recommendation": "建议以地铁和出租车为主，遇到热门时段可提前安排。",
            "dining_recommendation": "优先体验当地特色餐厅，午餐和晚餐建议提前预订。",
            "days": days,
        }

