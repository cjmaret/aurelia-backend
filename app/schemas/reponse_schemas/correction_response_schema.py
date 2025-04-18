from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class GrammarErrorResponse(BaseModel):
    id: str
    error: str
    reason: str
    suggestion: str
    improvedClause: str


class SentenceFeedbackResponse(BaseModel):
    id: str
    original: str
    corrected: str
    errors: List[GrammarErrorResponse]


class CorrectionData(BaseModel):
    conversationId: str
    createdAt: datetime
    originalText: str
    sentenceFeedback: List[SentenceFeedbackResponse]


class CorrectionResponse(BaseModel):
    success: bool
    data: Optional[CorrectionData] 
    error: Optional[str]
