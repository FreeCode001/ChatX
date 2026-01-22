
"""Research Agent Implementation.

This module implements a research agent that can perform iterative web searches
and synthesis to answer complex research questions.
"""
import sys
import os
# 添加项目根目录到 Python 路径
root_dir=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
deepresearch_dir=os.path.dirname(os.path.abspath(__file__))
sys.path.append(deepresearch_dir)
sys.path.append(root_dir)

from typing_extensions import Literal

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages

from states import ResearcherState, ResearcherOutputState
from utils import get_today_str
from tools import think_tool, tavily_search
from prompts import research_agent_prompt, compress_research_system_prompt, compress_research_human_message
from models import init_model

# ===== CONFIGURATION =====

# Set up tools and model binding
tools = [tavily_search, think_tool]
tools_by_name = {tool.name: tool for tool in tools}
max_tool_call_iterations = 5

# Initialize models
model = init_model(temperature=0.7, model_name="SF_Qwen3-8B")
model_with_tools = model.bind_tools(tools)
summarization_model = model
compress_model = model


# ===== AGENT NODES =====

def llm_call(state: ResearcherState):
    """Analyze current state and decide on next actions.

    The model analyzes the current conversation state and decides whether to:
    1. Call search tools to gather more information
    2. Provide a final answer based on gathered information

    Returns updated state with the model's response.
    """
    return {
        "researcher_messages": [
            model_with_tools.invoke(
                [SystemMessage(content=research_agent_prompt)] + state["researcher_messages"]
            )
        ],
        # Add tool call iterations to state
        "tool_call_iterations": state.get("tool_call_iterations", 0)
    }

def tool_node(state: ResearcherState):
    """Execute all tool calls from the previous LLM response.

    Executes all tool calls from the previous LLM responses.
    Returns updated state with tool execution results.
    """
    tool_calls = state["researcher_messages"][-1].tool_calls

    # Execute all tool calls
    observations = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observations.append(tool.invoke(tool_call["args"]))

    # Create tool message outputs
    tool_outputs = [
        ToolMessage(
            content=observation,
            name=tool_call["name"],
            tool_call_id=tool_call["id"]
        ) for observation, tool_call in zip(observations, tool_calls)
    ]

    # Update tool call iterations
    if "tavily_search" in [tool_call["name"] for tool_call in tool_calls]:
        tool_call_iterations = state.get("tool_call_iterations", 0) + 1
    else:
        tool_call_iterations = state.get("tool_call_iterations", 0)

    return {"researcher_messages": tool_outputs, "tool_call_iterations": tool_call_iterations}

def compress_research(state: ResearcherState) -> dict:
    """Compress research findings into a concise summary.

    Takes all the research messages and tool outputs and creates
    a compressed summary suitable for the supervisor's decision-making.
    """

    system_message = compress_research_system_prompt.format(date=get_today_str())
    messages = [SystemMessage(content=system_message)] + state.get("researcher_messages", []) + [HumanMessage(content=compress_research_human_message)]
    response = compress_model.invoke(messages)

    # Extract raw notes from tool and AI messages
    raw_notes = [
        str(m.content) for m in filter_messages(
            state["researcher_messages"], 
            include_types=["tool", "ai"]
        )
    ]

    return {
        "compressed_research": str(response.content),
        "raw_notes": ["\n".join(raw_notes)]
    }

# ===== ROUTING LOGIC =====

def should_continue(state: ResearcherState) -> Literal["tool_node", "compress_research"]:
    """Determine whether to continue research or provide final answer.

    Determines whether the agent should continue the research loop or provide
    a final answer based on whether the LLM made tool calls.

    Returns:
        "tool_node": Continue to tool execution
        "compress_research": Stop and compress research
    """
    messages = state["researcher_messages"]
    last_message = messages[-1]

    if state.get("tool_call_iterations", 0) >= max_tool_call_iterations:
        return "compress_research"
    # If the LLM makes a tool call, continue to tool execution
    if last_message.tool_calls:
        return "tool_node"
    # Otherwise, we have a final answer
    return "compress_research"

# ===== GRAPH CONSTRUCTION =====

# Build the agent workflow
agent_builder = StateGraph(ResearcherState, output_schema=ResearcherOutputState)

# Add nodes to the graph
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("compress_research", compress_research)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node", # Continue research loop
        "compress_research": "compress_research", # Provide final answer
    },
)
agent_builder.add_edge("tool_node", "llm_call") # Loop back for more research
agent_builder.add_edge("compress_research", END)

# Compile the agent
researcher_agent = agent_builder.compile()


if __name__ == "__main__":
    # Draw the graph and save it to a file
    #researcher_agent.get_graph().draw_mermaid_png(output_file_path="researcher_agent.png")

    # Test the agent with a sample query
    query = "量子计算有什么最新进展?"
    config = {"stream_mode": "updates", "recursion_limit": 100}
    for chunk in researcher_agent.stream({"researcher_messages": [HumanMessage(content=query)]},config=config):
        node, event = next(iter(chunk.items()))
        if node != "compress_research":
            print("="*30 + "节点：" + node + "="*30)
            print("tool_call_iterations：" + str(event.get("tool_call_iterations", 0)))
            #print(event)
            event.get("researcher_messages", [])[-1].pretty_print()
        else:
            print("="*30 + "节点：" + node + "="*30)
            print("compressed_research：" + event.get("compressed_research", ""))
            print("raw_notes：" + str(event.get("raw_notes", [])))
