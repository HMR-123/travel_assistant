# 状态定义模块
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class PlanningStatus(Enum):
    INIT = "init"  # 初始化
    WEATHER = "weather"  # 天气
    ATTRACTION = "attraction"  # 景点
    ITINERARY = "itinerary"  # 行程
    BUDGET = "budget"  # 预算
    DONE = "done"  # 完成

# 数据验证与状态定义
class TravelInfo(BaseModel):
    destination: str  # 旅行的目的地, 例如"杭州"
    start_date: str  # 开始日期, 例如"2025-04-22"
    duration: int  # 行程天数, 例如3天
    preferences: Dict[str, Any] = Field(default_factory=dict)  # 用户偏好, 如兴趣, 预算等
    weather_info: Dict[str, Any] = Field(default_factory=dict)  # 天气分析结果, 由天气Agent填充
    attractions: List[Dict[str, Any]] = Field(default_factory=list)  # 推荐的景点列表, 由景点Agent填充
    itinerary: Dict[str, Any] = Field(default_factory=dict)  # 最终生成的行程计划, 由行程Agent填充
    budget_estimate: Dict[str, Any] = Field(default_factory=dict)  # 预算预估, 由预算Agent填充
    status: PlanningStatus = PlanningStatus.INIT  # 当前规划阶段



