#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反思模式问答智能体
基于LangGraph框架实现的简单反思智能体，能够生成初始响应、自我评估并优化回答。
"""

import os
import sys
# 添加项目根目录到Python路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from typing import TypedDict, Annotated, Literal
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from models import init_model


class ReflectionQAState(TypedDict):
    """反思智能体的状态定义
    
    属性:
        messages: 对话历史消息列表
        reflection: 对响应的反思内容
        is_refined: 响应是否已优化
        iterations: 反思迭代次数
        max_iterations: 最大迭代次数（默认值）
    """
    messages: Annotated[list, operator.add]  # 对话历史，支持累加
    reflection: str  # 反思内容
    is_refined: bool  # 是否已优化
    iterations: int  # 已迭代次数
    max_iterations: int  # 最大迭代次数


# 初始化全局模型实例
model = init_model()


def generate_response(state: ReflectionQAState) -> dict:
    """生成初始响应节点
    
    参数:
        state: 当前状态
    
    返回:
        更新后的状态
    """
    print("🔄 正在生成初始响应...")
    
    # 确保max_iterations有默认值
    max_iterations = state.get("max_iterations", 2)
    
    # 系统提示词
    system_prompt = SystemMessage(content="""
    你是一个专业、友好的问答助手。
    请直接回答用户的问题，保持回答清晰、准确、全面。
    """)
    
    # 调用模型生成响应
    response = model.invoke([system_prompt] + state["messages"])
    
    return {
        "messages": [response],
        "iterations": state.get("iterations", 0) + 1,
        "is_refined": False,
        "max_iterations": max_iterations
    }


def reflect_on_answer(state: ReflectionQAState) -> dict:
    """反思评估节点
    
    参数:
        state: 当前状态
    
    返回:
        更新后的状态（包含反思内容）
    """
    print("🔍 正在反思评估响应...")
    
    messages = state["messages"]
    if not messages:
        return {"reflection": "没有可反思的消息。"}
    
    # 提取用户问题和助手响应
    user_question = None
    assistant_response = None
    
    for msg in messages:
        if isinstance(msg, HumanMessage):
            user_question = msg.content
        elif isinstance(msg, AIMessage):
            assistant_response = msg.content
    
    if not user_question or not assistant_response:
        return {"reflection": "无法提取用户问题或助手响应。"}
    
    # 生成反思
    reflection_system_prompt = SystemMessage(content="""
    你是一位专业的评估者，负责对问答质量进行严格评估。
    请客观分析响应的优点和不足，并提供具体的改进建议。
    """)
    
    reflection_query = f"""
    请评估以下对用户问题的回答：
    
    用户问题：{user_question}
    助手回答：{assistant_response}
    
    评估应包括：
    1. 回答的优点（准确性、相关性、清晰度等）
    2. 回答的不足（信息缺失、错误、表述不清等）
    3. 具体的改进建议
    """.strip()
    
    reflection_result = model.invoke([
        reflection_system_prompt,
        HumanMessage(content=reflection_query)
    ])
    
    return {"reflection": reflection_result.content}


def revise_answer(state: ReflectionQAState) -> dict:
    """修订优化节点
    
    参数:
        state: 当前状态
    
    返回:
        更新后的状态（包含优化后的响应）
    """
    print("📝 正在根据反思优化响应...")
    
    messages = state["messages"]
    reflection = state["reflection"]
    
    if not messages or not reflection:
        return {"is_refined": True}
    
    # 提取用户问题和初始响应
    user_question = None
    initial_response = None
    
    for msg in messages:
        if isinstance(msg, HumanMessage):
            user_question = msg.content
        elif isinstance(msg, AIMessage):
            initial_response = msg.content
    
    if not user_question or not initial_response:
        return {"is_refined": True}
    
    # 生成优化后的响应
    revision_system_prompt = SystemMessage(content="""
    你是一位专业的内容优化者，负责根据反思意见改进回答。
    请保持原意的同时，解决所有指出的问题，使回答更加完美。
    """)
    
    revision_query = f"""
    请根据以下反思意见，优化助手的回答：
    
    用户问题：{user_question}
    初始回答：{initial_response}
    反思意见：{reflection}
    
    优化后的回答应：
    1. 保留原有回答的优点
    2. 解决反思中指出的所有问题
    3. 保持回答的清晰、准确和全面
    4. 不要添加与问题无关的内容
    """.strip()
    
    revised_response = model.invoke([
        revision_system_prompt,
        HumanMessage(content=revision_query)
    ])
    
    # 替换最后一条消息为优化后的响应
    updated_messages = messages[:-1] + [revised_response]
    
    return {
        "messages": updated_messages,
        "is_refined": True,
        "iterations": state.get("iterations", 0) + 1
    }


def should_reflect(state: ReflectionQAState) -> Literal["reflect", END]:
    """条件边：是否需要反思
    
    参数:
        state: 当前状态
    
    返回:
        下一个节点名称
    """
    max_iterations = state.get("max_iterations", 2)
    current_iterations = state.get("iterations", 0)
    
    if not state.get("is_refined", False) and current_iterations < max_iterations:
        return "reflect"
    return END


def should_revise(state: ReflectionQAState) -> Literal["revise", END]:
    """条件边：是否需要修订
    
    参数:
        state: 当前状态
    
    返回:
        下一个节点名称
    """
    return "revise"


def build_reflection_qa_graph() -> StateGraph:
    """构建反思问答图
    
    返回:
        编译后的状态图
    """
    print("📊 正在构建反思问答图...")
    
    # 创建状态图实例
    graph_builder = StateGraph(ReflectionQAState)
    
    # 添加节点
    graph_builder.add_node("generate", generate_response)
    graph_builder.add_node("reflect", reflect_on_answer)
    graph_builder.add_node("revise", revise_answer)
    
    # 添加边
    graph_builder.add_edge(START, "generate")
    
    # 生成响应后，根据条件决定是否反思
    graph_builder.add_conditional_edges(
        "generate",
        should_reflect,
        {"reflect": "reflect", END: END}
    )
    
    # 反思后，决定是否修订
    graph_builder.add_conditional_edges(
        "reflect",
        should_revise,
        {"revise": "revise", END: END}
    )
    
    # 修订后结束
    graph_builder.add_edge("revise", END)
    
    # 编译图
    return graph_builder.compile()

QAAgent=build_reflection_qa_graph()

def run_reflection_qa_agent(question: str, max_iterations: int = 2) -> dict:
    """运行反思问答智能体
    
    参数:
        question: 用户问题
        max_iterations: 最大迭代次数
    
    返回:
        智能体运行结果
    """
    print(f"\n📋 用户问题: {question}")
    print("=" * 60)
    
    # 初始化状态
    initial_state = {
        "messages": [HumanMessage(content=question)],
        "reflection": "",
        "is_refined": False,
        "iterations": 0,
        "max_iterations": max_iterations
    }
    
    # 构建并运行图
    reflection_graph = build_reflection_qa_graph()
    
    try:
        # 生成流程图（可选）
        if not os.path.exists("images"):
            os.makedirs("images")
        
        try:
            reflection_graph.get_graph(xray=True).draw_mermaid_png(
                output_file_path="images/reflection_qa_graph.png"
            )
            print("📈 流程图已保存到: images/reflection_qa_graph.png")
        except Exception as e:
            print(f"⚠️  生成流程图失败: {e}")
        
        # 运行智能体
        config = {"run_name": "reflection_qa_agent"}
        result = reflection_graph.invoke(initial_state,config)
        return result
        
    except Exception as e:
        print(f"❌ 智能体运行失败: {e}")
        raise


if __name__ == "__main__":
    """主函数，用于测试反思问答智能体"""
    
    # 示例问题
    test_questions = [
        "什么是LangGraph，它与传统的LangChain有什么区别？",
        "解释一下Python中的装饰器，并给出几个实用的例子。",
        "如何优化RAG系统的检索效果？"
    ]
    
    print("🚀 反思模式问答智能体启动")
    print("=" * 60)
    
    try:
        # 选择一个测试问题
        question = test_questions[0]
        
        # 运行智能体
        result = run_reflection_qa_agent(question, max_iterations=2)
        
        print("=" * 60)
        print("✅ 智能体运行完成")
        print("=" * 60)
        
        # 输出结果
        print("📌 最终回答:")
        print(result['messages'][-1].content)
        print("\n💭 反思内容:")
        print(result['reflection'])
        print(f"\n🔢 迭代次数: {result['iterations']}")
        print(f"🎯 是否优化: {'是' if result['is_refined'] else '否'}")
        
    except KeyboardInterrupt:
        print("\n\n👋 用户中断程序")
    except Exception as e:
        print(f"\n\n❌ 程序出错: {e}")
    finally:
        print("\n" + "=" * 60)
        print("📋 反思模式问答智能体结束")
