from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import database
from routes import hotels, rates, insights

app = FastAPI(title="Hotel Rate Intelligence API")

# CORS - permite chamadas do frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3005",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Hotel Rate Intelligence API"}

# Include routers 
app.include_router(hotels.router, prefix="/api/hotels", tags=["Hotels"])
app.include_router(rates.router, prefix="/api/rates", tags=["Rates"])
app.include_router(insights.router, prefix="/api/insights", tags=["Insights"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
