import re
from typing import Optional, Dict


def extract_date_from_description(description: Optional[str]) -> Optional[str]:
    if not description:
        return None
    parts = description.split('•')
    if parts and len(parts) > 0:
        date_part = parts[0].strip()
        date_part = re.sub(r',\s*\d{1,2}:\d{2}', '', date_part)
        date_part = re.sub(r'^(завтра|сегодня|послезавтра)\s+', '', date_part, flags=re.IGNORECASE)
        return date_part if date_part else None
    return None


def extract_time_from_description(description: Optional[str]) -> Optional[str]:
    if not description:
        return None
    parts = description.split('•')
    if parts and len(parts) > 0:
        date_time_part = parts[0].strip()
        time_match = re.search(r'(\d{1,2}:\d{2})', date_time_part)
        if time_match:
            return time_match.group(1)
    return None


def extract_venue_from_description(description: Optional[str]) -> Optional[str]:
    if not description:
        return None
    parts = description.split('•')
    if len(parts) > 1:
        venue = parts[1].strip()
        return venue if venue else None
    return None


def get_concert_date(concert: Dict) -> Optional[str]:
    if 'dates' in concert and concert['dates']:
        dates = concert['dates']
        if isinstance(dates, list) and len(dates) > 0:
            return ', '.join(dates[:3])
    if 'date' in concert and concert['date']:
        return concert['date']
    if 'description' in concert and concert['description']:
        date_from_desc = extract_date_from_description(concert['description'])
        if date_from_desc:
            return date_from_desc
    return None


def get_concert_time(concert: Dict) -> Optional[str]:
    if 'description' in concert and concert['description']:
        time_from_desc = extract_time_from_description(concert['description'])
        if time_from_desc:
            return time_from_desc
    return None


def get_concert_venue(concert: Dict) -> Optional[str]:
    if 'venue' in concert and concert['venue']:
        return concert['venue']
    if 'description' in concert and concert['description']:
        venue_from_desc = extract_venue_from_description(concert['description'])
        if venue_from_desc:
            return venue_from_desc
    return None
