import base64
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from app.state import KYCState

import re
from datetime import datetime

# ---------------------------------------------------------
# 1. THE DATA SCHEMA (The Bouncer)
# ---------------------------------------------------------
class IDExtractionSchema(BaseModel):
    extracted_name: str = Field(
        description="The full legal name. Regardless of the format on the ID (e.g., 'Last, First Middle'), you MUST standardize the output to 'First Middle Last' format. Remove any commas."
    )
    extracted_dob: str = Field(
        description="The date of birth on the ID. Regardless of how it is written on the card (e.g., 'August 19, 2003'), you MUST convert it to 'YYYY-MM-DD' format."
    )
    extracted_id_number: str = Field(
        description="The unique alphanumeric identification number on the document."
    )
    is_expired: bool = Field(
        description="Evaluate the expiration date. Return True if the card is expired as of today, False if valid."
    )

# ---------------------------------------------------------
# 2. HELPER FUNCTION
# ---------------------------------------------------------
def encode_image(image_path: str) -> str:
    """Encodes an image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def standardize_date(date_str: str):
    """Translates messy date strings into comparable Date objects."""
    if not date_str:
        return None

    # (YYYY-MM-DD, MM/DD/YYYY, August 19, 2003, Aug 19 2003, etc.)
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%d/%m/%Y", "%d-%m-%Y"]
    
    clean_date = date_str.strip()
    
    for fmt in formats:
        try:
            return datetime.strptime(clean_date, fmt).date()
        except ValueError:
            continue 
            
    return None 
    
# ---------------------------------------------------------
# 3. THE EXTRACTOR NODE (The Worker)
# ---------------------------------------------------------
def extractor_node(state: KYCState) -> dict:
    """
    Reads the ID image using Llama 3.2 Vision and extracts structured data.
    """
    print("--- RUNNING EXTRACTOR NODE ---")
    
    image_path = state.get("image_path")
    attempts = state.get("extraction_attempts", 0)
    current_errors = state.get("errors", [])

    # Attempt to load and encode the image
    try:
        base64_image = encode_image(image_path)
    except Exception as e:
        return {"errors": current_errors + [f"System error: Could not load image file at {image_path}"]}

    # Initialize the local Llama Vision model
    # Temperature 0 ensures factual extraction without creative hallucination
    llm = ChatOllama(
        model="llama3.2-vision",
        temperature=0
    )

    # Bind our Pydantic schema to force the LLM to output strict JSON
    structured_llm = llm.with_structured_output(IDExtractionSchema)

    # Construct the multimodal prompt
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": "You are a strict compliance officer. Analyze this ID document and extract the required fields exactly as specified in the schema. Do not include any conversational text."
                },
                {
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        }
    ]

    # Execute the extraction
    try:
        result = structured_llm.invoke(messages)
        
        # LangGraph updates the state by merging this returned dictionary
        return {
            "extracted_name": result.extracted_name,
            "extracted_dob": result.extracted_dob,
            "extracted_id_number": result.extracted_id_number,
            "extraction_attempts": attempts + 1,
            # We append a temporary flag here so the Validator Node knows if it expired
            "errors": current_errors + ["ID is expired."] if result.is_expired else current_errors
        }
        
    except Exception as e:
        # If the LLM fails to parse the schema or read the image, we catch it gracefully
        return {
            "errors": current_errors + [f"Extraction failed: {str(e)}"],
            "extraction_attempts": attempts + 1
        }

# ---------------------------------------------------------
# 4. THE VALIDATOR NODE
# ---------------------------------------------------------
def validator_node(state: KYCState) -> dict:
    """
    Checks the extracted data against business rules and user inputs using order-agnostic matching.
    """
    print("--- RUNNING VALIDATOR NODE ---")
    
    extracted_name = state.get("extracted_name", "")
    user_name = state.get("user_provided_name", "")
    extracted_dob_raw = state.get("extracted_dob", "")
    user_dob_raw = state.get("user_provided_dob", "")
    
    current_errors = state.get("errors", [])
    new_errors = []
    
    # 1. Missing Data Check
    if not extracted_name or not extracted_dob_raw or not state.get("extracted_id_number"):
        new_errors.append("Missing required fields from the ID.")
        
    # 2. Advanced Name Match Check (Order-Agnostic)
    if extracted_name and user_name:
        user_words = set(re.sub(r'[^a-z\s]', '', user_name.lower()).split())
        extracted_words = set(re.sub(r'[^a-z\s]', '', extracted_name.lower()).split())
        if user_words != extracted_words:
            new_errors.append(f"Name mismatch: User entered '{user_name}' but ID says '{extracted_name}'.")


    if extracted_dob_raw and user_dob_raw:
        user_dob_obj = standardize_date(user_dob_raw)
        extracted_dob_obj = standardize_date(extracted_dob_raw)
        
        if not user_dob_obj or not extracted_dob_obj:
            new_errors.append("System error: Could not parse one of the dates into a standard format.")
        elif user_dob_obj != extracted_dob_obj:
            new_errors.append(f"DOB mismatch: User entered '{user_dob_raw}' but ID says '{extracted_dob_raw}'.")
            
    return {"errors": current_errors + new_errors}

# ---------------------------------------------------------
# 5. THE DATABASE MOCK NODE
# ---------------------------------------------------------
def database_check_node(state: KYCState) -> dict:
    """
    Mocks a government Ayuda or Fintech compliance database check.
    """
    print("--- RUNNING DATABASE CHECK ---")
    id_number = state.get("extracted_id_number")
    
    # Mock blacklisted IDs for fraud testing
    blacklisted_ids = ["123456789", "999999999", "000000000"]
    
    if id_number in blacklisted_ids:
        return {"final_status": "REJECTED_BLACKLISTED"}
        
    return {"final_status": "APPROVED"}
