import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:35946800Pedro@db.ptkmfeinqmisluyljlyn.supabase.co:5432/postgres")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Testing connection to: {DATABASE_URL.split('@')[-1]}")

try:
    # Use a simpler connection string for testing if SSL fails
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT count(*) FROM hotels"))
        count = result.scalar()
        print(f"SUCCESS: Connected to Supabase. Found {count} hotels.")
except Exception as e:
    print(f"FAILED to connect: {e}")
    print("\nTip: If you're on Windows and see SSL errors, it's usually a local environment issue.")
    print("This will work in Docker (Easypanel) because it uses a Linux environment with full SSL support.")
