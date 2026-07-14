# ✈️ travel_assistant

基于 LangGraph 多代理协作流程的智能旅行规划系统，通过四个专业 AI 代理协同工作，自动为用户生成完整的旅行计划，包括天气分析、景点推荐、行程规划和预算估算。

## 🎯 功能特性

- **🌤️ 天气分析** - 实时获取目的地天气信息，提供出行建议
- **🏛️ 景点推荐** - 根据目的地和偏好智能推荐必去景点
- **📅 行程规划** - 自动生成详细的每日行程安排
- **💰 预算估算** - 基于旅行天数和偏好进行合理预算预估
- **🌐 Web 界面** - 提供 Streamlit 交互式 Web 前端
- **🔄 命令行工具** - 支持通过命令行参数快速调用

## 🛠️ 技术栈

- **Python 3.10+** - 核心开发语言
- **LangGraph** - 多代理协作框架
- **LangChain** - AI 应用开发框架
- **Streamlit** - Web 界面框架
- **Pydantic** - 数据验证与状态管理
- **OpenAI GPT** - AI 模型支持（通过 LangChain 集成）

## 📦 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/HMR-123/travel_assistant.git
cd travel_assistant
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 文件并填写必要的 API 密钥：

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

## 🚀 使用方法

### 方式一：Web 界面

```bash
streamlit run web.py
```

然后在浏览器中打开显示的 URL（通常是 `http://localhost:8501`）。

### 方式二：命令行

```bash
python main.py --destination 杭州 --start-date 2025-05-01 --duration 3 --preferences "interests:历史文化, budget_level:mid-range"
```

### 命令行参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| `--destination` | `-d` | 旅行目的地（必填） |
| `--start-date` | `-s` | 开始日期，格式 YYYY-MM-DD（必填） |
| `--duration` | `-n` | 旅行天数（必填） |
| `--preferences` | `-p` | 用户偏好，JSON 或逗号分隔的 key:value 列表（可选） |

### 方式三：交互式模式

直接运行 `main.py`，程序会提示输入必要信息：

```bash
python main.py
```

## 🏗️ 项目结构

```
travel_assistant/
├── agents/                 # 代理模块
│   ├── __init__.py        # 代理导出
│   ├── base_agent.py      # 基础代理类
│   ├── weather_agent.py   # 天气分析代理
│   ├── attraction_agent.py # 景点推荐代理
│   ├── itinerary_agent.py # 行程规划代理
│   └── budget_agent.py    # 预算估算代理
├── md/                    # 文档资料
├── txt/                   # 示例文本
├── .env.example          # 环境变量示例
├── .gitignore            # Git 忽略配置
├── LICENSE               # MIT 许可证
├── README.md             # 项目说明文档
├── EXAMPLE.md            # 使用示例文档
├── main.py               # 命令行入口
├── web.py                # Web 界面入口
├── states.py             # 状态定义
└── requirements.txt      # 依赖列表
```

## 🧠 代理架构

系统包含四个专业 AI 代理，按顺序协同工作：

1. **WeatherAgent** - 天气分析
   - 调用真实天气 API 获取目的地预报
   - 根据天气条件生成出行建议

2. **AttractionAgent** - 景点推荐
   - 基于目的地和天气推荐景点
   - 返回景点类型、描述、最佳游玩时间等信息

3. **ItineraryAgent** - 行程规划
   - 根据景点和天气安排每日行程
   - 包含上午、下午、晚上活动安排

4. **BudgetAgent** - 预算估算
   - 估算住宿、餐饮、交通等费用
   - 提供总预算和日均预算

## 📝 输入输出示例

### 输入

```bash
python main.py -d 杭州 -s 2025-05-01 -n 3 -p "interests:历史文化, travel_style:轻松慢游"
```

### 输出

```json
{
  "destination": "杭州",
  "start_date": "2025-05-01",
  "duration": 3,
  "weather_info": {
    "temperature_range": "18-26°C",
    "condition": "晴到多云",
    "advice": "天气适宜，建议携带轻便衣物。",
    "summary": "杭州在 2025-05-01 起 3 天内，预计温度范围 18-26°C，主要天气：晴到多云。"
  },
  "attractions": [...],
  "itinerary": {...},
  "budget_estimate": {...}
}
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请在 GitHub 上提交 Issue。