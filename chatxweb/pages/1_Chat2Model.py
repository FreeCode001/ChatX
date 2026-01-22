"""
ChatX UI：基于Streamlit框架的Web应用，用于与大模型进行交互。
"""
# encoding=utf-8
import os
import sys
import time
import logging

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

import streamlit as st
from models import init_model, get_available_models
from auth import check_authentication

# 初始化日志
logger = logging.getLogger('ChatX-Chat2Model')


# 设置页面配置
st.set_page_config(
    page_title="Chat2Model",
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
if f'chat2modelpage_{username}' not in st.session_state:
    logger.info(f'用户：{username} | 访问Chat2Model: 用户 {username} ({name})进入Chat2Model页面')
    st.session_state[f'chat2modelpage_{username}'] = True
    

# 侧边栏配置
with st.sidebar:
    # 模式选择
    chat_mode = st.radio(
        "选择聊天模式",
        ["默认模式", "创意模式", "精确模式"]
    ) 
    
    # 根据聊天模式设置温度值和slider可用性
    if chat_mode == "创意模式":
        temperature = 0.9  # 创意模式使用高温度值
        slider_disabled = True
    elif chat_mode == "精确模式":
        temperature = 0.1  # 精确模式使用低温度值
        slider_disabled = True
    else:  # 默认模式
        slider_disabled = False
    
    # 温度控制 - 根据模式决定是否可用
    if not slider_disabled:
        temperature = st.slider(
            "设置大模型创造性：",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1
        )
    else:
        # 不可用时显示固定值
        st.slider(
            "设置大模型创造性：",
            min_value=0.0,
            max_value=1.0,
            value=temperature,
            step=0.1,
            disabled=True
        )
    
    st.divider()
  
    # 清空对话按钮
    if st.button("清空对话", width='stretch'):
        st.session_state["messages"] = []
        logger.info(f'用户：{username} |用户 {st.session_state.get("username", "未知用户")} 清空了对话历史')

    st.markdown("---")
    st.markdown("### 关于 ChatX")
    st.markdown("基于Streamlit的AI聊天助手")

# 主聊天界面 - 简化布局
## 标题
st.markdown("<h1 style='text-align: center; color: #2c3e50; margin: 0px;'>💬 Chat2Model聊天助手</h1>", unsafe_allow_html=True)
st.markdown("<div style='background: linear-gradient(90deg, #3498db, #2ecc71); height: 3px; margin-bottom: 10px; border-radius: 2px;'></div>", unsafe_allow_html=True)

model_list = get_available_models(username).keys()
## 模型选择控件 - 放在容器外部，不会被滚动影响
model_option = st.selectbox(
    "选择模型：",
    model_list,
    key="model_select",
    placeholder="请选择一个模型...",
    label_visibility="visible",
    width=300,
)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state["messages"] = []
# 消息大于等于200条强制清空
if len(st.session_state["messages"]) >= 200:
    st.session_state["messages"] = []
    st.warning("对话轮数超过100轮，强制清空历史消息！")
# 初始化或更新模型选项
if "model_option" not in st.session_state:
    st.session_state["model_option"] = model_option
    logger.info(f'用户：{username} |用户 {st.session_state.get("username", "未知用户")} 初始化选择了 {model_option} 模型')
else:
    # 更新模型选择
    if st.session_state["model_option"] != model_option:
        logger.info(f'用户：{username} |用户 {st.session_state.get("username", "未知用户")} 将模型从 {st.session_state["model_option"]} 更改为 {model_option}')
        st.session_state["model_option"] = model_option

# 使用选择的模型名称和当前温度值初始化模型
st.session_state["model"] = init_model(
    temperature=temperature, 
    model_name=model_option
)
#st.success("选择了" + st.session_state["model_option"] + "模型")
# 聊天历史区域 - 创建独立的滚动容器
model_messages_container = st.container(height=300, key="chat2model_messages_container")
with model_messages_container:
    # 聊天历史区域 - 按顺序显示每条消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

## 用户输入框
prompt = st.chat_input("请输入您的问题...",key="main_chat_input")

if prompt:
    # 添加用户消息到会话状态
    st.session_state["messages"].append({"role": "user", "content": prompt})
    logger.info(f'用户：{username} |用户 {st.session_state.get("username", "未知用户")} 输入问题: {prompt[:50]}... (完整长度: {len(prompt)} 字符)')

    with model_messages_container:
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 显示助手回复
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # 模拟打字效果
            try:
                # 调用模型获取回复
                if st.session_state.model:
                    logger.info(f'用户：{username} |调用模型 {st.session_state["model_option"]} 处理用户请求')
                    response = st.session_state.model.invoke(prompt)
                    
                    # 模拟打字效果
                    for chunk in response.content.split(" "):
                        full_response += chunk + " "
                        time.sleep(0.05)
                        message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                    logger.info(f'用户：{username} |模型 {st.session_state["model_option"]} 成功返回响应 (长度: {len(full_response)} 字符)')
                else:
                    message_placeholder.error("模型初始化失败，请检查配置")
                    full_response = "模型初始化失败，请检查配置"
                    logger.error(f'用户：{username} |模型初始化失败: 用户 {st.session_state.get("username", "未知用户")} 尝试使用 {st.session_state["model_option"]} 模型但失败')
            except Exception as e:
                message_placeholder.error(f"请求失败: {e}")
                full_response = f"请求失败: {e}"
                logger.error(f'用户：{username} |模型请求失败: {st.session_state["model_option"]} 模型处理用户请求时发生错误 - {e}')
    
    # 添加助手回复到会话状态
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
