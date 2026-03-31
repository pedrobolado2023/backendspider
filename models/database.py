from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import datetime

import os
from dotenv import load_dotenv

load_dotenv()

# Use environment variable for database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:35946800Pedro@db.ptkmfeinqmisluyljlyn.supabase.co:5432/postgres")

# PostgreSQL URL cleanup
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ensure sslmode=require for cloud deployments if not already present
if "sslmode=" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL += f"{separator}sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    official_url = Column(String)
    instruction = Column(String, default="extraia o preço, data check-in checkout")
    status = Column(String, default="idle") # idle, running, completed, failed
    
    # Proxy Configuration
    proxy_host = Column(String, nullable=True)
    proxy_port = Column(String, nullable=True)
    proxy_user = Column(String, nullable=True)
    proxy_pass = Column(String, nullable=True)
    
    # AI Discovery & Logs
    last_ai_log = Column(String, nullable=True)
    discovery_map = Column(String, nullable=True) # JSON store for selectors/logic
    is_active = Column(Boolean, default=True)
    
    rates = relationship("RateSnapshot", back_populates="hotel")
    ai_logs = relationship("AIJobLog", back_populates="hotel")

class RateSnapshot(Base):
    __tablename__ = "rate_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), index=True)
    check_in = Column(DateTime, index=True)
    rate_value = Column(Float)
    currency = Column(String, default="BRL")
    adults = Column(Integer, default=2)
    scraped_at = Column(DateTime, default=datetime.datetime.utcnow)

    hotel = relationship("Hotel", back_populates="rates")

class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    status = Column(String) # SUCCESS, ERROR
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class AIJobLog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    action = Column(String) # Discovery, Extraction
    prompt = Column(String)
    response = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    hotel = relationship("Hotel", back_populates="ai_logs")

Base.metadata.create_all(bind=engine)
