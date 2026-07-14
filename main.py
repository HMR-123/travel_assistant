import argparse
import asyncio
import json
import logging
from typing import Dict
import os

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START

from agents.attraction_agent import AttractionAgent
from agents.budget_agent import BudgetAgent
from agents.itinerary_agent import ItineraryAgent
from agents.weather_agent import WeatherAgent
from states import TravelInfo

# 环境变量配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")    # openai密钥
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai-hk.com/v1")  # openai第三方服务器地址
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai:gpt-3.5-turbo")  # openai模型版本

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


# 解析用户输入的偏好
def parse_preferences(text: str) -> Dict[str, str]:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        preferences: Dict[str, str] = {}
        for item in text.split(","):
            if ":" in item:
                key, value = item.split(":", 1)
                preferences[key.strip()] = value.strip()
        return preferences


# 构建图
# 构建有向图工作流
# 节点管理
# 边连接
# 状态传递
def build_graph(api_key: str) -> StateGraph[TravelInfo, None, TravelInfo, TravelInfo]:
    weather_agent = WeatherAgent(api_key=api_key, model_name=OPENAI_MODEL)
    attraction_agent = AttractionAgent(api_key=api_key, model_name=OPENAI_MODEL)
    itinerary_agent = ItineraryAgent(api_key=api_key, model_name=OPENAI_MODEL)
    budget_agent = BudgetAgent(api_key=api_key, model_name=OPENAI_MODEL)

    graph = StateGraph(
        state_schema=TravelInfo,
        input_schema=TravelInfo,
        output_schema=TravelInfo,
    )

    graph.add_node("weather_analysis", weather_agent.analyze)
    graph.add_node("attraction_recommendation", attraction_agent.recommend)
    graph.add_node("itinerary_planning", itinerary_agent.plan)
    graph.add_node("budget_estimate", budget_agent.estimate)

    graph.add_edge(START, "weather_analysis")
    graph.add_edge("weather_analysis", "attraction_recommendation")
    graph.add_edge("attraction_recommendation", "itinerary_planning")
    graph.add_edge("itinerary_planning", "budget_estimate")

    graph.set_entry_point("weather_analysis")
    graph.set_finish_point("budget_estimate")

    return graph.compile()


# 旅行规划
async def run_travel_planner(destination: str, start_date: str, duration: int, preferences: dict) -> dict:
    logger.info("Initializing travel planner for %s", destination)
    travel_info = TravelInfo(
        destination=destination,
        start_date=start_date,
        duration=duration,
        preferences=preferences,
    )

    compiled_graph = build_graph(OPENAI_API_KEY)
    try:
        result = await compiled_graph.ainvoke(travel_info.model_dump())
        logger.info("Graph execution completed")
    except Exception:
        logger.exception("Graph execution failed")
        result = travel_info.model_dump()

    try:
        final_state = TravelInfo.model_validate(result)
        return json.loads(final_state.model_dump_json(ensure_ascii=False, indent=2))
    except Exception:
        logger.exception("Result validation failed, returning raw graph output")
        return result


def pretty_print(result: dict) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


def prompt_for_missing_args(args: argparse.Namespace) -> dict:
    destination = args.destination or input("请输入旅行目的地：").strip()
    start_date = args.start_date or input("请输入开始日期（YYYY-MM-DD）：").strip()
    duration = args.duration
    if duration is None:
        duration_text = input("请输入旅行天数：").strip()
        try:
            duration = int(duration_text)
        except ValueError:
            duration = 3
    preferences_text = args.preferences or input(
        "请输入偏好（例如 interests:历史文化, budget_level:mid-range, travel_style:轻松慢游）：\n"
    ).strip()
    preferences = parse_preferences(preferences_text)
    return {
        "destination": destination,
        "start_date": start_date,
        "duration": duration,
        "preferences": preferences,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LangGraph 智能旅行助手")
    parser.add_argument("--destination", "-d", help="旅行目的地")
    parser.add_argument("--start-date", "-s", help="开始日期，格式YYYY-MM-DD")
    parser.add_argument("--duration", "-n", type=int, help="旅行天数")
    parser.add_argument(
        "--preferences",
        "-p",
        help="用户偏好，JSON或逗号分隔的 key:value 列表",
    )
    return parser.parse_args()

# asyncio、aiohttp异步并发与HTTP请求
if __name__ == "__main__":
    args = parse_args()
    user_input = prompt_for_missing_args(args)

    result = asyncio.run(
        run_travel_planner(
            user_input["destination"],
            user_input["start_date"],
            user_input["duration"],
            user_input["preferences"],
        )
    )
    pretty_print(result)

