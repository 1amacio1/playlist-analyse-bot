from clients.music_playlist_client import MusicClient
from services.playlist_service import ServicePlaylist
from utils.url_parser import extract_from_url
from dotenv import load_dotenv

load_dotenv()

def main():
    url = input()

    owner, kind = extract_from_url(url)

    client = MusicClient.from_env()
    service = ServicePlaylist(client)

    arts = service.get_artist_names(kind, owner)
    for name in arts:
        print(name)
#
if __name__ == "__main__":
    main()