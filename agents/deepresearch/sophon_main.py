import sys
import os
from tkinter import S
# 添加项目根目录到 Python 路径
root_dir=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
deepresearch_dir=os.path.dirname(os.path.abspath(__file__))
sys.path.append(deepresearch_dir)
sys.path.append(root_dir)

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from draft_research import AgentState, InputSchema, clarify_with_user, write_research_brief, write_draft_report
from subgraph import supervisor_agent
from models import init_model
from prompts import final_report_generation_with_helpfulness_insightfulness_hit_citation_prompt
from utils import get_today_str


writer_model = init_model(temperature=0.7, model_name="SF_Qwen3-8B")

async def final_report_generation(state: AgentState):
    """
    Final report generation node.

    Synthesizes all research findings into a comprehensive final report
    """

    notes = state.get("notes", [])

    findings = "\n".join(notes)

    final_report_prompt = final_report_generation_with_helpfulness_insightfulness_hit_citation_prompt.format(
        research_brief=state.get("research_brief", ""),
        findings=findings,
        date=get_today_str(),
        draft_report=state.get("draft_report", ""),
        user_request=state.get("user_request", "")
    )

    final_report = await writer_model.ainvoke([HumanMessage(content=final_report_prompt)])

    return {
        "final_report": final_report.content, 
        "messages": ["Here is the final report: " + final_report.content],
    }


# 构建状态图
sophon_builder = StateGraph(AgentState, input_schema=InputSchema)

# Add workflow nodes
sophon_builder.add_node("clarify_with_user", clarify_with_user)
sophon_builder.add_node("write_research_brief", write_research_brief)
sophon_builder.add_node("write_draft_report", write_draft_report)
sophon_builder.add_node("supervisor_subgraph", supervisor_agent)
sophon_builder.add_node("final_report_generation", final_report_generation)

# Add workflow edges
sophon_builder.add_edge(START, "clarify_with_user")
sophon_builder.add_edge("write_research_brief", "write_draft_report")
sophon_builder.add_edge("write_draft_report", "supervisor_subgraph")
sophon_builder.add_edge("supervisor_subgraph", "final_report_generation")
sophon_builder.add_edge("final_report_generation", END)

# Compile the full workflow
Sophon = sophon_builder.compile()


async def stream_run(query: str):
    async for item in Sophon.astream({"messages": [HumanMessage(content=query)]},version="v1",stream_mode="updates"):
        for node, data in item.items():
            print("#"*30 + "节点：" + node + "#"*30)
            print(data)
            if node == "final_report_generation":
                print("="*30 + "最终报告：" + "="*30)
                print(data.get("final_report", ""))
    
if __name__ == "__main__":
    # draw the graph
    #graph_png_data = sophon_research.get_graph(xray=True).draw_mermaid_png(output_file_path="sophon_research1.png")
    
    query="在基于大模型的AI智能体（Agent）开发中，有很多有用的设计模式。反思模式（reflection pattern）就是其中之一。请详细研究一下反思模式的概念、基本特点、适用场景、实现方式等，并使用python语言基于LangGraph框架实现一个简单的反思模式智能体，要有实际的应用场景。"
    import asyncio
    #asyncio.run(agent.ainvoke({"messages": [HumanMessage(content="请研究一下中国的历史")]}))
    asyncio.run(stream_run(query))
