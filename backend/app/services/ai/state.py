from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage

def trim_messages_reducer(existing: Sequence[BaseMessage], new: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    """
    Custom reducer that adds new messages and trims the total history 
    to the last 10 messages (approx 5 chat turns).
    """
    combined = list(existing) + list(new)
    # Keep only the last 10 messages to remember past 5 chats per session
    return combined[-10:]

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], trim_messages_reducer]
    user_id: int
    classification: str
    next_agent: str
    final_response: str
