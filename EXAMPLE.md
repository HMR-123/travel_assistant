# 使用示例

本文档提供了 `travel_assistant` 智能旅行规划系统的详细使用示例。

## 🚀 快速开始

### 环境配置

首先复制 `.env.example` 文件并填写 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai-hk.com/v1
OPENAI_MODEL=openai:gpt-3.5-turbo
WEATHER_API_KEY=your_weather_api_key_here
```

## 🖥️ 命令行模式

### 基本用法

```bash
python main.py -d 北京 -s 2025-06-01 -n 5
```

### 带偏好设置

```bash
python main.py \
  -d 成都 \
  -s 2025-07-15 \
  -n 4 \
  -p "interests:美食,历史文化, travel_style:轻松慢游, budget_level:mid-range"
```

### JSON 格式偏好

```bash
python main.py \
  -d 西安 \
  -s 2025-08-20 \
  -n 3 \
  -p '{"interests": ["历史文化", "美食"], "budget_level": "high"}'
```

## 🌐 Web 界面模式

启动 Web 服务：

```bash
streamlit run web.py
```

在浏览器中访问 `http://localhost:8501`，您将看到：

1. **左侧面板** - 输入旅行信息：
   - 目的地选择（支持预设城市和自定义输入）
   - 开始日期
   - 旅行天数
   - 旅行爱好选择

2. **右侧主区域** - 显示规划结果：
   - 天气信息标签页
   - 推荐景点标签页
   - 行程安排标签页
   - 预算估算标签页

## 📋 输入参数说明

### 必填参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `destination` | 旅行目的地 | 杭州、北京、成都 |
| `start_date` | 开始日期 | 2025-05-01 |
| `duration` | 旅行天数 | 3 |

### 可选偏好参数

| 偏好键 | 说明 | 可选值 |
|--------|------|--------|
| `interests` | 旅行兴趣 | 历史文化、美食、冒险、购物、放松、摄影、自然风光、艺术、体育、家庭友好 |
| `travel_style` | 旅行风格 | 轻松慢游、深度探索、打卡式、悠闲度假、户外探险 |
| `budget_level` | 预算水平 | low（经济型）、mid-range（中等）、high（高端） |

## 📊 输出示例

### 完整输出结构

```json
{
  "destination": "杭州",
  "start_date": "2025-05-01",
  "duration": 3,
  "preferences": {
    "interests": "历史文化",
    "budget_level": "mid-range"
  },
  "weather_info": {
    "temperature_range": "18-26°C",
    "condition": "晴到多云",
    "humidity": "65%",
    "advice": "天气适宜，建议携带轻便衣物和防晒用品。",
    "travel_tips": "根据天气合理安排户外活动时间，备好防晒用品。",
    "summary": "杭州在 2025-05-01 起 3 天内，预计温度范围 18-26°C，主要天气：晴到多云。"
  },
  "attractions": [
    {
      "活动": "西湖",
      "类型": "自然景观",
      "描述": "杭州最著名的景点，湖光山色美不胜收。",
      "最佳游玩时间": "上午/傍晚",
      "旅行时间": "约30分钟",
      "建议": "建议早起避开人流，傍晚观赏日落。"
    }
  ],
  "itinerary": {
    "summary": "为您规划了3天杭州之旅，涵盖主要景点和美食体验。",
    "transport_recommendation": "推荐使用地铁和步行，西湖周边景点较集中。",
    "dining_recommendation": "建议品尝西湖醋鱼、龙井虾仁等杭州特色美食。",
    "days": [
      {
        "date": "第1天",
        "morning": "西湖景区游览",
        "afternoon": "灵隐寺参观",
        "evening": "河坊街美食体验",
        "transport": "地铁 + 步行",
        "meals": "午餐：楼外楼，晚餐：河坊街小吃",
        "travel_tips": "西湖景区较大，建议租用自行车。"
      }
    ]
  },
  "budget_estimate": {
    "currency": "CNY",
    "total_budget": 2500,
    "daily_budget": 833,
    "categories": [
      {"name": "住宿", "estimated_cost": 333},
      {"name": "餐饮", "estimated_cost": 208},
      {"name": "交通", "estimated_cost": 125},
      {"name": "景点门票", "estimated_cost": 125},
      {"name": "其他杂费", "estimated_cost": 42}
    ],
    "summary": "根据旅行天数和偏好，估算了含住宿、餐饮、交通、门票与杂费的每日和总预算。"
  }
}
```

## 🔄 高级用法

### 在代码中调用

```python
import asyncio
from main import run_travel_planner

async def main():
    result = await run_travel_planner(
        destination="苏州",
        start_date="2025-05-15",
        duration=3,
        preferences={"interests": "园林,美食", "budget_level": "mid-range"}
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 批量规划

```python
import asyncio
from main import run_travel_planner

async def batch_planner():
    destinations = ["北京", "上海", "广州"]
    tasks = []
    
    for dest in destinations:
        task = run_travel_planner(
            destination=dest,
            start_date="2025-06-01",
            duration=3,
            preferences={"interests": "历史文化"}
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    for dest, result in zip(destinations, results):
        print(f"=== {dest} ===")
        print(f"预算: ¥{result['budget_estimate']['total_budget']}")
        print(f"天气: {result['weather_info']['summary']}")

if __name__ == "__main__":
    asyncio.run(batch_planner())
```

## 💡 提示与技巧

1. **天气 API 密钥**：可以在 [聚合数据](https://www.juhe.cn/) 申请免费的天气 API 密钥

2. **偏好设置**：合理设置 `interests` 和 `travel_style` 可以获得更精准的推荐

3. **预算估算**：`budget_level` 参数会影响住宿和餐饮的预算建议

4. **日期选择**：尽量选择非节假日日期，预算会更准确

5. **城市支持**：支持中国大部分城市，包括省级行政区（如湖南、云南等）

## 🐛 常见问题

### Q: 运行时提示 API 密钥错误
A: 请检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确配置

### Q: 天气信息获取失败
A: 检查 `WEATHER_API_KEY` 是否有效，或等待稍后重试

### Q: Web 界面无法启动
A: 确保已安装 streamlit：`pip install streamlit`

### Q: 输出结果为空或异常
A: 检查网络连接，或尝试更换 `OPENAI_API_BASE` 地址