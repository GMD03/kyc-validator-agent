from typing import TypedDict, Optional, List

class KYCState(TypedDict):
    # Inputs (What the user provides)
    image_path: str
    user_provided_name: str
    user_provided_dob: str
    
    # Extracted Data (What the AI pulls from the ID)
    extracted_name: Optional[str]
    extracted_dob: Optional[str]
    extracted_id_number: Optional[str]
    
    # System Logic & Status
    extraction_attempts: int
    errors: List[str]
    final_status: Optional[str] # Will update to: PENDING, APPROVED, REJECTED, or MANUAL_REVIEW