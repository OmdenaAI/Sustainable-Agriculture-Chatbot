from typing import List, Optional
from pydantic import BaseModel, Field

class Chunk(BaseModel):
    """ChunkDocument model"""
    id: str = Field(..., description="The unique identifier of the chunk")
    text: str = Field(..., description="The text content of the chunk")
    # embedding: List[float] = Field(..., description="The embedding vector of the chunk")
    metadata: dict = Field(..., description="Metadata associated with the chunk")


