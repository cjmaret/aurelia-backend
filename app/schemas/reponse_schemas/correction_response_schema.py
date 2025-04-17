from typing import List
from pydantic import BaseModel
from datetime import datetime


class ErrorResponse(BaseModel):
    id: str
    error: str
    reason: str
    suggestion: str
    improvedClause: str


class SentenceFeedbackResponse(BaseModel):
    id: str
    original: str
    corrected: str
    errors: List[ErrorResponse]


class CorrectionResponse(BaseModel):
    conversationId: str
    createdAt: datetime
    originalText: str
    sentenceFeedback: List[SentenceFeedbackResponse]