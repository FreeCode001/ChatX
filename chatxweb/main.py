# main.py
# encoding=utf-8
import pandas as pd
import streamlit as st
import re
import logging
import os
from auth import check_authentication, get_user_roles

# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', 'logs', 'chatx.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ChatX-main')


# 登录成功后显示主页面内容
st.set_page_config(
    page_title="ChatX",
    page_icon="👋",
    layout="wide",
)
# 隐藏默认的Streamlit菜单和页脚
hide_default_styles = """
    <style>
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}  /* 隐藏右上角默认菜单 */
    #footer {visibility: hidden;}
    </style>
    """
#header {visibility: hidden;}     /* 隐藏顶部默认空白栏 */
#footer {visibility: hidden;}     /* 隐藏底部默认页脚 */
# 注入样式
st.markdown(hide_default_styles, unsafe_allow_html=True)

# 核心：全局登录验证（未登录则无法访问）
authenticator, name, username, config = check_authentication()

# 记录访问主页日志，确保每个会话只记录一次
if f'homepage_visited_{username}' not in st.session_state:
    logger.info(f'用户：{username} | 访问ChatX主页')
    st.session_state[f'homepage_visited_{username}'] = True

st.markdown("# 欢迎访问ChatX AI应用助手! 👋")
st.divider()

# 登出按钮（侧边栏）
with st.sidebar:
    st.write(f'### 欢迎你， {username} ！')
    st.write('请点击导航栏菜单访问子页面')
    st.markdown("### 关于 ChatX")
    st.markdown("基于Streamlit的AI聊天助手")
    st.divider()
    # 登出按钮（侧边栏）
    authenticator.logout('退出登录', 'sidebar', use_container_width=True, callback=lambda _: logger.info(f'用户：{username} | 退出登录'))


st.markdown(
    """
    ChatX是一个基于Streamlit的AI聊天助手，用于与AI模型应用进行交互。它提供了一个简洁而强大的界面，用于与AI模型应用进行交互。
    
    ## 功能介绍
    - 用户登录注册：用户可以注册账号并登录系统，实现个人数据隔离和安全。
    - 单模型对话：用户可以与单个模型进行对话，查看模型的回复。
    - 多模型对比：用户可以对比不同模型的对话结果，评估模型性能和适用场景。
    - 智能体对话：目前支持问答智能体、起网名智能体、深度研究智能体。
    - 模型注册：用户可以注册自己的模型服务以便在线使用。
    - 内置模型：ChatX内置了一些免费的模型，用户可以免费使用这些模型进行对话。

    **支持的模型有：**
    - QWen3
    - DeepSeek-R1
    - GLM-4.7-flash
    ....

    **👈 请从侧边栏选择一个模块，使用ChatX的功能！**

    如有问题，欢迎联系。电子邮箱：1429327078@qq.com

    模型服务由SiliconFlow提供。可点击[链接](https://cloud.siliconflow.cn/i/xN0byfSr)注册账号使用SiliconFlow的服务。

"""
)

roles = get_user_roles(username)
if 'admin' in roles:
    st.divider()
    with st.expander("# 管理员查看用户数据"):
        tab1, tab2 = st.tabs(["**功能统计**", "**用户统计**"])    
        
        # 解析日志文件
        # 读取日志文件
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'chatx.log')
        
        # 定义正则表达式模式
        login_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \|登录成功: 用户 (\w+) \((.*?)\) 已成功登录系统')
        logout_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \| 退出登录')
        homepage_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \| 访问ChatX主页')
        chat2model_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ChatX-Chat2Model - INFO - 用户：(\w+) \| 访问Chat2Model:.*?')
        multimodel_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ChatX-MultiModelChat - INFO - 用户：(\w+) \| 访问MultiModelChat:.*?')
        chat2agent_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ChatX-Chat2Agent - INFO - 用户：(\w+) \| 访问Chat2Agent:.*?')
        message_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \|\s*用户.*?输入问题:.*?')
        model_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \|.*?模型 ([\w-]+) 处理用户请求')
        agent_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \|.*?调用 (.*?) 处理用户请求')
        
        # 初始化数据结构
        user_stats = {}
        function_stats = {
            'Chat2Model': {'visits': 0, 'messages': 0, 'models': {}},
            'MultiModelChat': {'visits': 0, 'messages': 0, 'models': {}},
            'Chat2Agent': {'visits': 0, 'messages': 0, 'agents': {}}
        }
        daily_user_activities = {}  # 用于统计每天每个用户的活跃次数
        
        # 解析日志
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # 处理登录记录
                login_match = login_pattern.search(line)
                if login_match:
                    timestamp, username, username, full_name = login_match.groups()
                    if username not in user_stats:
                        user_stats[username] = {
                            'full_name': full_name,
                            'first_login': timestamp,
                            'last_login': timestamp,
                            'login_count': 0,
                            'logout_count': 0,
                            'homepage_visits': 0,
                            'chat2model_visits': 0,
                            'multimodel_visits': 0,
                            'chat2agent_visits': 0,
                            'messages': 0,
                            'models_used': set()
                        }
                    user_stats[username]['login_count'] += 1
                    user_stats[username]['last_login'] = timestamp
                    # 统计活跃次数
                    date = timestamp.split(' ')[0]
                    if date not in daily_user_activities:
                        daily_user_activities[date] = {}
                    if username not in daily_user_activities[date]:
                        daily_user_activities[date][username] = 0
                    daily_user_activities[date][username] += 1
                
                # 处理登出记录
                logout_match = logout_pattern.search(line)
                if logout_match:
                    timestamp, username = logout_match.groups()
                    if username in user_stats:
                        user_stats[username]['logout_count'] += 1
                    # 统计活跃次数
                    date = timestamp.split(' ')[0]
                    if date not in daily_user_activities:
                        daily_user_activities[date] = {}
                    if username not in daily_user_activities[date]:
                        daily_user_activities[date][username] = 0
                    daily_user_activities[date][username] += 1
                
                # 处理主页访问
                homepage_match = homepage_pattern.search(line)
                if homepage_match:
                    timestamp, username = homepage_match.groups()
                    if username in user_stats:
                        user_stats[username]['homepage_visits'] += 1
                    # 统计活跃次数
                    date = timestamp.split(' ')[0]
                    if date not in daily_user_activities:
                        daily_user_activities[date] = {}
                    if username not in daily_user_activities[date]:
                        daily_user_activities[date][username] = 0
                    daily_user_activities[date][username] += 1
                
                # 处理Chat2Model访问
                chat2model_match = chat2model_pattern.search(line)
                if chat2model_match:
                    timestamp, username = chat2model_match.groups()
                    if username in user_stats:
                        user_stats[username]['chat2model_visits'] += 1
                    function_stats['Chat2Model']['visits'] += 1
                    # 统计活跃次数
                    date = timestamp.split(' ')[0]
                    if date not in daily_user_activities:
                        daily_user_activities[date] = {}
                    if username not in daily_user_activities[date]:
                        daily_user_activities[date][username] = 0
                    daily_user_activities[date][username] += 1
                
                # 处理MultiModelChat访问
                multimodel_match = multimodel_pattern.search(line)
                if multimodel_match:
                    timestamp, username = multimodel_match.groups()
                    if username in user_stats:
                        user_stats[username]['multimodel_visits'] += 1
                    function_stats['MultiModelChat']['visits'] += 1
                    # 统计活跃次数
                    date = timestamp.split(' ')[0]
                    if date not in daily_user_activities:
                        daily_user_activities[date] = {}
                    if username not in daily_user_activities[date]:
                        daily_user_activities[date][username] = 0
                    daily_user_activities[date][username] += 1
                
                # 处理Chat2Agent访问
                chat2agent_match = chat2agent_pattern.search(line)
                if chat2agent_match:
                    timestamp, username = chat2agent_match.groups()
                    if username in user_stats:
                        user_stats[username]['chat2agent_visits'] += 1
                    function_stats['Chat2Agent']['visits'] += 1
                    # 统计活跃次数
                    date = timestamp.split(' ')[0]
                    if date not in daily_user_activities:
                        daily_user_activities[date] = {}
                    if username not in daily_user_activities[date]:
                        daily_user_activities[date][username] = 0
                    daily_user_activities[date][username] += 1
                
                # 处理消息记录
                message_match = message_pattern.search(line)
                if message_match:
                    timestamp, username = message_match.groups()
                    if username in user_stats:
                        user_stats[username]['messages'] += 1
                        # 根据日志源判断功能类型
                        if 'Chat2Model' in line:
                            function_stats['Chat2Model']['messages'] += 1
                        elif 'MultiModelChat' in line:
                            function_stats['MultiModelChat']['messages'] += 1
                        elif 'Chat2Agent' in line:
                            function_stats['Chat2Agent']['messages'] += 1
                    # 统计活跃次数
                    date = timestamp.split(' ')[0]
                    if date not in daily_user_activities:
                        daily_user_activities[date] = {}
                    if username not in daily_user_activities[date]:
                        daily_user_activities[date][username] = 0
                    daily_user_activities[date][username] += 1
                
                # 处理模型使用
                model_match = model_pattern.search(line)
                if model_match:
                    timestamp, username, model_name = model_match.groups()
                    if username in user_stats:
                        user_stats[username]['models_used'].add(model_name)
                    # 根据日志源判断功能类型
                    if 'Chat2Model' in line:
                        function_stats['Chat2Model']['models'][model_name] = function_stats['Chat2Model']['models'].get(model_name, 0) + 1
                    elif 'MultiModelChat' in line:
                        function_stats['MultiModelChat']['models'][model_name] = function_stats['MultiModelChat']['models'].get(model_name, 0) + 1
                    # 统计活跃次数
                    date = timestamp.split(' ')[0]
                    if date not in daily_user_activities:
                        daily_user_activities[date] = {}
                    if username not in daily_user_activities[date]:
                        daily_user_activities[date][username] = 0
                    daily_user_activities[date][username] += 1
                
                # 处理Agent使用
                agent_match = agent_pattern.search(line)
                if agent_match and 'Chat2Agent' in line:
                    timestamp, username, agent_name = agent_match.groups()
                    function_stats['Chat2Agent']['agents'][agent_name] = function_stats['Chat2Agent']['agents'].get(agent_name, 0) + 1
                    # 统计活跃次数
                    date = timestamp.split(' ')[0]
                    if date not in daily_user_activities:
                        daily_user_activities[date] = {}
                    if username not in daily_user_activities[date]:
                        daily_user_activities[date][username] = 0
                    daily_user_activities[date][username] += 1
        
        # 准备用户访问表数据
        user_access_data = []
        for username, stats in user_stats.items():
            user_access_data.append({
                '用户名': username,
                '姓名': stats['full_name'],
                '首次登录': stats['first_login'],
                '最后登录': stats['last_login'],
                '登录次数': stats['login_count'],
                '登出次数': stats['logout_count'],
                '主页访问': stats['homepage_visits'],
                '单模型聊天访问': stats['chat2model_visits'],
                '多模型聊天访问': stats['multimodel_visits'],
                'Agent聊天访问': stats['chat2agent_visits'],
                '消息总数': stats['messages'],
                '使用模型': ', '.join(stats['models_used'])
            })
        
        user_access_df = pd.DataFrame(user_access_data)
        
        # 准备功能使用统计数据
        function_usage_data = []
        for func_name, stats in function_stats.items():
            total_models = sum(stats['models'].values()) if 'models' in stats else 0
            most_used_model = max(stats['models'], key=stats['models'].get) if 'models' in stats and stats['models'] else 'N/A'
            function_usage_data.append({
                '功能模块': func_name,
                '访问次数': stats['visits'],
                '消息总数': stats['messages'],
                '模型使用次数': total_models,
                '最常用模型': most_used_model
            })
        
        function_usage_df = pd.DataFrame(function_usage_data)
        
        # 准备模型和Agent使用统计
        all_models = {}
        for func_name, stats in function_stats.items():
            if 'models' in stats:
                for model, count in stats['models'].items():
                    all_models[model] = all_models.get(model, 0) + count
        
        all_agents = function_stats['Chat2Agent']['agents']
        
        # 功能使用统计
        with tab1:
            # 总览统计
            st.markdown("#### 系统使用总览")
            total_users = len(user_stats)
            total_messages = sum(user['messages'] for user in user_stats.values())
            total_visits = sum(func['visits'] for func in function_stats.values())
            col1, col2, col3 = st.columns(3)
            col1.metric("总用户数", total_users)
            col2.metric("总消息数", total_messages)
            col3.metric("功能模块访问", total_visits)
            
            st.markdown("#### 功能模块使用情况")
            st.dataframe(function_usage_df, width="stretch")

            # 模型使用统计
            st.markdown("#### 模型使用分布")
            models_df = pd.DataFrame(list(all_models.items()), columns=['模型', '使用次数'])
            models_df = models_df.sort_values(by='使用次数', ascending=False)
            st.bar_chart(models_df.set_index('模型')['使用次数'],sort=False)
            
            # Agent使用统计
            st.markdown("#### Agent使用分布")
            agents_df = pd.DataFrame(list(all_agents.items()), columns=['Agent', '使用次数'])
            agents_df = agents_df.sort_values(by='使用次数', ascending=False)
            st.bar_chart(agents_df.set_index('Agent')['使用次数'],sort=False)
            
        
        # 用户访问表
        with tab2:
            # 每日新增和活跃用户数统计
            # 提取所有用户的首次登录日期
            user_first_login = {}
            for username, stats in user_stats.items():
                if 'first_login' in stats:
                    first_login_date = stats['first_login'].split(' ')[0]  # 提取日期部分
                    user_first_login[username] = first_login_date
            
            if user_first_login or daily_user_activities:
                # 统计每日新增用户数（按首次登录日期）
                new_users_by_date = {}
                for username, date in user_first_login.items():
                    if date not in new_users_by_date:
                        new_users_by_date[date] = 0
                    new_users_by_date[date] += 1
                
                # 统计每日活跃用户数和总活跃次数
                active_users_by_date = {}
                total_activities_by_date = {}
                for date, user_activities in daily_user_activities.items():
                    active_users_by_date[date] = len(user_activities)
                    total_activities_by_date[date] = sum(user_activities.values())
                
                # 创建DataFrame
                dates = sorted(set(new_users_by_date.keys()) | set(active_users_by_date.keys()))
                data = []
                data_activity = []
                for date in dates:
                    data.append({
                        'date': date,
                        'new_users': new_users_by_date.get(date, 0),
                        'active_users': active_users_by_date.get(date, 0),
                    })
                    data_activity.append({
                        'date': date,
                        'total_activities': total_activities_by_date.get(date, 0)
                    })
                
                activity_df = pd.DataFrame(data_activity)
                activity_df = activity_df.sort_values('date')
                
                merged_df = pd.DataFrame(data)
                merged_df = merged_df.sort_values('date')

                # 数据展示
                # 绘制总活跃次数折线图
                st.markdown("#### 每日总活跃次数") 
                st.line_chart(activity_df.set_index('date'), width="stretch")
                
                # 绘制新增和活跃用户数折线图
                st.markdown("#### 每日新增和活跃用户数") 
                st.line_chart(merged_df.set_index('date'), width="stretch")
                
                # 统计每天每个活跃用户的活跃次数
                st.markdown("#### 每日用户活跃次数详情")
                user_activity_data = []
                for date, user_activities in daily_user_activities.items():
                    for username, count in user_activities.items():
                        user_activity_data.append({
                            'date': date,
                            'username': username,
                            'activity_count': count
                        })
                
                if user_activity_data:
                    user_activity_df = pd.DataFrame(user_activity_data)
                    user_activity_df = user_activity_df.sort_values(['date', 'username'])
                    st.dataframe(user_activity_df, width="stretch")
                else:
                    st.write("暂无用户活跃数据")
            else:
                st.write("暂无用户数据")
            
            
            st.markdown("#### 用户总访问详细信息")
            st.dataframe(user_access_df, width="stretch")
            st.markdown("#### 用户总活跃度统计")
            # 按消息数排序的用户
            active_users_df = user_access_df.sort_values(by='消息总数', ascending=False)[['用户名', '姓名', '消息总数', '主页访问']]
            st.bar_chart(active_users_df.set_index('用户名')['消息总数'],sort=False)
            
