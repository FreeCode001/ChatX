"""
测试数据统计的正则表达式模式
"""
import re

login_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \|登录成功: 用户 (\w+) \((.*?)\) 已成功登录系统')
logout_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \| 退出登录')
homepage_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \| 访问ChatX主页')
chat2model_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ChatX-Chat2Model - INFO - 用户：(\w+) \| 访问Chat2Model:.*?')
multimodel_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ChatX-MultiModelChat - INFO - 用户：(\w+) \| 访问MultiModelChat:.*?')
chat2agent_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ChatX-Chat2Agent - INFO - 用户：(\w+) \| 访问Chat2Agent:.*?')
message_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \|\s*用户.*?输入问题:.*?')
model_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \|.*?模型 ([\w-]+) 处理用户请求')
agent_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) -.*? - INFO - 用户：(\w+) \|.*?调用 (.*?) 处理用户请求')

login_log = ["2026-01-23 00:33:34,401 - ChatX-auth - INFO - 用户：monkey |登录成功: 用户 monkey (大圣 sun 大圣 sun) 已成功登录系统"]
logout_log = ["2026-01-23 00:33:52,640 - ChatX-main - INFO - 用户：monkey | 退出登录"]
homepage_log = ["2026-01-23 00:58:09,848 - ChatX-main - INFO - 用户：monkey | 访问ChatX主页"]
chat2model_log = ["2026-01-23 00:16:55,070 - ChatX-Chat2Model - INFO - 用户：yuyang | 访问Chat2Model: 用户 yuyang (yu yang yu yang)进入Chat2Model页面"]
multimodel_log = ["2026-01-23 00:58:15,143 - ChatX-MultiModelChat - INFO - 用户：monkey | 访问MultiModelChat: 用户 monkey (大圣 sun 大圣 sun)进入MultiModelChat页面"]
chat2agent_log = ["2026-01-20 13:06:48,791 - ChatX-Chat2Agent - INFO - 用户：yuyang | 访问Chat2Agent: 用户 yuyang (yu yang yu yang)进入Chat2Agent页面"]
message_log = ["2026-01-20 13:10:22,607 - ChatX-Chat2Model - INFO - 用户：monkey |用户 monkey 输入问题:","2026-01-21 17:51:52,982 - ChatX-Chat2Agent - INFO - 用户：monkey | 用户 monkey 向 深度研究Agent 输入问题:","2026-01-22 12:42:19,631 - ChatX-MultiModelChat - INFO - 用户：yuyang | 用户 yuyang 在 col1 中输入问题:","2026-01-22 12:42:20,455 - ChatX-MultiModelChat - INFO - 用户：yuyang | 用户 yuyang 在 col2 中输入问题:","2026-01-22 12:42:23,421 - ChatX-MultiModelChat - INFO - 用户：yuyang | 用户 yuyang 在 col3 中输入问题:"]
model_log = ["2026-01-20 13:04:42,125 - ChatX-Chat2Model - INFO - 用户：yuyang |调用模型 Qwen3 处理用户请求","2026-01-20 13:06:16,148 - ChatX-MultiModelChat - INFO - 用户：yuyang | 调用 col1 中的模型 Qwen3 处理用户请求","2026-01-20 13:06:17,698 - ChatX-MultiModelChat - INFO - 用户：yuyang | 调用 col2 中的模型 Qwen3 处理用户请求","2026-01-20 13:06:18,447 - ChatX-MultiModelChat - INFO - 用户：yuyang | 调用 col3 中的模型 Qwen3 处理用户请求","2026-01-23 10:26:46,953 - ChatX-Chat2Model - INFO - 用户：monkey |调用模型 SF_DeepSeek-R1-7B 处理用户请求"]
agent_log = ["2026-01-21 17:51:52,987 - ChatX-Chat2Agent - INFO - 用户：monkey | 调用 深度研究Agent 处理用户请求"]

# 测试所有模式
patterns = {
    'login_pattern': (login_pattern, login_log),
    'logout_pattern': (logout_pattern, logout_log),
    'homepage_pattern': (homepage_pattern, homepage_log),
    'chat2model_pattern': (chat2model_pattern, chat2model_log),
    'multimodel_pattern': (multimodel_pattern, multimodel_log),
    'chat2agent_pattern': (chat2agent_pattern, chat2agent_log),
    'message_pattern': (message_pattern, message_log),
    'model_pattern': (model_pattern, model_log),
    'agent_pattern': (agent_pattern, agent_log)
}

print("开始测试正则表达式模式...\n")
#patterns = {'model_pattern': (model_pattern, model_log)}

for pattern_name, (pattern, logs) in patterns.items():
    print(f"测试 {pattern_name}:")
    print(f"模式: {pattern.pattern}")
    
    total_matches = 0
    for log in logs:
        match = pattern.search(log)
        if match:
            print(f"  ✓ 匹配: {log[:60]}...")
            print(f"    提取的组: {match.groups()}")
            total_matches += 1
        else:
            print(f"  ✗ 不匹配: {log[:60]}...")
    
    print(f"  结果: {total_matches}/{len(logs)} 个匹配\n")

print("测试完成！")


