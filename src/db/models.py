from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class Event(Base):
    __tablename__ = 'events'
    
    id = Column(String, primary_key=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    full_title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True)
    date = Column(String, nullable=True, index=True)
    dates = Column(JSONB, nullable=True)
    venue = Column(String, nullable=True)
    city = Column(String, nullable=True)
    source = Column(String, nullable=True)
    artist_name = Column(String, nullable=True)
    matched_artist = Column(String, nullable=True)
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_date', 'date'),
        Index('idx_city', 'city'),
        Index('idx_source', 'source'),
        UniqueConstraint('url', name='uq_events_url'),
    )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'full_title': self.full_title,
            'description': self.description,
            'category': self.category,
            'date': self.date,
            'dates': self.dates,
            'venue': self.venue,
            'city': self.city,
            'source': self.source,
            'artist_name': self.artist_name,
            'matched_artist': self.matched_artist,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        import hashlib
        url = data.get('url', '')
        event_id = hashlib.md5(url.encode()).hexdigest() if url else None
        
        event = cls(
            id=event_id,
            url=url,
            title=data.get('title'),
            full_title=data.get('full_title'),
            description=data.get('description'),
            category=data.get('category'),
            date=data.get('date'),
            dates=data.get('dates'),
            venue=data.get('venue'),
            city=data.get('city'),
            source=data.get('source'),
            artist_name=data.get('artist_name'),
            matched_artist=data.get('matched_artist'),
        )
        
        if 'scraped_at' in data and data['scraped_at']:
            if isinstance(data['scraped_at'], str):
                event.scraped_at = datetime.fromisoformat(data['scraped_at'].replace('Z', '+00:00'))
            else:
                event.scraped_at = data['scraped_at']
        
        return event

