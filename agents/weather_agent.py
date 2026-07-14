# 天气分析模块
# 使用聚合数据API获取天气信息。
# 获取实时天气和未来几天的预报。
# 根据天气信息生成建议。
# 获取当前季节的默认温度范围
import logging
from datetime import datetime
from typing import Any, Dict, Optional
import os
import aiohttp
import requests

from .base_agent import OpenAIBaseAgent
from states import PlanningStatus, TravelInfo  # 如果在前缀中添加..的话,就会出现(程序运行时会无法正确解析路径)

logger = logging.getLogger(__name__)


# 天气预报,使用聚合数据API。让AI去获取真实的天气数据信息
class WeatherAgent(OpenAIBaseAgent):

    # WeatherAgent: 使用真实的天气API（聚合数据）获取天气预报。
    # 使用环境变量 WEATHER_API_KEY，如果未设置则使用默认密钥。
    DEFAULT_API_KEY = "5d0d09a7a3c055066382819ab84ca724"   # 聚合数据个人账号的APIKEY密钥(先申请对应数据信息)
    BASE_URL = "http://apis.juhe.cn/simpleWeather/query"  # 天气API的URL,必须有,否则会报错(查看对应的官方接口文档即可)


    # 真实天气信息
    async def analyze(self, state: TravelInfo) -> Dict[str, Any]:
        logger.info("WeatherAgent: starting weather analysis for %s", state.destination)

        api_key = os.getenv("WEATHER_API_KEY", self.DEFAULT_API_KEY)
        try:
            forecast = await self._fetch_forecast(api_key, state.destination)
            weather_info = self._build_weather_info_from_api(forecast, state)
        except Exception:
            logger.exception("WeatherAgent: real API call failed, falling back to local logic")
            weather_info = self._fallback_weather(state)

        return {"weather_info": weather_info, "status": PlanningStatus.WEATHER.value}

    # 获取当前季节的默认温度范围
    async def _fetch_forecast(self, api_key: str, location: str) -> Dict[str, Any]:
        """调用聚合数据天气API获取天气信息"""
        params = {
            "key": api_key,
            "city": location,
        }

        loop = None
        try:
            import asyncio
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        response = await loop.run_in_executor(None, self._sync_request, params)

        # 判断响应结果
        if response.status_code == 200:
            result = response.json()
            if result.get('reason') == '查询成功!':
                return result.get('result', {})
            else:
                raise Exception(f"API返回错误: {result.get('reason', '查询失败')}")
        else:
            raise Exception(f"请求异常，状态码: {response.status_code}")

    # 同步HTTP请求
    def _sync_request(self, params: Dict[str, str]) -> requests.Response:
        """同步发送HTTP请求"""
        return requests.get(self.BASE_URL, params=params, timeout=10)

    def _build_weather_info_from_api(self, data: Dict[str, Any], state: TravelInfo) -> Dict[str, Any]:
        """从API响应中构建天气信息"""
        try:
            # 获取实时天气和未来预报
            realtime = data.get('realtime', {})
            future = data.get('future', [])

            # 提取当前天气信息
            temperature = realtime.get('temperature', '')
            humidity = realtime.get('humidity', '')
            current_condition = realtime.get('info', '')

            # 处理未来几天的天气预报
            temps = []
            conditions = []
            for day in future[:state.duration]:  # 只取旅行天数的预报
                temp_min = day.get('temperature', '').split('/')[0] if '/' in day.get('temperature', '') else day.get(
                    'temperature', '')
                temp_max = day.get('temperature', '').split('/')[1] if '/' in day.get('temperature', '') else day.get(
                    'temperature', '')

                if temp_min and temp_max:
                    try:
                        temps.append((float(temp_min), float(temp_max)))
                    except ValueError:
                        pass

                condition = day.get('weather', '')
                if condition:
                    conditions.append(condition)

            # 计算温度范围
            if temps:
                min_temp = min(t[0] for t in temps)
                max_temp = max(t[1] for t in temps)
                temperature_range = f"{min_temp:.0f}-{max_temp:.0f}°C"
            elif temperature:
                temperature_range = f"{temperature}°C"
            else:
                temperature_range = self._season_temperature(state.start_date)

            # 天气状况
            condition = ", ".join(dict.fromkeys(conditions)) if conditions else (current_condition or "晴到多云")

            # 生成建议
            advice_parts = []
            if any("雨" in c for c in conditions) or "雨" in current_condition:
                advice_parts.append("可能有降雨，建议携带雨具和防滑鞋。")
            if temps and any(t[1] >= 30 for t in temps):
                advice_parts.append("天气偏热，注意补水与防晒。")
            if temps and any(t[0] <= 5 for t in temps):
                advice_parts.append("夜间较冷，准备保暖衣物。")

            # 湿度建议
            if humidity:
                try:
                    hum_value = int(humidity.replace('%', ''))
                    if hum_value > 80:
                        advice_parts.append("湿度较大，注意防潮。")
                    elif hum_value < 30:
                        advice_parts.append("空气干燥，注意保湿。")
                except ValueError:
                    pass

            if not advice_parts:
                advice_parts.append("出行前关注当地实时天气，合理安排行程与着装。")
            travel_tips = "根据天气合理安排户外活动时间，备好雨具或防晒用品。"
            summary = f"{state.destination} 在 {state.start_date} 起 {state.duration} 天内，预计温度范围 {temperature_range}，主要天气：{condition}。"
            return {
                "temperature_range": temperature_range,  # 实时的温度
                "condition": condition,  # 天气状况
                "advice": "；".join(advice_parts),  # 外出建议
                "travel_tips": travel_tips,  # 旅行建议
                "summary": summary,  # 概述
                "realtime_temperature": temperature,  # 实时的温度
                "humidity": humidity,  # 湿度
            }
        except Exception:
            logger.exception("Failed to parse weather API response")
            return self._fallback_weather(state)


    # 假数据

    # # 获取季节的默认温度范围
    # def _season_temperature(self,start_date:str)->str:
    #     try:
    #         date_value = datetime.strptime(start_date, "%Y-%m-%d")
    #         month = date_value.month
    #         if month in (12, 1, 2):
    #             return "2-10°C"
    #         if month in (3, 4, 5):
    #             return "10-18°C"
    #         if month in (6, 7, 8):
    #             return "22-32°C"
    #         return "15-25°C"
    #     except Exception:
    #         return "18-28°C"
    #
    # # 获取默认天气信息
    # def _fallback_weather(self,state:TravelInfo)->Dict[str,Any]:
    #     month_temp = self._season_temperature(state.start_date)
    #     condition = "晴到多云"
    #     if "雨" in state.preferences.get("weather_notes","") or state.preferences.get("travel_style") == "雨天优先":
    #         condition = "阵雨/多云"
    #     return {
    #         "temperature_range": month_temp,
    #         "condition": condition,
    #         "advice": "建议携带轻便雨具和舒适鞋子，白天适合安排室内与室外交替活动。",
    #         "travel_tips": "根据天气选择轻便层叠穿搭，并在雨天安排室内活动。",
    #         "summary": f"预计{state.destination}旅行期间天气温和，{condition}，适合轻松旅行。",
    #     }


    # 先模拟假天气数据
    # def _season_temperature(self, start_date: str) -> str:
    #     try:
    #         date_value = datetime.strptime(start_date, "%Y-%m-%d")
    #         month = date_value.month
    #         if month in (12, 1, 2):
    #             return "2-10°C"
    #         if month in (3, 4, 5):
    #             return "10-18°C"
    #         if month in (6, 7, 8):
    #             return "22-32°C"
    #         return "15-25°C"
    #     except Exception:
    #         return "18-28°C"
    #
    # def _fallback_weather(self, state: TravelInfo) -> Dict[str, Any]:
    #     month_temp = self._season_temperature(state.start_date)
    #     condition = "晴到多云"
    #     if "雨" in state.preferences.get("weather_notes", "") or state.preferences.get("travel_style") == "雨天优先":
    #         condition = "阵雨/多云"
    #     return {
    #         "temperature_range": month_temp,
    #         "condition": condition,
    #         "advice": "建议携带轻便雨具和舒适鞋子，白天适合安排室内与室外交替活动。",
    #         "travel_tips": "根据天气选择轻便层叠穿搭，并在雨天安排室内活动。",
    #         "summary": f"预计{state.destination}旅行期间天气温和，{condition}，适合轻松旅行。",
    #     }
