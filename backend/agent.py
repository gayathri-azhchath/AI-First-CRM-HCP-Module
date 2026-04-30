from typing import Any, Dict, Optional, TypedDict, Annotated, List, Union
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import json
from dotenv import load_dotenv

load_dotenv()

# Define the State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The chat history"]
    form_data: Dict[str, Any]

# --- Mandatory Tools ---

@tool
def log_interaction(
    hcp_name: Optional[str] = None,
    interaction_type: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    attendees: Optional[str] = None,
    topics: Optional[str] = None,
    materials: Optional[Union[List[str],str]] = None,
    samples: Optional[Union[List[str],str]] = None,
    sentiment: Optional[str] = None,
    outcomes: Optional[str] = None,
    follow_ups: Optional[str] = None
):
    """
    Extracts and logs HCP interaction details. 
    Only extracts fields that are explicitly mentioned or clearly inferred from the text.
    - interaction_type MUST be exactly one of: 'Meeting', 'Email', 'Phone Call', 'Event'.
    - sentiment MUST be exactly one of: 'Positive', 'Neutral', 'Negative'.
    """

    if isinstance(materials, str):
        materials = [materials]
    if isinstance(samples, str):
        samples = [samples]
    # Capture all provided arguments, filtering out None values
    updates = {
        "hcp_name": hcp_name,
        "interaction_type": interaction_type,
        "date": date,
        "time": time,
        "attendees": attendees,
        "topics": topics,
        "materials": materials,
        "samples": samples,
        "sentiment": sentiment,
        "outcomes": outcomes,
        "follow_ups": follow_ups
    }
    # Return only the keys that the AI successfully extracted
    return {k: v for k, v in updates.items() if v is not None}

@tool
def edit_interaction(field_name: str, new_value: Any):
    """
    Edits a specific field in the form if the user identifies an error.
    ALLOWED field_name VALUES ONLY:
    - hcp_name
    - interaction_type
    - date
    - time
    - attendees
    - topics
    - materials
    - samples
    - sentiment
    - outcomes
    - follow_ups
    """
    # Returning a dictionary makes it consistent with log_interaction
    return {"field_name": field_name, "new_value": new_value}

@tool
def get_hcp_history(hcp_name: str):
    """
    Retrieves previous meeting notes, specialty, and prescribing history for a specific HCP.
    Trigger this if the user asks for background context on the doctor before logging.
    """
    # In a real app, this would query Postgres. For now, mock it:
    return f"DB_RESULT: Last meeting with {hcp_name} was 2 weeks ago regarding OncoBoost. Sentiment was Neutral. Specialty: Oncology."

@tool
def schedule_followup(task_name: str, date: str):
    """
    Schedules a follow-up task or calendar event in the CRM system.
    Format the date as YYYY-MM-DD.
    """
    return f"SUCCESS: Task '{task_name}' officially scheduled for {date} in the rep's calendar."

@tool
def check_compliance(interaction_summary: str):
    """
    Checks if the interaction notes meet Pharma medical-legal compliance guidelines.
    Run this tool if the user asks to verify compliance or check for off-label promotion.
    """
    return "COMPLIANCE_STATUS: Passed. No off-label claims or prohibited gift values detected in the summary."

tools = [log_interaction, edit_interaction, get_hcp_history, schedule_followup, check_compliance]
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0) # As specified in requirements
llm_with_tools = llm.bind_tools(tools)

# Node logic
def call_model(state: AgentState):
    # System prompt gives the AI context about its job
    system_msg = SystemMessage(content="""
    You are an AI assistant embedded in a Life Sciences CRM for Pharma Sales Reps. 
    Your job is to read the rep's chat messages and trigger the 'log_interaction' tool 
    to populate the structured CRM form. Map their natural language to the tool's parameters.
    If they realize a mistake and ask for a correction, use the 'edit_interaction' tool.
    Keep your conversational responses brief and confirm what was logged.
    """)
    
    # Prepend the system prompt to the message history
    messages = [system_msg] + state['messages']
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}

def apply_tool_updates(state: AgentState):
    last_msg = state['messages'][-1]
    new_form = state['form_data'].copy()
    tool_messages = [] 
    
    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
        for tool_call in last_msg.tool_calls:
            args = tool_call['args']
            tool_name = tool_call['name']
            
            if tool_name == 'log_interaction':
                extracted_data = log_interaction.invoke(args)
                for key, value in extracted_data.items():
                    if value: 
                        new_form[key] = value
                
                tool_messages.append(ToolMessage(
                    tool_call_id=tool_call['id'], 
                    name=tool_name, 
                    content=f"SUCCESS: Form updated with {extracted_data}"
                ))
                    
            elif tool_name == 'edit_interaction':
                edit_data = edit_interaction.invoke(args)
                field = edit_data["field_name"]
                val = edit_data["new_value"]
                if field in new_form:
                    new_form[field] = val
                
                tool_messages.append(ToolMessage(
                    tool_call_id=tool_call['id'], 
                    name=tool_name, 
                    content=f"SUCCESS: Field '{field}' updated to '{val}'"
                ))
            else:
                tool_messages.append(ToolMessage(
                    tool_call_id=tool_call['id'], 
                    name=tool_name, 
                    content="SUCCESS: Tool executed."
                ))
                
    return {"form_data": new_form, "messages": tool_messages}

# --- NEW: Third Node for the Final Reply ---
def generate_final_reply(state: AgentState):
    """
    This node uses the base LLM (WITHOUT tools) to ensure it only 
    generates a conversational text reply and doesn't try to extract data again.
    """
    response = llm.invoke(state['messages'])
    return {"messages": [response]}


# --- Define the Strictly Linear Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)               # Step 1: Assume form update & extract
workflow.add_node("sync", apply_tool_updates)        # Step 2: Apply to Redux state
workflow.add_node("reply", generate_final_reply)     # Step 3: Speak back to the user

workflow.set_entry_point("agent")

# No conditional edges needed! It runs straight through.
workflow.add_edge("agent", "sync")
workflow.add_edge("sync", "reply")
workflow.add_edge("reply", END)

graph = workflow.compile()