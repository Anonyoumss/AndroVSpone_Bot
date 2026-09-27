"""
debate.py
---------
Debate state management: sessions, message counting, timer bar generation.
Safe cleanup with .pop() to avoid KeyError crashes.
"""

import time
from dataclasses import dataclass, field
from typing import Optional
from config import logger


@dataclass
class Submission:
    """A single argument in the debate."""
    user_id: int
    username: str
    text: str
    media_type: Optional[str] = None  # "photo" or "video" if media included


@dataclass
class DebateSession:
    """Encapsulates a single debate round."""
    chat_id: int
    topic: str
    mode: str  # "human_vs_ai", "1v1_silent", "1v1_sportscaster"
    timer_seconds: int
    message_limit: int  # per person (999 = unlimited)
    model: str
    started_at: float = field(default_factory=time.time)
    submissions: list[Submission] = field(default_factory=list)
    message_counts: dict[int, int] = field(default_factory=dict)  # user_id -> count
    timer_job_id: Optional[int] = None
    status_message_id: Optional[int] = None  # pinned timer message

    def seconds_remaining(self) -> int:
        elapsed = time.time() - self.started_at
        return max(0, int(self.timer_seconds - elapsed))

    def is_expired(self) -> bool:
        return self.seconds_remaining() <= 0

    def can_user_submit(self, user_id: int) -> bool:
        """Check if user has hit their message limit."""
        count = self.message_counts.get(user_id, 0)
        return count < self.message_limit

    def increment_user_message(self, user_id: int) -> int:
        """Increment user's message count and return new count."""
        self.message_counts[user_id] = self.message_counts.get(user_id, 0) + 1
        return self.message_counts[user_id]

    def add_submission(self, user_id: int, username: str, text: str, media_type: Optional[str] = None):
        """Record a submission."""
        submission = Submission(user_id, username, text, media_type)
        self.submissions.append(submission)
        logger.info(
            f"Submission recorded | chat={self.chat_id} | user={username} | "
            f"media={media_type or 'text'} | limit={self.message_counts.get(user_id, 0)}/{self.message_limit}"
        )

    def get_transcript(self) -> str:
        """Return full debate transcript for verdict generation."""
        lines = [f"**Topic:** {self.topic}\n"]
        for sub in self.submissions:
            media_str = f" [{sub.media_type}]" if sub.media_type else ""
            lines.append(f"**{sub.username}**{media_str}:\n{sub.text}\n")
        return "\n".join(lines)


class DebateManager:
    """Thread-unsafe state dict manager (single event loop assumption)."""

    def __init__(self):
        self.sessions: dict[int, DebateSession] = {}

    def create_session(
        self,
        chat_id: int,
        topic: str,
        mode: str,
        timer_seconds: int,
        message_limit: int,
        model: str,
    ) -> DebateSession:
        """Start a new debate session."""
        if chat_id in self.sessions:
            raise ValueError(f"Debate already active in chat {chat_id}")
        
        session = DebateSession(
            chat_id=chat_id,
            topic=topic,
            mode=mode,
            timer_seconds=timer_seconds,
            message_limit=message_limit,
            model=model,
        )
        self.sessions[chat_id] = session
        logger.info(
            f"Debate created | chat={chat_id} | topic={topic} | mode={mode} | "
            f"timer={timer_seconds}s | limit={message_limit} | model={model}"
        )
        return session

    def get_session(self, chat_id: int) -> Optional[DebateSession]:
        """Fetch active session (None if not found)."""
        return self.sessions.get(chat_id)

    def has_session(self, chat_id: int) -> bool:
        """Check if debate is active."""
        return chat_id in self.sessions

    def end_session(self, chat_id: int) -> Optional[DebateSession]:
        """End debate and return the session (safe pop)."""
        session = self.sessions.pop(chat_id, None)
        if session:
            logger.info(f"Debate ended | chat={chat_id}")
        return session

    def get_all_sessions(self) -> dict[int, DebateSession]:
        """Return all active sessions (for timer jobs)."""
        return self.sessions.copy()


def generate_timer_bar(remaining: int, total: int, width: int = 10) -> str:
    """Generate a visual progress bar: ▓▓▓░░░░░░░"""
    if total <= 0:
        return "█" * width
    filled = max(0, min(width, int((1 - remaining / total) * width)))
    empty = width - filled
    bar = "▓" * filled + "░" * empty
    minutes = remaining // 60
    seconds = remaining % 60
    return f"{bar} {minutes}m{seconds:02d}s"
