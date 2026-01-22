"""
ChatX UI：基于Streamlit框架的Web应用，用于与大模型进行交互。
"""
# encoding=utf-8
import os
import sys
import time
import logging
import asyncio

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

import streamlit as st
from models import init_model
from agents import QAAgent, Name_Agent, Sophon
from auth import check_authentication

# 初始化日志
logger = logging.getLogger('ChatX-Chat2Agent')


# 设置页面配置
st.set_page_config(
    page_title="Chat2Agent",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# 基本样式 - 只保留必要的美化
basic_styles = """
    <style>
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    #footer {visibility: hidden;}
        /* 聊天输入框样式 - 更精确的选择器 */
        div[data-testid="stChatInput"] {
            width: 40% !important;
            margin: 2px auto !important;  /* 上外边距1rem，右外边距auto，下外边距1rem，左外边距auto */
            display: block !important;
        }
        /* 输入框主容器样式 */
        div[data-testid="stChatInput"] > div {
            height: 80px !important;  /* 增加高度一倍 */
            min-height: 80px !important;
            max-height: 160px !important;
            display: flex !important;
            align-items: center !important;
        }
        /* 发送按钮容器样式 */
        div[data-testid="stChatInput"] button {
            height: 80px !important;
            min-height: 80px !important;
            max-height: 80px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
    </style>
    """
# 注入基本样式
st.markdown(basic_styles, unsafe_allow_html=True)

# 核心：全局登录验证（未登录则无法访问）
authenticator, name, username, config = check_authentication()
if f'chat2agentpage_{username}' not in st.session_state:
    logger.info(f'用户：{username} | 访问Chat2Agent: 用户 {username} ({name})进入Chat2Agent页面')
    st.session_state[f'chat2agentpage_{username}'] = True


# 侧边栏配置
with st.sidebar:
    temperature = st.slider(
            "设置大模型创造性：",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1
        )
    # 清空对话按钮
    if st.button("清空对话", width='stretch'):
        st.session_state["agent_messages"] = []
        logger.info(f'用户：{username} | 用户 {st.session_state.get("username", "未知用户")} 清空了Agent对话历史')
    
    st.markdown("---")
    st.markdown("### 关于 ChatX")
    st.markdown("基于Streamlit的AI聊天助手")

# 主聊天界面 - 简化布局
## 标题
st.markdown("<h1 style='text-align: center; color: #2c3e50; margin: 0px;'>💬 Chat2Agent聊天助手</h1>", unsafe_allow_html=True)
st.markdown("<div style='background: linear-gradient(90deg, #3498db, #2ecc71); height: 3px; margin-bottom: 10px; border-radius: 2px;'></div>", unsafe_allow_html=True)

## 模型选择控件 - 放在容器外部，不会被滚动影响
agent_option = st.selectbox(
    "选择Agent：",
    ("问答Agent", "起网名Agent", "深度研究Agent"),
    key="agent_select",
    placeholder="请选择一个Agent...",
    label_visibility="visible",
    width=200,
)
if agent_option == "起网名Agent":
    st.warning("本Agent响应可能耗费20分钟左右的时间，请耐心等待。")
elif agent_option =="深度研究Agent":
    col1, col2 = st.columns([2,1],gap="large")
    with col1:
        with st.status("深度研究执行时间较长，大约需要30分钟至1小时。当前执行状态如下：", expanded=True) as status:
            status.write("让我们开始研究吧，请在输入框输入您的问题。")
    with col2:
        btn_holder=st.empty()
        btn_holder.download_button(label="下载报告",data="",file_name="report.md",mime="text/markdown",icon=":material/download:",disabled=True)

# 初始化会话状态
if "agent_messages" not in st.session_state:
    st.session_state["agent_messages"] = []
# 消息大于等于200条强制清空
if len(st.session_state["agent_messages"]) >= 200:
    st.session_state["agent_messages"] = []
    st.warning("对话轮数超过100轮，强制清空历史消息！")
# 初始化或更新Agent选项
if "agent_option" not in st.session_state:
    st.session_state["agent_option"] = agent_option
    logger.info(f'用户：{username} | 用户 {st.session_state.get("username", "未知用户")} 初始化选择了 {agent_option}')
else:
    # 更新Agent选择
    if st.session_state["agent_option"] != agent_option:
        logger.info(f'用户：{username} | 用户 {st.session_state.get("username", "未知用户")} 将Agent从 {st.session_state["agent_option"]} 更改为 {agent_option}')
        st.session_state["agent_option"] = agent_option

# 根据选择的模型选项初始化或更新模型实例
agent_model_mapping = {
    "问答Agent": "ZP_GLM-4.7-Flash", 
    "起网名Agent": "ZP_GLM-4.7-Flash",
    "深度研究Agent": "ZP_GLM-4.7-Flash"   
}
selected_model = agent_model_mapping.get(agent_option,"ZP_GLM-4.7-Flash")

# 使用选择的模型名称和当前温度值初始化模型
st.session_state["agent_model"] = init_model(
    temperature=temperature, 
    model_name=selected_model
)
#st.info(selected_model)
if st.session_state["agent_option"] == "问答Agent":
    st.session_state["agent"] = QAAgent
elif st.session_state["agent_option"] == "起网名Agent":
    st.session_state["agent"] = Name_Agent
elif st.session_state["agent_option"] == "深度研究Agent":
    st.session_state["agent"] = Sophon

# 聊天历史区域 - 创建独立的滚动容器
agent_messages_container = st.container(height=300, key="chat2agent_messages_container")
with agent_messages_container:
    # 聊天历史区域 - 按顺序显示每条消息
    for message in st.session_state.agent_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 深度研究agent流式状态输出
async def stream_run(initial_state: str):
    final_report = ""
    async for item in st.session_state.agent.astream(initial_state,stream_mode="updates"):
        for node, data in item.items():
            status.write(node + "步骤执行完成。")
            if node == "final_report_generation":
                final_report = data.get("final_report", "")
                status.write("深度研究全部完成！")
    return final_report
## 用户输入框
if st.session_state["agent_option"] == "起网名Agent":
    prompt = st.chat_input("请输入您的姓名...",key="main_chat_input")
else:
    prompt = st.chat_input("请输入您的问题...",key="main_chat_input")

if prompt:
    # 添加用户消息到会话状态
    st.session_state["agent_messages"].append({"role": "user", "content": prompt})
    logger.info(f'用户：{username} | 用户 {st.session_state.get("username", "未知用户")} 向 {agent_option} 输入问题: {prompt[:50]}... (完整长度: {len(prompt)} 字符)')

    with agent_messages_container:
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 初始化状态
        if st.session_state["agent_option"]== "问答Agent":
            max_iterations = 2
            initial_state = {
                "messages": [{"role": "user", "content": prompt}],
                "reflection": "",
                "is_refined": False,
                "iterations": 0,
                "max_iterations": max_iterations
            }
        elif st.session_state["agent_option"]== "起网名Agent":
            initial_state = prompt
        elif st.session_state["agent_option"] == "深度研究Agent":
            initial_state = {"messages": [{"role": "user", "content": prompt}]}
        
        # 显示助手回复
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # 模拟打字效果
            try:
                # 调用Agent获取回复
                if st.session_state.agent:
                    logger.info(f'用户：{username} | 调用 {agent_option} 处理用户请求')
                    if st.session_state["agent_option"] == "深度研究Agent":
                        full_response = asyncio.run(stream_run(initial_state))
                        message_placeholder.markdown(full_response)
                        logger.info(f'用户：{username} | {agent_option} 成功返回响应 (长度: {len(full_response)} 字符)')
                        btn_holder.download_button(label="下载报告",data=full_response,file_name="report.md",mime="text/markdown",icon=":material/download:")
                    else:
                        result = st.session_state.agent.invoke(initial_state)
                        response = result["messages"][-1]
                        
                        # 模拟打字效果
                        for chunk in response.content.split(" "):
                            full_response += chunk + " "
                            time.sleep(0.05)
                            message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)
                        logger.info(f'用户：{username} | {agent_option} 成功返回响应 (长度: {len(full_response)} 字符)')
                else:
                    message_placeholder.error("Agent初始化失败，请检查配置")
                    full_response = "Agent初始化失败，请检查配置"
                    logger.error(f'用户：{username} | Agent初始化失败: 用户 {st.session_state.get("username", "未知用户")} 尝试使用 {agent_option} 但失败')
            except Exception as e:
                message_placeholder.error(f"请求失败: {e}")
                full_response = f"请求失败: {e}"
                logger.error(f'用户：{username} | Agent请求失败: {agent_option} 处理用户请求时发生错误 - {e}')
    
    # 添加助手回复到会话状态
    st.session_state["agent_messages"].append({"role": "assistant", "content": full_response})
    
