
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSQLiteSaver
from app.state import AgentState

llm = ChatAnthropic(model="claude-sonnet-4-5")
tools = [TavilySearchResults(max_results=2)]
llm_with_tools = llm.bind_tools(tools)

# Node 1: Safety screener
def safety_screener(state: AgentState):
    last_msg = state["messages"][-1].content.lower() # Get the content of the last message and convert it to lowercase
    flagged_terms = ["violence", "self-harm", "hate speech", "harm", "weapon", "exploit", "bypass"] # Example flagged terms
    flagged = any(term in last_msg for term in flagged_terms) # Check if any flagged term is in the last message
    state["safety_flagged"] = flagged # Update the state with the safety flag
    return state

# Node 2: Agent (LLM + tools)
def agent_node(state: AgentState):
    if state.get("safety_flagged"):
        return {"messages": [("assistant", "I can't help with that request.")] } # If flagged, go to safety response node
    # Otherwise, process with LLM and tools
    response = llm_with_tools.invoke(state["messages"]) # Get response from LLM with tools
    return {"messages": [response]} # Return the response as messages

# Node 3: Tool executor (prebuilt ToolNode)
tool_node = ToolNode(tools)

# Routing
def should_use_tools(state: AgentState):
    last = state["messages"][-1] # Get the last message
    if hasattr(last, "tool_calls") and last.tool_calls: # Check if there are any tool calls in the last message
        return "tools" # If there are tool calls, route to the tool node
    return END # Otherwise, end the graph execution


def build_graph(checkpointer: AsyncSQLiteSaver):
    g = StateGraph(AgentState) # Create a new graph with the AgentState type
    g.add_node("safety_screener", safety_screener) # Add safety screener node
    g.add_node("agent", agent_node) # Add agent node
    g.add_node("tools", tool_node) # Add tool node

    g.set_entry_point("safety_screener") # Set the entry point to the safety screener
    g.add_edge("safety_screener", "agent") # If safety screener passes, go to agent
    g.add_conditional_edges("agent", should_use_tools, {"tools": "tools", END: END}) # From agent, conditionally go to tools or end
    g.add_edge("tools", "agent") # Loop back to agent after using tools, allowing for multiple tool uses

    return g.compile(checkpointer=checkpointer) # Compile the graph with a checkpointer for state persistence
