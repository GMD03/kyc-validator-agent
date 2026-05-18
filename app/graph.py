from langgraph.graph import StateGraph, END
from app.state import KYCState
from app.nodes import extractor_node, validator_node, database_check_node

def route_after_validation(state: KYCState) -> str:
    """
    The brain of the graph. Decides where to send the data next based on the Validator's findings.
    """
    errors = state.get("errors", [])
    attempts = state.get("extraction_attempts", 0)
    
    # Self-Correction Loop
    if "Extraction failed" in str(errors) and attempts < 3:
        print("-> ROUTER: Extraction failed, looping back to Extractor Node.")
        return "retry_extraction"
        
    # Human-in-the-Loop / Rejection
    if errors:
        print(f"-> ROUTER: Errors found {errors}. Routing to Manual Review/END.")
        return "manual_review"
        
    # Clean Data
    print("-> ROUTER: Data clean. Proceeding to Database Check.")
    return "check_database"

# Initialize graph with State Schema
workflow = StateGraph(KYCState)

workflow.add_node("extractor_node", extractor_node)
workflow.add_node("validator_node", validator_node)
workflow.add_node("database_check_node", database_check_node)

workflow.set_entry_point("extractor_node")

workflow.add_edge("extractor_node", "validator_node")

workflow.add_conditional_edges(
    "validator_node",
    route_after_validation,
    {
        "retry_extraction": "extractor_node",       # The cyclic loop
        "manual_review": END,                       # Stops graph so a human can step in
        "check_database": "database_check_node"     # Moves forward
    }
)

workflow.add_edge("database_check_node", END)

kyc_agent = workflow.compile()