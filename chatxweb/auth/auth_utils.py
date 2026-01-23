# auth_utils.py
# encoding=utf-8
import os
import sys
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)
import streamlit as st
import streamlit_authenticator as stauth
import yaml
import logging
import time
from yaml.loader import SafeLoader

# 初始化日志
logger = logging.getLogger('ChatX-auth')

# 读取配置文件
def load_config():
    try:
        with open(os.path.join(root_dir, 'config.yaml')) as file:
            config = yaml.load(file, Loader=SafeLoader)
    except Exception as e:
        st.error(e)
        st.stop()
    return config

# 初始化认证器
def init_authenticator():
    try:
        config = load_config()
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
        )
        return authenticator, config
    except Exception as e:
        st.error(e)
        st.stop()   

# 获取用户角色
def get_user_roles(username: str):
    config = load_config()
    user_infos = config['credentials']['usernames'].get(username, {})
    if 'roles' in user_infos:
        user_roles = user_infos.get('roles', ['user'])
    else:
        user_roles = ['user']
    return user_roles

# 全局登录验证：未登录则终止访问
def check_authentication():
    # 初始化认证器
    authenticator, config = init_authenticator()
    
    # 从会话状态获取登录状态（跨页面共享）
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = None
    
    if st.session_state['authentication_status'] != True:
        # 若未登录，渲染登录表单
        tab1, tab2 = st.tabs(["**登录**", "**注册**"])
        with tab1:
            tab1_info_holder = st.empty()
            authenticator.login('main',fields={'Form name':'用户登入', 'Username':'用户名', 'Password':'密码', 'Login':'登入', 'Captcha':'验证码'},key='用户登入')
        with tab2:
            tab2_info_holder = st.empty()
            try:
                email, username, name = authenticator.register_user('main',fields= {'First name':'名字','Last name':'姓氏','Form name':'用户注册', 'Email':'Email', 'Username':'用户名', 'Password':'密码', 'Repeat password':'重复密码', 'Password hint':'密码提示词', 'Captcha':'验证码', 'Register':'注册'},roles=['user'],key='用户注册')
                if email:
                    config['credentials']['usernames'][username]['email'] = email
                    config['credentials']['usernames'][username]['first_name'] = name
                    config['credentials']['usernames'][username]['last_name'] = name
                    with open(os.path.join(root_dir, 'config.yaml'), 'w') as file:
                        yaml.safe_dump(config, file, default_flow_style=False)
                    tab2_info_holder.success('User registered successfully')
                    logger.info(f'用户：{username} | 注册成功: 新用户 {username} ({name}) 已成功注册，邮箱: {email}')
            except Exception as e:
                tab2_info_holder.error(e)
                logger.error(f'用户：None |注册失败: 用户尝试注册时发生错误 - {e}')
        
        # 验证状态判断
        if st.session_state['authentication_status'] == False:
            tab1_info_holder.error('用户名或密码错误！',icon='❌')
            logger.warning(f'用户：{username} |登录失败: {st.session_state.get("username", "未知用户")} 尝试登录，但用户名或密码错误')
            st.stop()  # 终止脚本，阻止访问页面
        if st.session_state['authentication_status'] == None:
            tab1_info_holder.warning('请先登录以访问页面！')
            # 添加标志防止重复记录未登录访问尝试日志
            current_time = time.time()
            if 'last_anonymous_attempt' not in st.session_state or current_time - st.session_state['last_anonymous_attempt'] > 5:  # 5秒内不重复记录
                logger.info(f'用户：{username} |未登录访问尝试: 用户尝试访问受保护页面，但未提供有效的登录凭证')
                st.session_state['last_anonymous_attempt'] = current_time
            st.stop()  # 未登录时终止访问
    
    # 登录成功，返回认证器和用户信息
    # 添加标志防止重复记录登录日志
    if 'login_logged' not in st.session_state or not st.session_state['login_logged']:
        logger.info(f'用户：{st.session_state["username"]} |登录成功: 用户 {st.session_state["username"]} ({st.session_state["name"]}) 已成功登录系统')
        st.session_state['login_logged'] = True
    return authenticator, st.session_state['name'], st.session_state['username'], config