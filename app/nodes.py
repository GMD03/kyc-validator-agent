from pydantic import BaseModel, Field
from typing import Optional

# This is the strict schema we will force the LLM to output
class IDExtractionSchema(BaseModel):
    extracted_name: str = Field(
        description="The full legal name exactly as it appears on the ID document. Format as First Last."
    )
    extracted_dob: str = Field(
        description="The date of birth found on the ID. MUST be in YYYY-MM-DD format."
    )
    extracted_id_number: str = Field(
        description="The unique alphanumeric identification number on the document."
    )
    is_expired: bool = Field(
        description="Evaluate the expiration date on the card. Return True if the card is expired as of today, False if it is still valid."
    )