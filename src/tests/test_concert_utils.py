import pytest
from src.utils.concert_utils import extract_date_from_description, extract_time_from_description
from src.utils.concert_utils import extract_venue_from_description, get_concert_date, get_concert_time, get_concert_venue

def test_extract_date():
    desc = "15 марта 2024, 19:00 • Venue"
    res = extract_date_from_description(desc)
    assert res == "15 марта 2024"

def test_extract_date_none():
    res = extract_date_from_description(None)
    assert res is None

def test_extract_time():
    desc = "15 марта 2024, 19:00 • Venue"
    res = extract_time_from_description(desc)
    assert res == "19:00"

def test_extract_time_none():
    res = extract_time_from_description(None)
    assert res is None

def test_extract_venue():
    desc = "15 марта 2024, 19:00 • Venue Name"
    res = extract_venue_from_description(desc)
    assert res == "Venue Name"

def test_extract_venue_none():
    res = extract_venue_from_description(None)
    assert res is None

def test_get_date():
    c = {'dates': ['2024-03-15']}
    res = get_concert_date(c)
    assert '2024-03-15' in res

def test_get_date_field():
    c = {'date': '2024-03-15'}
    res = get_concert_date(c)
    assert res == '2024-03-15'

def test_get_date_desc():
    c = {'description': '15 марта 2024, 19:00 • Venue'}
    res = get_concert_date(c)
    assert res is not None

def test_get_time():
    c = {'description': '15 марта 2024, 19:00 • Venue'}
    res = get_concert_time(c)
    assert res == '19:00'

def test_get_venue():
    c = {'venue': 'Test Venue'}
    res = get_concert_venue(c)
    assert res == 'Test Venue'

def test_get_venue_desc():
    c = {'description': '15 марта 2024, 19:00 • Venue Name'}
    res = get_concert_venue(c)
    assert res == 'Venue Name'

def test_get_date_empty():
    c = {}
    res = get_concert_date(c)
    assert res is None

def test_get_time_empty():
    c = {}
    res = get_concert_time(c)
    assert res is None

def test_get_venue_empty():
    c = {}
    res = get_concert_venue(c)
    assert res is None

def test_extract_date_tomorrow():
    desc = "завтра 19:00 • Venue"
    res = extract_date_from_description(desc)
    assert res is not None

def test_extract_time_none():
    desc = "15 марта 2024 • Venue"
    res = extract_time_from_description(desc)
    assert res is None

def test_extract_date_empty_string():
    res = extract_date_from_description('')
    assert res is None

def test_extract_time_empty_string():
    res = extract_time_from_description('')
    assert res is None

def test_extract_venue_empty_string():
    res = extract_venue_from_description('')
    assert res is None

def test_extract_venue_no_second_part():
    desc = "15 марта 2024, 19:00"
    res = extract_venue_from_description(desc)
    assert res is None
