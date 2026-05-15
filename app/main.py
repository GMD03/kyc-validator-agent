from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.graph import kyc_agent

app = FastAPI(
    title="Automated KYC Agent API",
    description="Backend API for local Llama-powered ID verification and validation.",
    version="1.0.0"
)

class KYCRequest(BaseModel):
    image_path: str
    user_provided_name: str
    user_provided_dob: str

class KYCResponse(BaseModel):
    extraction_attempts: int
    final_status: str
    errors: list[str]
    extracted_data: dict

@app.post("/validate", response_model=KYCResponse)
async def validate_kyc_endpoint(request: KYCRequest):
    """
    Triggers the LangGraph KYC workflow for a given ID image and user data.
    """
    try:
        # Initial state to feed into the graph
        initial_state = {
            "image_path": request.image_path,
            "user_provided_name": request.user_provided_name,
            "user_provided_dob": request.user_provided_dob,
            "extraction_attempts": 0,
            "errors": []
        }

        # .invoke() runs the entire graph from start to finish (END)
        final_state = kyc_agent.invoke(initial_state)

        # Structure the response
        return {
            "extraction_attempts": final_state.get("extraction_attempts", 0),
            "final_status": final_state.get("final_status", "UNKNOWN"),
            "errors": final_state.get("errors", []),
            "extracted_data": {
                "name": final_state.get("extracted_name"),
                "dob": final_state.get("extracted_dob"),
                "id_number": final_state.get("extracted_id_number")
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Execution Error: {str(e)}")

# 5. Root endpoint for health checks
@app.get("/")
def read_root():
    return {"message": "KYC Validator Agent is Online"}