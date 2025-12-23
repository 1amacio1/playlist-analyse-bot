import pytest
from unittest.mock import Mock
from src.services.playlist_service import ServicePlaylist

@pytest.fixture
def client():
    c = Mock()
    pl = Mock()
    tr = Mock()
    tr.track = Mock()
    a = Mock()
    a.name = 'Artist1'
    tr.track.artists = [a]
    pl.fetch_tracks.return_value = [tr]
    c.get_playlist.return_value = pl
    return c

def test_get_artists(client):
    s = ServicePlaylist(client)
    res = s.get_artist_names('kind', 'owner')
    assert len(res) == 1
    assert res[0] == 'Artist1'

def test_empty(client):
    c = Mock()
    pl = Mock()
    pl.fetch_tracks.return_value = []
    c.get_playlist.return_value = pl
    s = ServicePlaylist(c)
    res = s.get_artist_names('kind', 'owner')
    assert res == []

def test_no_track():
    c = Mock()
    pl = Mock()
    tr = Mock()
    tr.track = None
    pl.fetch_tracks.return_value = [tr]
    c.get_playlist.return_value = pl
    s = ServicePlaylist(c)
    res = s.get_artist_names('kind', 'owner')
    assert res == []

def test_no_artists():
    c = Mock()
    pl = Mock()
    tr = Mock()
    tr.track = Mock()
    tr.track.artists = []
    pl.fetch_tracks.return_value = [tr]
    c.get_playlist.return_value = pl
    s = ServicePlaylist(c)
    res = s.get_artist_names('kind', 'owner')
    assert res == []
