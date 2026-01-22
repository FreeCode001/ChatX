"""
ChatX UI：第三方模型接入配置页面
"""
# encoding=utf-8
import os
import sys
import yaml
import logging
from yaml.loader import SafeLoader

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

import streamlit as st
from auth import check_authentication

# 初始化日志
logger = logging.getLogger('ChatX-ModelEnroll')


# 设置页面配置
st.set_page_config(
    page_title="第三方模型接入",
    page_icon="🔧",
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
    /* 表单样式优化 */
    .stForm {
        padding: 20px;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
    /* 卡片样式 */
    .stCard {
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """
# 注入基本样式
st.markdown(basic_styles, unsafe_allow_html=True)

# 核心：全局登录验证（未登录则无法访问）
authenticator, name, username, config = check_authentication()

if f'model_enroll_page_{username}' not in st.session_state:
    logger.info(f'用户：{username} | 访问模型接入页面: 用户 {username} ({name}) 进入模型接入配置页面')
    st.session_state[f'model_enroll_page_{username}'] = True

# 标题
st.markdown("<h1 style='text-align: center; color: #2c3e50; margin: 20px 0;'>🔧 第三方模型接入配置</h1>", unsafe_allow_html=True)
st.markdown("<div style='background: linear-gradient(90deg, #3498db, #2ecc71); height: 3px; margin-bottom: 30px; border-radius: 2px;'></div>", unsafe_allow_html=True)

# 配置文件路径
config_file = os.path.join(root_dir, 'models_config.yaml')

# 读取现有配置
def load_existing_config():
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.load(f, Loader=SafeLoader)
    except Exception as e:
        st.error(f"读取配置文件失败: {e}")
        return dict()

# 保存配置到文件
def save_config(new_config):
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        st.error(f"保存配置文件失败: {e}")
        return False

# 主内容区
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    # 添加新模型表单
    st.markdown("<h3 style='color: #34495e;'>添加新模型</h3>", unsafe_allow_html=True)
    with st.form("model_enroll_form", clear_on_submit=True):
        st.markdown("填写以下信息以添加新的第三方模型")
        
        # 模型基本信息
        model_name = st.text_input("模型名称", placeholder="例如：MyCustomModel")
        display_name = st.text_input("显示名称", placeholder="例如：自定义模型")
        
        # API配置
        model_provider = st.selectbox(
            "模型接口类型",
            ["openai", "anthropic", "azure", "google", "其他"]
        )
        
        if model_provider == "其他":
            model_provider = st.text_input("请输入模型提供者")
        
        api_key = st.text_input("API Key", type="password", placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxx")
        base_url = st.text_input("API Base URL", placeholder="例如：https://api.openai.com/v1")
        model_id = st.text_input("模型ID", placeholder="例如：gpt-3.5-turbo")
        
        # 高级配置
        with st.expander("高级配置"):
            temperature = st.slider("温度参数", 0.0, 2.0, 0.7, 0.1)
            max_tokens = st.number_input("最大令牌数", 1, 100000, 64000, 1000)
            description = st.text_area("模型描述", placeholder="简要描述这个模型的特点和用途")
        
        # 提交按钮
        submitted = st.form_submit_button("保存模型配置", type="primary", width="stretch")
        
        if submitted:
            if not model_name or not display_name or not api_key or not model_id:
                st.error("请填写必填字段：模型名称、显示名称、API Key和模型ID")
            else:
                # 加载现有配置
                existing_config = load_existing_config()
                
                # 确保models配置部分存在
                if "models" not in existing_config:
                    existing_config["models"] = {}
                
                # 添加新模型配置
                keystr= f"PRIVATE_{model_name}"
                existing_config["models"][username] = {keystr: {
                    "display_name": display_name,
                    "provider": model_provider,
                    "api_key": api_key,
                    "base_url": base_url,
                    "model_id": model_id,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "description": description
                }}
                
                # 保存配置
                if save_config(existing_config):
                    st.success(f"模型 {display_name} 配置成功！")
                    logger.info(f'用户：{username} | 添加新模型: 成功添加模型 {model_name} ({display_name})')
                    # 重置表单
                    st.rerun()
                else:
                    st.error("保存配置失败，请检查权限和文件路径")

with col2:
    # 现有模型列表
    st.markdown("<h3 style='color: #34495e;'>已配置模型</h3>", unsafe_allow_html=True)
    
    # 加载现有配置
    existing_config = load_existing_config()
    
    if "models" in existing_config and existing_config["models"]:
        for model_name, model_config in existing_config["models"].get(username, {}).items():
            with st.expander(f"{model_config['display_name']} ({model_name})"):
                col_info1, col_info2 = st.columns([2, 1])
                
                with col_info1:
                    st.markdown(f"**模型接口类型**: {model_config['provider']}")
                    st.markdown(f"**模型ID**: {model_config['model_id']}")
                    if model_config['base_url']:
                        st.markdown(f"**API Base URL**: {model_config['base_url']}")
                    st.markdown(f"**温度参数**: {model_config['temperature']}")
                    st.markdown(f"**最大令牌数**: {model_config['max_tokens']}")
                    if model_config['description']:
                        st.markdown(f"**描述**: {model_config['description']}")
                
                with col_info2:
                    # 删除按钮
                    if st.button("删除模型", key=f"delete_{model_name}", type="secondary", width="stretch"):
                        # 删除模型配置
                        del existing_config["models"][username][model_name]
                        if save_config(existing_config):
                            st.success(f"模型 {model_config['display_name']} 已删除！")
                            logger.info(f'用户：{username} | 删除模型: 成功删除模型 {model_name} ({model_config["display_name"]})')
                            st.rerun()
                        else:
                            st.error("删除模型失败，请检查权限")
    else:
        st.info("暂无已配置的第三方模型")

# 模型使用说明
st.markdown("<h3 style='color: #34495e; margin-top: 40px;'>使用说明</h3>", unsafe_allow_html=True)
with st.expander("查看详细说明"):
    st.markdown("""
    ### 如何使用已添加的模型
    
    1. **添加模型后**：
       - 配置会自动保存到 `config.yaml` 文件
       - 您需要重启应用才能在聊天界面看到新添加的模型
    
    2. **在聊天界面使用**：
       - 打开 Chat2Model 或 MultiModelChat 页面
       - 在模型选择下拉框中选择您添加的模型
       - 开始与模型对话
    
    ### 支持的模型提供者
    
    - **OpenAI**：支持GPT系列模型
    - **Anthropic**：支持Claude系列模型
    - **Azure**：支持Azure OpenAI服务
    - **Google**：支持Gemini系列模型
    - **其他**：支持自定义模型提供者
    
    ### 注意事项
    
    - API Key会安全存储在配置文件中
    - 请确保您有使用第三方模型的合法权限
    - 某些模型可能需要特定的API格式或参数
    - 如果遇到问题，请检查API Key和Base URL是否正确
    """)
