# app/services/conversation_store.py
import time
from collections import defaultdict
from threading import Lock

MAX_TURNS = 6  # last N exchanges kept per session
TTL_SECONDS = 60 * 30  # expire idle sessions after 30 min

class ConversationStore:
    def __init__(self):
        self._sessions = defaultdict(list)
        self._last_seen = {}
        self._lock = Lock()

    def get_history(self, session_id: str):
        with self._lock:
            self._evict_expired()
            return list(self._sessions.get(session_id, []))

    def add_turn(self, session_id: str, question: str, answer: str):
        with self._lock:
            self._sessions[session_id].append({"question": question, "answer": answer})
            self._sessions[session_id] = self._sessions[session_id][-MAX_TURNS:]
            self._last_seen[session_id] = time.time()

    def _evict_expired(self):
        now = time.time()
        expired = [sid for sid, t in self._last_seen.items() if now - t > TTL_SECONDS]
        for sid in expired:
            self._sessions.pop(sid, None)
            self._last_seen.pop(sid, None)

conversation_store = ConversationStore()