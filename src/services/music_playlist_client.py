import os
from yandex_music import Client


class MusicClient:
    def __init__(self, token: str):
        self._client = Client(token).init()

    @classmethod
    def from_env(cls) -> "MusicClient":
        token = os.getenv("YANDEX_MUSIC_TOKEN")
        if not token:
            raise EnvironmentError("YANDEX_MUSIC_TOKEN не установлен")
        return cls(token)

    def get_playlist(self, kind: str, owner: str):
        return self._client.users_playlists(kind, owner)

