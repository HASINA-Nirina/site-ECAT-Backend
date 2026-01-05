from pydantic import BaseModel
from typing import List

class InscriptionsByAntenneResponse(BaseModel):
    labels: List[str]
    data: List[int]
    
    class Config:
        from_attributes = True

