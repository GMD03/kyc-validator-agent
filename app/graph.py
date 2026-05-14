from langgraph.graph import StateGraph, END
from app.state import KYCState
from app.nodes import extractor_node, validator_node, database_check_node

def route_after_validation(state: KYCState) -> str:
    """
    The brain of the graph. Decides where to send the data next based on the Validator's findings.
    """
    errors = state.get("errors", [])
    attempts = state.get("extraction_attempts", 0)
    
    # Condition 1: Self-Correction Loop
    # If the LLM failed to read the image properly, give it another try (up to 3 times)
    if "Extraction failed" in str(errors) and attempts < 3:
        print("-> ROUTER: Extraction failed, looping back to Extractor Node.")
        return "retry_extraction"
        
    # Condition 2: Human-in-the-Loop / Rejection
    # If there are expiry issues or name mismatches, stop the workflow
    if errors:
        print(f"-> ROUTER: Errors found {errors}. Routing to Manual Review/END.")
        return "manual_review"
        
    # Condition 3: Clean Data
    # If no errors, proceed to the database check
    print("-> ROUTER: Data clean. Proceeding to Database Check.")
    return "check_database"

# 1. Initialize the Graph with our State Schema
workflow = StateGraph(KYCState)

# 2. Add the Worker Stations (Nodes)
workflow.add_node("extractor_node", extractor_node)
workflow.add_node("validator_node", validator_node)
workflow.add_node("database_check_node", database_check_node)

# 3. Set the Entry Point
workflow.set_entry_point("extractor_node")

# 4. Draw the Edges (The Conveyor Belt)
# Extractor always goes to Validator
workflow.add_edge("extractor_node", "validator_node")

# Validator goes to the Conditional Router
workflow.add_conditional_edges(
    "validator_node",
    route_after_validation,
    {
        "retry_extraction": "extractor_node",       # The cyclic loop
        "manual_review": END,                       # Stops graph so a human can step in
        "check_database": "database_check_node"     # Moves forward
    }
)

# Database check always ends the workflow
workflow.add_edge("database_check_node", END)

# 5. Compile the Digital Worker
kyc_agent = workflow.compile()