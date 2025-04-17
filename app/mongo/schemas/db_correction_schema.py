from typing import List
from pydantic import BaseModel
from datetime import datetime


class DbError(BaseModel):
    id: str
    error: str
    reason: str
    suggestion: str
    improvedClause: str


class DbSentenceFeedback(BaseModel):
    id: str
    original: str
    corrected: str
    errors: List[DbError]


class DbCorrection(BaseModel):
    userId: str
    conversationId: str
    createdAt: datetime
    originalText: str
    sentenceFeedback: List[DbSentenceFeedback]
