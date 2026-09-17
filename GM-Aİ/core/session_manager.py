import os
import time
import uuid
from typing import Dict, Any, Optional
from core.game_state import GameState

class SessionManager:
    """
    Çoklu Kullanıcı ve Oturum Yöneticisi (Session Manager).
    Global tekil oyun durumu yerine, her istemci / sekme için izole edilmiş
    GameState ve API anahtarı oturumları sağlar.
    """

    def __init__(self, ttl_hours: int = 24):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_hours * 3600
        self.default_session_id = "default"
        # Varsayılan oturumu başlat (tek kişilik yerel kullanım ve test geriye uyumluluğu)
        self._init_session(self.default_session_id)

    def _init_session(self, session_id: str, api_key: str = "") -> Dict[str, Any]:
        env_key = os.environ.get("GEMINI_API_KEY", "").strip()
        data = {
            "game_state": GameState(),
            "api_key": api_key.strip() or env_key,
            "created_at": time.time(),
            "last_accessed": time.time()
        }
        self.sessions[session_id] = data
        return data

    def cleanup_expired(self):
        now = time.time()
        expired = [
            sid for sid, s in self.sessions.items()
            if sid != self.default_session_id and (now - s.get("last_accessed", 0)) > self.ttl_seconds
        ]
        for sid in expired:
            del self.sessions[sid]

    def get_or_create(self, session_id: Optional[str] = None) -> tuple[str, GameState]:
        self.cleanup_expired()
        sid = str(session_id).strip() if session_id else ""
        if not sid:
            sid = self.default_session_id

        if sid not in self.sessions:
            self._init_session(sid)

        self.sessions[sid]["last_accessed"] = time.time()
        return sid, self.sessions[sid]["game_state"]

    def get_game(self, session_id: Optional[str] = None) -> GameState:
        _, game = self.get_or_create(session_id)
        return game

    def get_api_key(self, session_id: Optional[str] = None) -> str:
        sid = str(session_id).strip() if session_id else self.default_session_id
        if sid in self.sessions:
            return self.sessions[sid].get("api_key", "")
        return os.environ.get("GEMINI_API_KEY", "").strip()

    def set_api_key(self, key: str, session_id: Optional[str] = None):
        sid = str(session_id).strip() if session_id else self.default_session_id
        if sid not in self.sessions:
            self._init_session(sid, key)
        else:
            self.sessions[sid]["api_key"] = key.strip()
            self.sessions[sid]["last_accessed"] = time.time()

    def delete_session(self, session_id: str) -> bool:
        if session_id and session_id != self.default_session_id and session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
