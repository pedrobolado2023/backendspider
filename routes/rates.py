from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import database
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

class RateSnapshotOut(BaseModel):
    id: int
    hotel_id: int
    check_in: datetime
    rate: float
    currency: str
    adults: int
    scraped_at: datetime
    class Config:
        from_attributes = True

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[RateSnapshotOut])
def read_rates(
    hotel_id: Optional[int] = None, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None, 
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(database.RateSnapshot)
    if hotel_id:
        query = query.filter(database.RateSnapshot.hotel_id == hotel_id)
    if start_date:
        query = query.filter(database.RateSnapshot.check_in >= start_date)
    if end_date:
        query = query.filter(database.RateSnapshot.check_in <= end_date)
    return query.order_by(database.RateSnapshot.scraped_at.desc()).offset(offset).limit(limit).all()

from scraper.ai_scraper import AIScraper
import asyncio

@router.post("/fetch")
async def fetch_rates_now(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(database.Hotel).filter(database.Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Update status to running
    hotel.status = "running"
    db.commit()
    
    scraper = AIScraper()
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    proxy_config = {
        "host": hotel.proxy_host,
        "port": hotel.proxy_port,
        "user": hotel.proxy_user,
        "pass": hotel.proxy_pass
    } if hotel.proxy_host else None
    
    try:
        result = await scraper.get_hotel_rate(
            hotel.id, 
            hotel.official_url, 
            today, 
            tomorrow, 
            hotel.instruction,
            proxy_config=proxy_config,
            discovery_map=hotel.discovery_map
        )
        
        # Save AI Thought and Log
        hotel.last_ai_log = result.get("ai_log")
        
        if result.get("status") == "SUCCESS":
            db_rate = database.RateSnapshot(
                hotel_id=hotel_id,
                check_in=today,
                rate=result["rate"],
                currency=result.get("currency", "BRL"),
                adults=2
            )
            db.add(db_rate)
            hotel.status = "completed"
            
            # Save to AIJobLog
            ai_log = database.AIJobLog(
                hotel_id=hotel_id,
                action="Extraction",
                prompt=f"Instructions: {hotel.instruction}",
                response=result.get("ai_log")
            )
            db.add(ai_log)
            
            db.commit()
            return {"message": "Success", "rate": result["rate"]}
        else:
            hotel.status = "failed"
            db.commit()
            return {"message": "Failed to fetch rate", "status": result.get("status"), "reason": result.get("message")}
            
    except Exception as e:
        hotel.status = "failed"
        db.commit()
        return {"message": "Error during fetch", "error": str(e)}
