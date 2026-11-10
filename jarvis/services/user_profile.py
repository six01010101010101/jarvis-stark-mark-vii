"""Perfil de usuário autenticado, contas e canais vinculados do senhor Ken."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from jarvis.repositories.memory_repository import MemoryRepository


@dataclass(frozen=True)
class UserProfile:
    """Dados de identificação e conexões de redes do usuário principal."""

    name: str = "Ken Kobayashi"
    youtube_email: str = "keekobayashi2005@gmail.com"
    google_email: str = "kenkobayashi2005@gmail.com"
    whatsapp_number: str = "5511981237033"
    instagram_handle: str = "dracos6x"

    def sync_to_database(self, repository: MemoryRepository) -> None:
        """Persiste todos os dados de perfil no banco SQLite local."""
        repository.set_memory("user_name", self.name, category="profile")
        repository.set_memory("youtube_email", self.youtube_email, category="profile")
        repository.set_memory("google_email", self.google_email, category="profile")
        repository.set_memory("whatsapp_number", self.whatsapp_number, category="profile")
        repository.set_memory("instagram_handle", self.instagram_handle, category="profile")

    def get_instagram_url(self) -> str:
        """URL direta do perfil do Instagram."""
        return f"https://www.instagram.com/{self.instagram_handle}/"

    def get_youtube_url(self) -> str:
        """URL do YouTube associada à conta."""
        return "https://www.youtube.com/"

    def get_whatsapp_url(self, message: str = "") -> str:
        """URL para envio de mensagem no WhatsApp do próprio usuário."""
        if message:
            return f"https://web.whatsapp.com/send?phone={self.whatsapp_number}&text={quote(message)}"
        return f"https://web.whatsapp.com/send?phone={self.whatsapp_number}"


KEN_PROFILE = UserProfile()
