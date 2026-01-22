import sys
import os
# 添加项目根目录到 Python 路径
root_dir=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
deepresearch_dir=os.path.dirname(os.path.abspath(__file__))
sys.path.append(deepresearch_dir)
sys.path.append(root_dir)

import operator
import asyncio
from langgraph.types import Command
from typing import Literal, Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, HumanMessage, filter_messages
from langgraph.graph import StateGraph,  add_messages, START, END
from prompts import lead_researcher_with_multiple_steps_diffusion_double_check_prompt
from utils import get_today_str
from models import init_model
from tools import think_tool, ConductResearch, ResearchComplete, refine_draft_report
from research_agent import researcher_agent
from langgraph.checkpoint.memory import InMemorySaver

model = init_model(temperature=0.7, model_name="SF_Qwen3-8B")
# 定义管理者状态
class SupervisorState(TypedDict):
    """
    State for the multi-agent research supervisor.
    Manages coordination between supervisor and research agents, tracking
    research progress and accumulating findings from multiple sub-agents.
    """
    # Messages exchanged with supervisor for coordination and decision-making
    supervisor_messages: Annotated[Sequence[BaseMessage], add_messages]
    # Detailed research brief that guides the overall research direction
    research_brief: str
    # Processed and structured notes ready for final report generation
    notes: Annotated[list[str], operator.add] = []
    # Counter tracking the number of research iterations performed
    research_iterations: int = 0
    # Raw unprocessed research notes collected from sub-agent research
    raw_notes: Annotated[list[str], operator.add] = []
    # Draft report
    draft_report: str

# 定义最大并发研究代理数量
max_concurrent_researchers = 3
# 定义最大研究迭代次数
max_researcher_iterations = 8
supervisor_tools = [ConductResearch, ResearchComplete, think_tool, refine_draft_report]
supervisor_model = model
supervisor_model_with_tools = supervisor_model.bind_tools(supervisor_tools)

# 定义管理者节点
async def supervisor(state: SupervisorState) -> Command[Literal["supervisor_tools"]]:
    """Coordinate research activities.

    Analyzes the research brief and current progress to decide:
    - What research topics need investigation
    - Whether to conduct parallel research
    - When research is complete

    Args:
        state: Current supervisor state with messages and research progress

    Returns:
        Command to proceed to supervisor_tools node with updated state
    """
    supervisor_messages = state.get("supervisor_messages", [])

    # Prepare system message with current date and constraints

    system_message = lead_researcher_with_multiple_steps_diffusion_double_check_prompt.format(
        date=get_today_str(), 
        max_concurrent_research_units=max_concurrent_researchers,
        max_researcher_iterations=max_researcher_iterations
    )
    messages = [SystemMessage(content=system_message)] + supervisor_messages

    # Make decision about next research steps
    response = await supervisor_model_with_tools.ainvoke(messages)

    return Command(
        goto="supervisor_tools",
        update={
            "supervisor_messages": [response],
            "research_iterations": state.get("research_iterations", 0) + 1
        }
    )

def get_notes_from_tool_calls(messages: list[BaseMessage]) -> list[str]:
    """Extract research notes from ToolMessage objects in supervisor message history.

    This function retrieves the compressed research findings that sub-agents
    return as ToolMessage content. When the supervisor delegates research to
    sub-agents via ConductResearch tool calls, each sub-agent returns its
    compressed findings as the content of a ToolMessage. This function
    extracts all such ToolMessage content to compile the final research notes.

    Args:
        messages: List of messages from supervisor's conversation history

    Returns:
        List of research note strings extracted from ToolMessage objects
    """
    return [tool_msg.content for tool_msg in filter_messages(messages, include_types="tool")]

# 定义执行者节点
async def supervisor_tools(state: SupervisorState) -> Command[Literal["supervisor", "__end__"]]:
    """Execute supervisor decisions - either conduct research or end the process.

    Handles:
    - Executing think_tool calls for strategic reflection
    - Launching parallel research agents for different topics
    - Aggregating research results
    - Determining when research is complete

    Args:
        state: Current supervisor state with messages and iteration count

    Returns:
        Command to continue supervision, end process, or handle errors
    """
    supervisor_messages = state.get("supervisor_messages", [])
    research_iterations = state.get("research_iterations", 0)
    most_recent_message = supervisor_messages[-1]

    # Initialize variables for single return pattern
    tool_messages = []
    all_raw_notes = []
    draft_report = ""
    next_step = "supervisor"  # Default next step
    should_end = False

    # Check exit criteria first
    exceeded_iterations = research_iterations >= max_researcher_iterations
    no_tool_calls = not most_recent_message.tool_calls
    research_complete = any(
        tool_call["name"] == "ResearchComplete" 
        for tool_call in most_recent_message.tool_calls
    )

    if exceeded_iterations or no_tool_calls or research_complete:
        should_end = True
        next_step = END
    else:
        # Execute ALL tool calls before deciding next step
        try:
            # Separate think_tool calls from ConductResearch calls
            think_tool_calls = [
                tool_call for tool_call in most_recent_message.tool_calls 
                if tool_call["name"] == "think_tool"
            ]

            conduct_research_calls = [
                tool_call for tool_call in most_recent_message.tool_calls 
                if tool_call["name"] == "ConductResearch"
            ]

            refine_report_calls = [
                tool_call for tool_call in most_recent_message.tool_calls 
                if tool_call["name"] == "refine_draft_report"
            ]

            # Handle think_tool calls (synchronous)
            for tool_call in think_tool_calls:
                observation = think_tool.invoke(tool_call["args"])
                tool_messages.append(
                    ToolMessage(
                        content=observation,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    )
                )

            # Handle ConductResearch calls (asynchronous)
            if conduct_research_calls:
                # Launch parallel research agents
                coros = [
                    researcher_agent.ainvoke({
                        "researcher_messages": [
                            HumanMessage(content=tool_call["args"]["research_topic"])
                        ],
                        "research_topic": tool_call["args"]["research_topic"]
                    }) 
                    for tool_call in conduct_research_calls
                ]

                # Wait for all research to complete
                tool_results = await asyncio.gather(*coros)

                # Format research results as tool messages
                # Each sub-agent returns compressed research findings in result["compressed_research"]
                # We write this compressed research as the content of a ToolMessage, which allows
                # the supervisor to later retrieve these findings via get_notes_from_tool_calls()
                research_tool_messages = [
                    ToolMessage(
                        content=result.get("compressed_research", "Error synthesizing research report"),
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    ) for result, tool_call in zip(tool_results, conduct_research_calls)
                ]

                tool_messages.extend(research_tool_messages)

                # Aggregate raw notes from all research
                all_raw_notes = [
                    "\n".join(result.get("raw_notes", [])) 
                    for result in tool_results
                ]

            for tool_call in refine_report_calls: 
              notes = get_notes_from_tool_calls(supervisor_messages)    
              findings = "\n".join(notes)

              draft_report = refine_draft_report.invoke({
                    "research_brief": state.get("research_brief", ""),
                    "findings": findings,
                    "draft_report": state.get("draft_report", "")
              })

              tool_messages.append(
                ToolMessage(
                    content=draft_report,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"]
                )
              )

        except Exception as e:
            should_end = True
            next_step = END

    # Single return point with appropriate state updates
    if should_end:
        return Command(
            goto=next_step,
            update={
                "notes": get_notes_from_tool_calls(supervisor_messages),
                "research_brief": state.get("research_brief", "")
            }
        )
    elif len(refine_report_calls) > 0:
        return Command(
            goto=next_step,
            update={
                "supervisor_messages": tool_messages,
                "raw_notes": all_raw_notes,
                "draft_report": draft_report
            }
        )        
    else:
        return Command(
            goto=next_step,
            update={
                "supervisor_messages": tool_messages,
                "raw_notes": all_raw_notes
            }
        )

# Build supervisor graph
supervisor_builder = StateGraph(SupervisorState)
supervisor_builder.add_node("supervisor", supervisor)
supervisor_builder.add_node("supervisor_tools", supervisor_tools)
supervisor_builder.add_edge(START, "supervisor")
#supervisor_builder.add_edge("supervisor_tools", END)
supervisor_agent = supervisor_builder.compile(checkpointer=InMemorySaver())


async def run():
    query = "全球量子计算的最新进展"
    thread = {"configurable": {"thread_id": "1", "recursion_limit": 50}}
    result = await supervisor_agent.ainvoke({"supervisor_messages": [HumanMessage(content=query)]}, config=thread)
    print(result)

async def stream_run():
    query = "全球量子计算的最新进展"
    thread = {"configurable": {"thread_id": "1", "recursion_limit": 50}}
    async for event in supervisor_agent.astream_events({"supervisor_messages": [HumanMessage(content=query)]}, config=thread):
        print(event)



if __name__ == "__main__":

    # Draw the graph and save it to a file
    #supervisor_agent.get_graph(xray=True).draw_mermaid_png(output_file_path="supervisor_agent.png")

    asyncio.run(stream_run())

