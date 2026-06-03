import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, text
from azure.storage.blob import BlobServiceClient

# Define a temporary settings class that matches the .env structure
class TestSettings(BaseSettings):
    DATABASE_URL: str
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_CONTAINER_NAME: str = "$logs"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        extra="ignore"
    )

def test_connections():
    print("--- Loading Configuration ---")
    try:
        settings = TestSettings()
        print("Configuration loaded successfully from .env")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return

    print(f"\n--- Testing PostgreSQL ---")
    # Try the configured DB first
    db_urls_to_try = [settings.DATABASE_URL]
    
    # Also try the default 'postgres' DB if the first one fails
    if "/health-ai-db" in settings.DATABASE_URL:
        db_urls_to_try.append(settings.DATABASE_URL.replace("/health-ai-db", "/postgres"))

    for db_url in db_urls_to_try:
        try:
            if "sslmode" not in db_url:
                if "?" in db_url:
                    db_url += "&sslmode=require"
                else:
                    db_url += "?sslmode=require"
            
            db_name = db_url.split("/")[-1].split("?")[0]
            print(f"Testing connection to database: '{db_name}'...")
            
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version();"))
                version = result.fetchone()
                print(f"✅ Successfully connected to PostgreSQL database '{db_name}'!")
                print(f"Database version: {version[0]}")
                return # Stop if successful
        except Exception as e:
            print(f"❌ Connection to '{db_name}' failed: {e}")

    print(f"\n--- Testing Azure Storage ---")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        account_info = blob_service_client.get_account_information()
        print(f"✅ Successfully connected to Azure Storage Account!")
        print(f"Account Tier: {account_info.get('account_tier')}")
        
        container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER_NAME)
        if container_client.exists():
            print(f"Container '{settings.AZURE_CONTAINER_NAME}' exists.")
        else:
            print(f"Container '{settings.AZURE_CONTAINER_NAME}' does not exist (but connection is valid).")
    except Exception as e:
        print(f"❌ Azure Storage connection failed: {e}")

if __name__ == "__main__":
    test_connections()
