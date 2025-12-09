from clients.music_playlist_client import MusicClient
from services.playlist_service import ServicePlaylist
from utils.url_parser import extract_from_url
from dotenv import load_dotenv

load_dotenv()

def main():
    url = "https://music.yandex.ru/users/kadkini/playlists/1002?ref_id=F3493709-2075-48D5-9264-D80FF61A7684&utm_medium=copy_link"

    owner, kind = extract_from_url(url)

    client = MusicClient.from_env()
    service = ServicePlaylist(client)

    arts = service.get_artist_names(kind, owner)
    for name in arts:
        print(name)
#
if __name__ == "__main__":
    main()