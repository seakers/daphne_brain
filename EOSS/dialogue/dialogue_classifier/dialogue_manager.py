from typing import Annotated, Dict, List, TypedDict, Union
from langgraph.graph import END, StateGraph
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from EOSS.dialogue.dialogue_classifier.intent_classifier import classify_and_extract, IntentType
import os
from EOSS.dialogue.dialogue_classifier.engineer_router import EngineerRouter
from EOSS.dialogue.dialogue_classifier.critic_agent import CriticAgent
from EOSS.dialogue.dialogue_classifier.historian_agent import HistorianAgent
from EOSS.dialogue.dialogue_classifier.analyst_agent import AnalystAgent
import sys
import django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "daphne_brain.settings")
django.setup()


# Define the state for our graph
class AgentState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage]]
    intent: str
    sub_intent: str
    response: str
    session_key: str
    designs: List[Dict]
    context: Dict
    parameters: Dict
    problem: str
    selected_designs: List[Dict]
    user_selected_ids: List[str]
    plot_data: List[Dict]

# Node functions for the graph
def classify_user_intent(state: AgentState) -> AgentState:
    """Classify the user's intent from their query."""
    user_message = state["messages"][-1].content
    llm = ChatOllama(
        model="deepseek-r1",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    # model = OllamaLLM(model_name="llama3")
    intent, parameters = classify_and_extract(user_message)
    print("type of Parameters:", type(parameters))
    return {"intent": intent,
            "parameters": parameters
        }

def analyze_query(state: AgentState) -> Dict:
    """Route to the appropriate agent based on intent."""
    intent = state["intent"]
    if intent == IntentType.ANALYST:
        return {"next": "analyst_agent"}
    elif intent == IntentType.ENGINEER:
        return {"next": "engineer_agent"}
    elif intent == IntentType.CRITIC:
        return {"next": "critic_agent"}
    elif intent == IntentType.HISTORIAN:
        return {"next": "historian_agent"}
    else:
        return {"next": "default_response"}

def analyst_agent(state: AgentState) -> AgentState:
    """Handle queries related to data analysis."""
    user_query = state["messages"][-1].content
    
    analyst = AnalystAgent()
    response, selected_designs = analyst.process_query(
        user_query,
        state["parameters"],
        state["designs"],
        state["context"],
        state["session_key"],
        state["problem"],
        state["user_selected_ids"],
        state["plot_data"]
    )
    return {"response": response, "selected_designs": selected_designs}

def engineer_agent(state: AgentState) -> AgentState:
    """Handle queries related to engineering."""
    user_query = state["messages"][-1].content    
    # engineer = EngineerAgent()
    # state["engineer_router"] = EngineerRouter()
    engineerRouter = EngineerRouter()
    response = engineerRouter.process_query(
        user_query, 
        state["problem"],
        state["parameters"], 
        state["designs"],
        state["context"]
    )
    
    return {"response": response}

def critic_agent(state: AgentState) -> AgentState:
    """Handle queries related to criticism/evaluation."""
    user_query = state["messages"][-1].content    
    critic = CriticAgent()
    response = critic.process_query(
        user_query, 
        state["parameters"], 
        state["designs"],
        state["context"],
        state["session_key"]
    )
    return {"response": response}

def historian_agent(state: AgentState) -> AgentState:
    """Handle queries related to historical data."""
    # This would be implemented with specific functions for historian queries
    user_query = state["messages"][-1].content
    
    historian = HistorianAgent()
    response = historian.process_query(
        user_query,
        state["parameters"],
        state["designs"],
        state["context"]
    )
    
    return {"response": response}

def default_response(state: AgentState) -> AgentState:
    """Provide a response when the intent cannot be classified."""
    return {"response": "I'm not sure how to help with that specific query."}

def format_response(state: AgentState) -> AgentState:
    """Format the final response to the user."""
    messages = state["messages"]
    response = state["response"]
    messages.append(AIMessage(content=response))
    return {"messages": messages}

def main(processed_command, user_info, context, data, new_dialogue_contexts, session, user_selected_ids, plot_data):
    # Build the graph
    workflow = StateGraph(AgentState)
    print("--------------------------------")
    print("full data:", data)
    print("full context:", context)
    print("--------------------------------")
    # designs = data['designs']
    # print("designs type:", type(designs))
    
    # # Option 1: Print first few objects in the QuerySet
    # print("First few designs:")
    # for i, design in enumerate(designs[:3]):  # Print first 3 designs
    #     print(f"Design {i}:", design)
        
    # # Option 2: Get all field values for first design (if any exist)
    # if designs.exists():
    #     first_design = designs.first()
    #     print("First design fields:")
    #     for field in first_design._meta.fields:
    #         print(f"{field.name}: {getattr(first_design, field.name)}")
    
    # # Option 3: Convert QuerySet to list of dictionaries
    # designs_list = list(designs.values())
    # print(f"Total designs: {len(designs_list)}")
    # if designs_list:
    #     print("First design as dict:", designs_list[0])
    
    
    # Add nodes
    workflow.add_node("classify_intent", classify_user_intent)
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("analyst_agent", analyst_agent)
    workflow.add_node("engineer_agent", engineer_agent)
    workflow.add_node("critic_agent", critic_agent)
    workflow.add_node("historian_agent", historian_agent)
    workflow.add_node("default_response", default_response)
    workflow.add_node("format_response", format_response)
    
    # Add edges
    workflow.add_edge("classify_intent", "analyze_query")
    workflow.add_conditional_edges(
        "analyze_query",
        lambda x: x["next"],
        {
            "analyst_agent": "analyst_agent",
            "engineer_agent": "engineer_agent",
            "critic_agent": "critic_agent",
            "historian_agent": "historian_agent",
            "default_response": "default_response"
        }
    )
    workflow.add_edge("analyst_agent", "format_response")
    workflow.add_edge("engineer_agent", "format_response")
    workflow.add_edge("critic_agent", "format_response")
    workflow.add_edge("historian_agent", "format_response")
    workflow.add_edge("default_response", "format_response")
    workflow.add_edge("format_response", END)
    
    # Set the entry point
    workflow.set_entry_point("classify_intent")
    
    # Compile the graph
    app = workflow.compile()
    
    # Run the application
    designs = data['designs']
    session_key = session.session_key


    result = app.invoke({
        "messages": [HumanMessage(content=processed_command)],
        "intent": "",
        "sub_intent": "",
        "response": "",
        "session_key": session_key,
        "designs": designs,
        "context": context,
        "problem": data["problem"],
        "parameters": {},
        "selected_designs": [],
        "user_selected_ids": user_selected_ids,
        "plot_data": plot_data,
    })

    print(result["messages"][-1].content)
    response = result["messages"][-1].content
    answer = {}
    answer["voice_answer"] = response
    answer["visual_answer_type"] = ["text"]
    answer["visual_answer"] = [response]
    return answer, result["selected_designs"]
    

def main1(processed_command, user_info, context, data, new_dialogue_contexts, session):
    # query = "Why does 115 not satisfy WAT3-1"
    query = processed_command

    intent, parameters = classify_and_extract(query)
    print("Intent:", intent)
    print("Parameters:", parameters)

    engineer_agent = EngineerAgent()
    response = engineer_agent.process_query(query, parameters, data['designs'], context)
    print("response:", response)
    answer = {}
    answer["voice_answer"] = response
    answer["visual_answer_type"] = ["text"]
    answer["visual_answer"] = response
    return answer

if __name__ == "__main__":
    main()