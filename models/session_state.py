# models/session_state.py
# Data structures for NPC Agent Engine
# Edtronaut AI Co-worker Engine

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SessionState:
    """
    Trạng thái của 1 session learner.
    Được lưu trong Redis, cập nhật sau mỗi turn.

    Attributes:
        mood_score      : Cảm xúc hiện tại của NPC (-2.0 đến +2.0)
        turn_count      : Số turn đã qua trong session
        history         : Lịch sử hội thoại (sliding window 10 turns)
        rubric_coverage : Những deliverable nào learner đã đề cập
        stuck_signal    : Đếm số turn bị stuck liên tiếp
    """
    mood_score: float = 0.0
    turn_count: int = 0
    history: list = field(default_factory=list)
    rubric_coverage: dict = field(default_factory=dict)
    stuck_signal: int = 0


@dataclass
class AgentResponse:
    """
    Output trả về sau mỗi turn.

    Attributes:
        message          : Câu trả lời của NPC gửi về frontend
        state_update     : SessionState đã được cập nhật
        safety_flags     : Kết quả kiểm tra an toàn
        director_action  : Instruction từ Supervisor nếu có can thiệp
    """
    message: str
    state_update: SessionState
    safety_flags: dict
    director_action: Optional[str] = None