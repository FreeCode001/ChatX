# encoding=utf-8
import streamlit as st
import time
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from models import init_model, get_available_models
from auth import check_authentication

# 初始化日志
logger = logging.getLogger('ChatX-MultiModelChat')


# 设置页面配置
st.set_page_config(
    page_title="MultiModelChat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# 自定义页面样式
def custom_page_style():
    custom_style="""
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
    st.markdown(custom_style, unsafe_allow_html=True)

# 初始化列布局和状态
def init_column(col, col_key):
    with col:
        st.markdown(f"{col_key} 聊天区域")
        # 获取可用模型列表
        model_list = get_available_models(username).keys()
        # 模型选择控件 - 放在容器外部，不会被滚动影响
        model_option = st.selectbox(
            "选择模型：",
            model_list,
            key=f"{col_key}_model_select",
            placeholder="请选择一个模型...",
            label_visibility="visible",
            width=300,
        )

        # 初始化会话状态
        if f"{col_key}_messages" not in st.session_state:
            st.session_state[f"{col_key}_messages"] = []
        
        # 初始化或更新模型选项
        if f"{col_key}_model_option" not in st.session_state:
            st.session_state[f"{col_key}_model_option"] = model_option
            logger.info(f'用户：{username} | 用户 {st.session_state.get("username", "未知用户")} 为 {col_key} 初始化选择了 {model_option} 模型')
        else:
            # 更新模型选择
            if st.session_state[f"{col_key}_model_option"] != model_option:
                logger.info(f'用户：{username} | 用户 {st.session_state.get("username", "未知用户")} 将 {col_key} 的模型从 {st.session_state[f"{col_key}_model_option"]} 更改为 {model_option}')
                st.session_state[f"{col_key}_model_option"] = model_option
        
        # 使用选择的模型名称和当前温度值初始化模型
        st.session_state[f"{col_key}_model"] = init_model(
            temperature=temperature, 
            model_name=model_option
        )
        
        # 聊天历史区域 - 创建独立的滚动容器
        st.session_state[f"{col_key}_messages_container"] = st.container(height=300,key=f"{col_key}_messages_container")
        with st.session_state[f"{col_key}_messages_container"]:
            # 显示聊天历史
            for message in st.session_state[f"{col_key}_messages"]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

# 初始化线程池用于异步模型调用
executor = ThreadPoolExecutor(max_workers=3)
# 辅助函数：异步获取模型回复
async def get_model_response_async(model_instance, prompt):
    """异步获取模型回复"""
    loop = asyncio.get_event_loop()
    try:
        if model_instance:
            # 使用线程池异步调用模型
            response = await loop.run_in_executor(
                executor, 
                lambda: model_instance.invoke(prompt)
            )
            return response.content
        else:
            return "模型初始化失败，请检查配置"
    except Exception as e:
        return f"请求失败: {e}"

# 列对话处理
async def handle_column_chat(col, col_key, prompt):
    with col:
        # 添加用户消息到会话状态
        st.session_state[f"{col_key}_messages"].append({"role": "user", "content": prompt})
        
        # 在聊天历史区域内显示
        with st.session_state[f"{col_key}_messages_container"]:
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
                    if st.session_state[f"{col_key}_model"]:
                        logger.info(f'用户：{username} | 用户 {st.session_state.get("username", "未知用户")} 在 {col_key} 中输入问题: {prompt[:50]}... (完整长度: {len(prompt)} 字符)')
                        logger.info(f'用户：{username} | 调用 {col_key} 中的模型 {st.session_state[f"{col_key}_model_option"]} 处理用户请求')
                        res_content = await get_model_response_async(
                            st.session_state[f"{col_key}_model"], 
                            prompt
                        )
                        
                        # 模拟打字效果
                        for chunk in res_content.split(" "):
                            full_response += chunk + " "
                            time.sleep(0.05)
                            message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)
                        logger.info(f'用户：{username} | {col_key} 中的模型 {st.session_state[f"{col_key}_model_option"]} 成功返回响应 (长度: {len(full_response)} 字符)')
                    else:
                        message_placeholder.error("模型初始化失败，请检查配置")
                        full_response = "模型初始化失败，请检查配置"
                        logger.error(f'用户：{username} | {col_key} 中的模型初始化失败: 用户 {st.session_state.get("username", "未知用户")} 尝试使用 {st.session_state[f"{col_key}_model_option"]} 模型但失败')
                except Exception as e:
                    message_placeholder.error(f"请求失败: {e}")
                    full_response = f"请求失败: {e}"
                    logger.error(f'用户：{username} | {col_key} 中的模型请求失败: {st.session_state[f"{col_key}_model_option"]} 模型处理用户请求时发生错误 - {e}')
        # 添加助手回复到会话状态
        st.session_state[f"{col_key}_messages"].append({"role": "assistant", "content": full_response})




#==========开始页面布局==========#
# 1. 应用自定义样式
custom_page_style()

# 核心：全局登录验证（未登录则无法访问）
authenticator, name, username, config = check_authentication()
if f'multimodelchatpage_{username}' not in st.session_state:
    logger.info(f'用户：{username} | 访问MultiModelChat: 用户 {username} ({name})进入MultiModelChat页面')
    st.session_state[f'multimodelchatpage_{username}'] = True


# 2. 侧边栏配置
with st.sidebar:
    st.title("大模型设置")
    st.markdown("---")
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
    st.session_state["temperature"] = temperature
    
    
    # 清空对话按钮
    if st.button("清空对话", width='stretch'):
        for col_key in ["col1", "col2", "col3"]:
            st.session_state[f"{col_key}_messages"] = []
        logger.info(f'用户：{username} | 用户 {st.session_state.get("username", "未知用户")} 清空了多模型聊天的所有对话历史')

    st.markdown("---")
    st.markdown("### 关于 ChatX")
    st.markdown("基于Streamlit的AI聊天助手")
    st.markdown("多种大模型可供选择")

# 3. 主界面
## 3.1 标题
st.markdown("<h1 style='text-align: center; color: #2c3e50; margin: 0px;'>💬 MultiModelChat聊天助手</h1>", unsafe_allow_html=True)
st.markdown("<div style='background: linear-gradient(90deg, #3498db, #2ecc71); height: 3px; margin-bottom: 10px; border-radius: 2px;'></div>", unsafe_allow_html=True)
## 3.2 聊天区域
col1, col2, col3 = st.columns([1,1,1], gap="medium",border=True)
columns = [col1, col2, col3]
col_keys = ["col1", "col2", "col3"]

for col, col_key in zip(columns, col_keys):
    init_column(col, col_key)
    # 强制清空对话
    if len(st.session_state[f"{col_key}_messages"])>=200:
        st.session_state[f"{col_key}_messages"] = []
        st.warning("对话轮数超过100轮，强制清空历史消息！")

## 3.3 聊天输入框
if prompt := st.chat_input("请输入您的问题..."):
    for col, col_key in zip(columns, col_keys):
        asyncio.run(handle_column_chat(col, col_key, prompt))
