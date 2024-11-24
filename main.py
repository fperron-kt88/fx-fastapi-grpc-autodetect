# Copyright 2024 Francois Perron
# This software is proprietary and confidential.
# Use is subject to the accompanying license agreement.


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from DeviceManager import DeviceManager
from contextlib import asynccontextmanager
import asyncio

# DeviceManager instance
device_manager = DeviceManager()


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        device_manager.connect()
    except Exception as e:
        print(f"Error during device initialization: {e}")
        print("Proceeding without a connected device.")  # Allow server to start

    yield  # Application runs here

    device_manager.disconnect()


# Initialize FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint for testing the API.
    """
    status = "connected" if device_manager.is_connected() else "disconnected"
    return {
        "message": "Welcome to the grpc FastAPI backend interface!",
        "status": status,
    }


@app.get("/get-active-interface")
async def get_active_interface():
    """
    Return the active serial interface using the device manager.
    """
    return device_manager.get_active_interface()


@app.get("/get-device-id")
async def get_device_id():
    """
    Fetch unique identification data from the device and return it as JSON.
    """
    return device_manager.get_device_id()


@app.post("/clear-uuid")
async def clear_device_uuid():
    """
    Clear the stored UUID in the device manager.
    """
    device_manager.clear_uuid()
    return {"message": "Stored UUID cleared. Ready to accept a new device."}


# Main entry point for running the server
if __name__ == "__main__":
    import signal
    import uvicorn

    def handle_exit(sig, frame):
        print("Received signal to terminate, shutting down...")
        asyncio.get_event_loop().stop()

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl_certfile="./certs/acme.crt",
        ssl_keyfile="./certs/acme.key",
        reload=True,
    )
