from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from DeviceManager import DeviceManager
from contextlib import asynccontextmanager
import asyncio

# Configuration for the serial interface
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

# DeviceManager instance
device_manager = DeviceManager(SERIAL_PORT, BAUD_RATE)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        device_manager.connect()
    except Exception as e:
        print(f"Error during device initialization: {e}")

    yield  # Application runs here

    # Disconnect the device on shutdown
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
    return {"message": "Welcome to the grpc FastAPI backend interface!"}


@app.get("/get-device-id")
async def get_device_id():
    """
    Fetch unique identification data from the device and return it as JSON.
    """
    return device_manager.get_device_id()


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
