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


class ConversationData(BaseModel):
    conversationId: str
    createdAt: datetime
    originalText: str
    sentenceFeedback: List[SentenceFeedbackResponse]


class PaginatedConversationsResponse(BaseModel):
    conversations: List[ConversationData]
    total: int
    page: int
    limit: int


class ConversationResponse(BaseModel):
    success: bool
    data: Optional[Union[List[ConversationData], PaginatedConversationsResponse]]
    error: Optional[str]
