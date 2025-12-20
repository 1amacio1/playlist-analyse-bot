from typing import List

from src.services.music_playlist_client import MusicClient

class ServicePlaylist:
    def __init__(self, client: MusicClient):
        self._client = client

    def get_artist_names(self, kind: str, owner: str) -> List[str]:
        playlist = self._client.get_playlist(kind, owner)
        tracks = playlist.fetch_tracks()

        artists = []
        for tr in tracks:
            t = tr.track
            if t and t.artists:
                artists.append(t.artists[0].name)

        return artists
