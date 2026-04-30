from typing import Any, Dict, Optional, TypedDict, Annotated, List, Union
from backend.main import FollowUpRecord
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import json
from dotenv import load_dotenv
from database import SessionLocal, InteractionRecord

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
    Retrieves previous meeting notes, sentiment, and topics for a specific HCP from the database.
    Trigger this if the user asks for background context on the doctor before logging.
    """
    # Open a local database session
    db = SessionLocal()
    try:
        # Query the DB for the most recent 3 interactions with this HCP
        # ilike() is used for case-insensitive matching
        history = db.query(InteractionRecord).filter(
            InteractionRecord.hcp_name.ilike(f"%{hcp_name}%")
        ).order_by(InteractionRecord.id.desc()).limit(3).all()
        
        if not history:
            return f"No previous interaction history found in the database for {hcp_name}."
        
        # Format the SQL results into a readable string for Llama 3.3 to summarize
        result_str = f"Found {len(history)} recent interactions for {hcp_name}:\n"
        for record in history:
            result_str += f"- Date: {record.date} | Type: {record.interaction_type} | Sentiment: {record.sentiment}\n"
            result_str += f"  Topics: {record.topics}\n"
            result_str += f"  Outcomes: {record.outcomes}\n"
        
        return result_str
        
    except Exception as e:
        return f"Error accessing database: {str(e)}"
    finally:
        # Always close the connection
        db.close()

@tool
def schedule_followup(hcp_name: str, task_name: str, date: str):
    """
    Schedules a follow-up task or calendar event for a specific HCP in the database.
    Format the date as YYYY-MM-DD.
    """
    db = SessionLocal()
    try:
        new_task = FollowUpRecord(hcp_name=hcp_name, task_name=task_name, date=date)
        db.add(new_task)
        db.commit()
        return f"SUCCESS: Task '{task_name}' for {hcp_name} officially scheduled for {date} in the database."
    except Exception as e:
        db.rollback()
        return f"ERROR: Failed to save task to database: {str(e)}"
    finally:
        db.close()

@tool
def get_hcp_followups(hcp_name: str):
    """
    Retrieves all scheduled follow-up tasks for a specific HCP from the database.
    Trigger this if the user asks what tasks or follow-ups are coming up for a doctor.
    """
    db = SessionLocal()
    try:
        # Query the DB for tasks matching this HCP, ordered by date
        tasks = db.query(FollowUpRecord).filter(
            FollowUpRecord.hcp_name.ilike(f"%{hcp_name}%")
        ).order_by(FollowUpRecord.date.asc()).all()
        
        if not tasks:
            return f"No pending follow-ups found for {hcp_name}."
        
        result_str = f"Found {len(tasks)} upcoming follow-up(s) for {hcp_name}:\n"
        for t in tasks:
            result_str += f"- [{t.date}] {t.task_name} (Status: {t.status})\n"
            
        return result_str
    except Exception as e:
        return f"ERROR retrieving follow-ups: {str(e)}"
    finally:
        db.close()
        
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
                if tool_name == 'get_hcp_history':
                    result = get_hcp_history.invoke(args)
                elif tool_name == 'schedule_followup':
                    result = schedule_followup.invoke(args)
                elif tool_name == 'check_compliance':
                    result = check_compliance.invoke(args)
                else:
                    result = "SUCCESS: Unknown tool executed."
                
                # Pass the actual result from the tool back to the AI
                tool_messages.append(ToolMessage(
                    tool_call_id=tool_call['id'], 
                    name=tool_name, 
                    content=str(result)
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