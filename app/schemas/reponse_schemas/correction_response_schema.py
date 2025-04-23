from typing import List, Optional, Union
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


class PaginatedCorrectionsResponse(BaseModel):
    corrections: List[CorrectionData]
    total: int
    page: int
    limit: int


class CorrectionResponse(BaseModel):
    success: bool
    data: Optional[Union[List[CorrectionData], PaginatedCorrectionsResponse]]
    error: Optional[str]
