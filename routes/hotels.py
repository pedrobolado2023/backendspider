from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import database
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Pydantic models
class HotelBase(BaseModel):
    name: str
    official_url: str
    is_active: bool = True
    instruction: Optional[str] = "extraia o preço, data check-in checkout"
    proxy_host: Optional[str] = None
    proxy_port: Optional[str] = None
    proxy_user: Optional[str] = None
    proxy_pass: Optional[str] = None

class HotelCreate(HotelBase):
    pass

class HotelOut(HotelBase):
    id: int
    status: str
    class Config:
        from_attributes = True

class BulkHotelCreate(BaseModel):
    urls: str # Newline separated URLs
    instruction: Optional[str] = "extraia o preço, data check-in checkout"

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[HotelOut])
def read_hotels(db: Session = Depends(get_db)):
    return db.query(database.Hotel).all()

@router.post("/", response_model=HotelOut)
def create_hotel(hotel: HotelCreate, db: Session = Depends(get_db)):
    db_hotel = database.Hotel(**hotel.dict())
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)
    return db_hotel

@router.post("/bulk", response_model=List[HotelOut])
def bulk_create_hotels(bulk: BulkHotelCreate, db: Session = Depends(get_db)):
    urls = [u.strip() for u in bulk.urls.split("\n") if u.strip()]
    created_hotels = []
    for url in urls:
        name = url.split("//")[-1].split("/")[0] # Simple name extraction
        db_hotel = database.Hotel(
            name=name, 
            official_url=url,
            instruction=bulk.instruction
        )
        db.add(db_hotel)
        created_hotels.append(db_hotel)
    db.commit()
    for h in created_hotels:
        db.refresh(h)
    return created_hotels

@router.delete("/{hotel_id}")
def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
    db_hotel = db.query(database.Hotel).filter(database.Hotel.id == hotel_id).first()
    if not db_hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    db.delete(db_hotel)
    db.commit()
    return {"message": "Hotel deleted successfully"}
