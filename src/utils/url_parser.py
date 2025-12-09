# src/utils/url_parser.py
import re
from typing import Tuple

def extract_from_url(text: str) -> Tuple[str, str]:
    match = re.search(r'<iframe[^>]*src\s*=\s*["\']([^"\']+)["\']', text, re.IGNORECASE)
    if match:
        url = match.group(1).strip()
    else:
        url = text.strip()

    pk = re.search(r'/iframe/playlist/([^/]+)/(\d+)', url)
    if pk:
        return pk.group(1), pk.group(2)

    mobile = re.search(r'/users/([^/]+)/playlists/(\d+)', url)
    if mobile:
        return mobile.group(1), mobile.group(2)

    raise ValueError("URL не подходит")