from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models for reminder functionality
class Reminder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    interval_minutes: int
    is_active: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ReminderCreate(BaseModel):
    text: str
    interval_minutes: int

class ReminderUpdate(BaseModel):
    text: Optional[str] = None
    interval_minutes: Optional[int] = None
    is_active: Optional[bool] = None

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "Smart Reminders API is running!"}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": "Smart Reminders API"
    }

# Reminder routes
@api_router.post("/reminders", response_model=Reminder)
async def create_reminder(reminder_data: ReminderCreate):
    """Create a new reminder configuration"""
    try:
        reminder_dict = reminder_data.dict()
        reminder_obj = Reminder(**reminder_dict)
        
        # Insert into database
        result = await db.reminders.insert_one(reminder_obj.dict())
        
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to create reminder")
        
        return reminder_obj
    except Exception as e:
        logger.error(f"Error creating reminder: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/reminders", response_model=List[Reminder])
async def get_reminders():
    """Get all reminders for the user"""
    try:
        reminders = await db.reminders.find().to_list(1000)
        return [Reminder(**reminder) for reminder in reminders]
    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/reminders/{reminder_id}", response_model=Reminder)
async def get_reminder(reminder_id: str):
    """Get a specific reminder by ID"""
    try:
        reminder = await db.reminders.find_one({"id": reminder_id})
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        return Reminder(**reminder)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reminder {reminder_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.put("/reminders/{reminder_id}", response_model=Reminder)
async def update_reminder(reminder_id: str, reminder_update: ReminderUpdate):
    """Update a reminder"""
    try:
        # Find existing reminder
        existing_reminder = await db.reminders.find_one({"id": reminder_id})
        if not existing_reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        # Prepare update data
        update_data = {k: v for k, v in reminder_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in database
        result = await db.reminders.update_one(
            {"id": reminder_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update reminder")
        
        # Return updated reminder
        updated_reminder = await db.reminders.find_one({"id": reminder_id})
        return Reminder(**updated_reminder)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reminder {reminder_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    """Delete a reminder"""
    try:
        result = await db.reminders.delete_one({"id": reminder_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        return {"message": "Reminder deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reminder {reminder_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Legacy status check routes (keeping for compatibility)
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)