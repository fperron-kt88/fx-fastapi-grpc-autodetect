from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from simple_rpc import Interface
from contextlib import asynccontextmanager
import json

# Configuration for the serial interface
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

# Global variable for the Interface object
interface = None


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    global interface
    try:
        print("Initializing Interface...")
        interface = Interface(SERIAL_PORT, BAUD_RATE)
        if not interface.is_open:
            raise RuntimeError("Failed to open interface.")
        print(f"Connected to {SERIAL_PORT}")
    except Exception as e:
        print(f"Error initializing Interface: {e}")
        interface = None

    yield  # Application runs here

    # Close the Interface on shutdown
    if interface and interface.is_open:
        print("Closing interface...")
        interface.close()


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
    global interface
    if interface is not None and interface.is_open():
        try:
            # Call the ESP32 method and retrieve raw tuple data
            raw_data = interface.getDeviceId()

            # Expected field names corresponding to tuple values
            field_names = [
                "board_uuid",
                "git_version",
                "api_version",
                "hw_version",
                "device_name",
            ]

            # Check if raw_data is a tuple with the expected number of fields
            if isinstance(raw_data, tuple) and len(raw_data) == len(field_names):
                # Decode any bytes fields and map them to field names
                response = {
                    field: (value.decode("utf-8") if isinstance(value, bytes) else value)
                    for field, value in zip(field_names, raw_data)
                }

                return response

            # Handle unexpected data format
            print("Unexpected tuple format or size.")
            return {"error": "Unexpected data format received from the device"}

        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

    # Return an error if the interface is not available
    print("Interface is not available or not open.")
    return {"error": "Interface not available"}



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
