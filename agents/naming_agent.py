import os
import sys
# 添加项目根目录到Python路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
from models import init_model
from langchain_core.messages import HumanMessage, AIMessage

class NameAgent:
    def __init__(self):
        self.extract_model = init_model(temperature=0.3,model_name="SF_Qwen3-8B")
        #self.extract_model = init_model(temperature=0.3,model_name="ZP_GLM-4.7-Flash")
        self.naming_model = init_model(temperature=0.9,model_name="SF_Qwen3-8B")
        self.state = {"messages": []}
    
    def invoke(self, user_input: str):
        if len(self.state["messages"])>=200:
            self.state["messages"] = []
        self.state["messages"].append(HumanMessage(content=user_input))
        extract_prompt=f"""#任务：从用户输入中提取用户名字，返回由用户名字每个字的拼音首字母拼接成的字符串。
        #用户输入为：{user_input}。

        #举例：
        ##例子1：
        用户输入：我是张三。
        返回结果：ZS  

        ##例子2：
        用户输入：赵文成。
        返回结果：ZWC

        ##例子3：
        用户输入：zhaoyunyi。
        返回结果：ZYY


        #要求：返回结果应只包含字母，不要带其他东西。"""
        short_name=self.extract_model.invoke(extract_prompt)
        #print("输出名字首字母：" + short_name)
        naming_prompt = f"以首字母{short_name}生成15个好听的网名，兼顾意境美感与读音流畅度，涵盖文雅、深情、励志、诙谐、大气、有趣、婉约、豪放、哲理、寓意、温柔、清冷、诗意等多元风格。并为每个网名搭配上匹配的个性签名。要求结果以MarkDown格式输出。"
        res=self.naming_model.invoke(naming_prompt)
        self.state["messages"].append(AIMessage(content=res.content))
        return self.state

Name_Agent=NameAgent()

if __name__=="__main__":
    user_input="我的名字是赵文成。"
    print("开始执行")
    res=Name_Agent.invoke(user_input)
    print(res)