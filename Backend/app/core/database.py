from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from dotenv import load_dotenv
import os
import ssl

load_dotenv()

class Database:
    client: Optional[AsyncIOMotorClient] = None
    
    def connect_to_database(self, path: str = None):
        MONGODB_URL = path or os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        
        # Connect with SSL options
        self.client = AsyncIOMotorClient(
            MONGODB_URL,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        try:
            # The ping command is cheap and does not require auth
            self.client.admin.command('ping')
            print("MongoDB connection successful")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
        
    def close_database_connection(self):
        if self.client:
            self.client.close()

# Create a database instance
db = Database()

# Get database instance
def get_database() -> Database:
    return db 