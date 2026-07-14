from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import asyncio
import json
from datetime import datetime
from main import run_travel_planner, parse_preferences

st.set_page_config(page_title="智能旅行助手", layout="wide", page_icon='✈️')
st.title("✈️ 智能旅行助手")
st.caption("基于LangGraph的AI旅行规划平台")

# 初始化session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def format_itinerary_field(value):
    if isinstance(value, dict):
        mapping = {
            'activity': '活动',
            'description': '描述',
            'travel_time': '持续时间',
            '旅行时间': '持续时间',
            'weather_advice': '天气建议',
            '交通': '交通',
            'transport': '交通',
            'meals': '餐饮',
            '餐饮': '餐饮',
            'suggestions': '建议',
            'notes': '建议',
            'activity_name': '活动',
        }
        lines = []
        for key in ['活动', 'activity', '描述', 'description', '持续时间', 'travel_time', '旅行时间', '天气建议', 'weather_advice', '交通', 'transport', '餐饮', 'meals', '建议', 'suggestions', 'notes']:
            if key in value and value[key] is not None:
                label = mapping.get(key, key)
                text = value[key]
                lines.append(f"**{label}**：{text}")
        return "\n\n".join(lines) if lines else json.dumps(value, ensure_ascii=False, indent=2)

    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return format_itinerary_field(parsed)
            if isinstance(parsed, list):
                return "\n".join(f"- {item}" for item in parsed)
            return str(parsed)
        except json.JSONDecodeError:
            return value

    return str(value)

# 左侧输入栏
with st.sidebar:
    st.header("📋 旅行信息输入")
    
    with st.form("travel_form"):
        # 城市选择
        # 支持下拉预设 + 自定义输入两种方式，自定义输入优先
        city_options = ["北京", "上海", "广州", "深圳", "杭州", "成都", "西安", "南京", "苏州", "厦门", "其他（自定义）"]
        # 不把自定义值写回到 selectbox 的 session_state（会导致值回退为首项），只在提交时决定 destination
        selected_city = st.selectbox("🏙️ 旅行目的地（预设选择）", city_options, index=0, key='selected_city')

        custom_city = st.text_input("🏙️ 自定义城市/省份（可选，优先使用）", value=st.session_state.get('custom_city', ''), placeholder="输入自定义城市或省份，如湖南、江西等", key='custom_city')

        # 在最终使用时决定 destination（自定义优先），避免把自定义写入 selectbox
        if custom_city and custom_city.strip():
            destination = custom_city.strip()
        else:
            # 如果用户选择了“其他（自定义）”但没填写自定义，则视为未填写目的地
            destination = '' if selected_city == "其他（自定义）" else selected_city
        
        # 时间选择
        start_date = st.date_input("📅 开始日期（预设选择）", value=datetime.today())
        custom_date = st.text_input("📅 自定义日期（可选，格式：YYYY-MM-DD，优先使用）", placeholder="如不填则使用上方选择")
        start_date_str = custom_date if custom_date else start_date.strftime("%Y-%m-%d")
        
        duration = st.number_input("⏱️ 旅行天数", min_value=1, value=3)
        
        # 旅行爱好选择
        hobby_options = ["历史文化", "美食", "冒险", "购物", "放松", "摄影", "自然风光", "艺术", "体育", "家庭友好"]
        selected_hobbies = st.multiselect("🎯 旅行爱好（预设选择）", hobby_options, default=[])
        custom_hobby = st.text_input("🎯 自定义爱好（可选，用逗号分隔）", placeholder="例如：温泉, 滑雪")
        all_hobbies = selected_hobbies.copy()
        if custom_hobby:
            custom_hobbies_list = [h.strip() for h in custom_hobby.split(',') if h.strip()]
            all_hobbies.extend(custom_hobbies_list)
        preferences_text = ", ".join([f"interests:{hobby}" for hobby in all_hobbies])
        
        submitted = st.form_submit_button("🚀 开始规划", use_container_width=True)

    # 聊天记录会话
    st.header("💬 聊天记录")
    if st.session_state.chat_history:
        for i, chat in enumerate(st.session_state.chat_history):
            with st.expander(f"对话 {i+1}: {chat['destination']} - {chat['date']}"):
                st.write(f"**目的地:** {chat['destination']}")
                st.write(f"**日期:** {chat['date']}")
                st.write(f"**天数:** {chat['duration']} 天")
                st.write(f"**爱好:** {', '.join(chat['hobbies'])}")
                st.write(f"**结果摘要:** {chat['summary']}")
                if st.button(f"🗑️ 删除此记录", key=f"delete_{i}"):
                    st.session_state.chat_history.pop(i)
                    st.rerun()
    else:
        st.info("暂无聊天记录")
    
    if st.button("🗑️ 删除所有聊天记录"):
        st.session_state.chat_history = []
        st.rerun()

# 主内容区域
if submitted:
    # 表单校验：如果用户在下拉中选择了“其他（自定义）”但没有填写自定义城市，阻止提交并提示
    if selected_city == "其他（自定义）" and (not custom_city or not custom_city.strip()):
        st.error("❌ 你选择了‘其他（自定义）’，但未在“自定义城市/省份”中填写具体城市或省份，请填写例如：湖南、江西。")
    elif not destination or not start_date_str:
        st.error("❌ 请填写目的地和开始日期")
    else:
        preferences = parse_preferences(preferences_text)
        
        with st.spinner("🔄 正在为您规划旅行..."):
            try:
                result = asyncio.run(run_travel_planner(destination, start_date_str, int(duration), preferences))
                st.success("✅ 规划完成！")
                
                # 添加到聊天记录
                summary = f"规划了{duration}天的{destination}旅行"
                if 'weather_info' in result and 'summary' in result['weather_info']:
                    summary += f"，天气：{result['weather_info']['summary']}"
                if 'budget_estimate' in result and 'total_budget' in result['budget_estimate']:
                    summary += f"，预算约¥{result['budget_estimate']['total_budget']}"
                
                chat_entry = {
                    'destination': destination,
                    'date': start_date_str,
                    'duration': duration,
                    'hobbies': all_hobbies,
                    'summary': summary
                }
                st.session_state.chat_history.append(chat_entry)
                
                # 创建标签页显示不同内容
                tab1, tab2, tab3, tab4 = st.tabs(["天气信息", "推荐景点", "行程安排", "预算估算"])
                
                # 标签页1：天气信息
                with tab1:
                    if 'weather_info' in result:
                        weather = result['weather_info']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("🌡️ 温度范围", weather.get('temperature_range', 'N/A'))
                        with col2:
                            st.metric("☀️ 天气状况", weather.get('condition', 'N/A'))
                        with col3:
                            st.metric("💨 湿度", weather.get('humidity', 'N/A') if weather.get('humidity') else '获取中')
                        
                        # 显示摘要
                        if 'summary' in weather:
                            st.info(f"📋 {weather['summary']}")
                        
                        # 显示建议
                        if 'advice' in weather:
                            st.success(f"✅ 出行建议：{weather['advice']}")
                        
                        # 显示旅行提示
                        if 'travel_tips' in weather:
                            st.warning(f"💡 旅行提示：{weather['travel_tips']}")
                    else:
                        st.info("暂无天气数据")
                
                # 标签页2：推荐景点
                with tab2:
                    if 'attractions' in result and result['attractions']:
                        st.write(f"**推荐景点数量：{len(result['attractions'])}**")
                        for i, attraction in enumerate(result['attractions'], 1):
                            with st.container(border=True):
                                st.write(f"### {i}. {attraction.get('活动', '景点' + str(i))} ({attraction.get('类型', '景点')})")
                                if '描述' in attraction:
                                    st.write(f"📖 {attraction['描述']}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if '最佳游玩时间' in attraction:
                                        st.caption(f"⏰ 最佳游玩时间：{attraction['最佳游玩时间']}")
                                with col2:
                                    if '旅行时间' in attraction:
                                        st.caption(f"🚗 交通时间：{attraction['旅行时间']}")
                                
                                if '建议' in attraction:
                                    st.info(f"💡 {attraction['建议']}")
                    else:
                        st.info("暂无景点推荐")
                
                # 标签页3：行程安排
                with tab3:
                    if 'itinerary' in result:
                        itinerary = result['itinerary']
                        if isinstance(itinerary, dict):
                            # 显示概览
                            if 'summary' in itinerary:
                                st.info(f"📋 {itinerary['summary']}")
                            
                            # 显示每日行程
                            if 'days' in itinerary and isinstance(itinerary['days'], list):
                                for index, day_plan in enumerate(itinerary['days'], start=1):
                                    day_date = day_plan.get('date', f'第{index}天')
                                    with st.expander(f"📅 {day_date}"):
                                        if day_plan.get('summary'):
                                            st.success(format_itinerary_field(day_plan.get('summary')))

                                        col1, col2 = st.columns([3, 2], gap='large')
                                        with col1:
                                            st.markdown(
                                                f"**上午 ☀️:**\n{format_itinerary_field(day_plan.get('morning', '自由活动'))}\n\n"
                                                f"**下午 🌤️:**\n{format_itinerary_field(day_plan.get('afternoon', '自由活动'))}\n\n"
                                                f"**晚上 🌙:**\n{format_itinerary_field(day_plan.get('evening', '推荐品尝当地美食'))}"
                                            )
                                        with col2:
                                            st.markdown(
                                                f"**餐饮 🍽️:**\n{format_itinerary_field(day_plan.get('meals', '本地餐饮'))}\n\n"
                                                f"**交通 🚗:**\n{format_itinerary_field(day_plan.get('transport', '地铁/出租车'))}"
                                            )
                                            if day_plan.get('travel_tips'):
                                                st.info(f"💡: {format_itinerary_field(day_plan.get('travel_tips'))}")
                                            if day_plan.get('note'):
                                                st.info(format_itinerary_field(day_plan.get('note')))
                                        st.divider()
                            else:
                                st.info("暂无详细每日行程，请稍后调整或重新生成。")
                            
                            # 显示通用建议
                            col1, col2 = st.columns(2)
                            with col1:
                                if 'transport_recommendation' in itinerary:
                                    st.info(f"🚗 **交通建议**\n{format_itinerary_field(itinerary['transport_recommendation'])}")
                            with col2:
                                if 'dining_recommendation' in itinerary:
                                    st.info(f"🍜 **餐饮建议**\n{format_itinerary_field(itinerary['dining_recommendation'])}")
                        else:
                            st.write(format_itinerary_field(itinerary))
                    else:
                        st.info("暂无行程安排")
                
                # 标签页4：预算估算
                with tab4:
                    if 'budget_estimate' in result:
                        budget = result['budget_estimate']
                        if isinstance(budget, dict):
                            # 显示总预算和日均预算
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                total = budget.get('total_budget', 0)
                                st.metric("💰 总预算", f"¥ {total}" if total else "N/A")
                            with col2:
                                daily = budget.get('daily_budget', 0)
                                st.metric("📅 日均预算", f"¥ {daily}" if daily else "N/A")
                            with col3:
                                currency = budget.get('currency', 'CNY')
                                st.metric("💱 货币", currency)
                            
                            st.divider()
                            
                            # 显示预算明细
                            if 'categories' in budget and isinstance(budget['categories'], list):
                                st.subheader("预算分类明细")
                                categories = budget['categories']
                                
                                if categories:
                                    # 创建表格数据
                                    table_data = []
                                    total_cost = 0
                                    # 预算分类中英文映射,不添加映射默认为英文
                                    budget_category_mapping = {
                                        'lodging': '住宿',
                                        'meals': '餐饮',
                                        'transportation': '交通',
                                        'attractions': '景点门票',
                                        'miscellaneous': '其他杂费',
                                        'hotel': '住宿',
                                        'food': '餐饮',
                                        'transport': '交通',
                                        'attraction': '景点门票',
                                        'other': '其他杂费',
                                        'accommodation': '住宿',
                                        'shopping': '购物',
                                        'shopping_and_misc': '购物及其他',
                                    }
                                    for cat in categories:
                                        cat_name = cat.get('name', '其他')
                                        cat_name = budget_category_mapping.get(cat_name.lower(), cat_name)
                                        cat_cost = cat.get('estimated_cost', 0)
                                        table_data.append({
                                            "分类": cat_name,
                                            "金额": f"¥ {cat_cost}" if cat_cost else "N/A"
                                        })
                                        if isinstance(cat_cost, (int, float)):
                                            total_cost += cat_cost
                                    
                                    # 显示为表格
                                    for item in table_data:
                                        col1, col2 = st.columns([3, 1], gap="large")
                                        with col1:
                                            col1.write(item["分类"])
                                        with col2:
                                            col2.write(item["金额"])
                            
                            # 显示摘要
                            if 'summary' in budget:
                                st.info(f"📋 {budget['summary']}")
                        else:
                            st.write(budget)
                    else:
                        st.info("暂无预算估算")
                
                # 底部：导出选项
                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📥 下载完整规划报告（JSON格式）"):
                        json_str = json.dumps(result, ensure_ascii=False, indent=2)
                        st.download_button(
                            label="点击下载",
                            data=json_str,
                            file_name=f"{destination}_travel_plan.json",
                            mime="application/json"
                        )
                with col2:
                    if st.button("🔄 开始新规划"):
                        st.rerun()
                    
            except Exception as e:
                st.error(f"❌ 规划失败：{str(e)}")
                st.info("请检查输入的信息是否正确，或稍后重试")