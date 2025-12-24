import pytest
from src.repositories.concert_repository import ConcertRepository

class TestConcertRepository:
    
    def test_repository_has_methods(self):
        assert hasattr(ConcertRepository, 'save_event')
        assert hasattr(ConcertRepository, 'get_events_by_category')
        assert hasattr(ConcertRepository, 'count_events_by_category')
        assert hasattr(ConcertRepository, 'close')
        assert hasattr(ConcertRepository, 'connect')
