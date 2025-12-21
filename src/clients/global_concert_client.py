# src/clients/global_concert_client.py
import os
import time
import random
import requests
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

API_TOKEN = os.getenv("TICKETMASTER_API_TOKEN")
BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

class TicketmasterError(Exception):
    pass

def get_artist_events(
    artist: str,
    api_token: str | None = None,
    retries: int = 3,
    page_size: int = 20
):
    token = api_token or API_TOKEN
    if not token:
        raise TicketmasterError("TICKETMASTER_API_TOKEN is not set")

    params = {
        "apikey": token,
        "keyword": artist,
        "size": page_size
    }

    headers = {"User-Agent": "Mozilla/5.0 (Ticketmaster Collector Bot)"}

    for attempt in range(retries):
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            events = data.get("_embedded", {}).get("events", [])
            result = []

            for e in events:
                venue = e.get("_embedded", {}).get("venues", [{}])[0]
                result.append({
                    "artist_name": artist,
                    "event_name": e.get("name"),
                    "datetime": e.get("dates", {}).get("start", {}).get("dateTime"),
                    "venue": venue.get("name"),
                    "city": venue.get("city", {}).get("name"),
                    "country": venue.get("country", {}).get("name"),
                    "fetched_at": pd.Timestamp.utcnow(),
                    "timezone": e.get("dates", {}).get("timezone"),
                    "url": e.get("_links", {}).get("self", {}).get("href"),
                    "source": "ticketmaster"
                })
            return result

        if response.status_code == 429:
            sleep_time = (2 ** attempt) + random.uniform(0.2, 0.6)
            print(f"[Ticketmaster] 429 for '{artist}', retry in {sleep_time:.1f}s (attempt {attempt+1}/{retries})")
            time.sleep(sleep_time)
            continue

        raise TicketmasterError(f"Ticketmaster API error {response.status_code}: {response.text}")

    return []