from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from simple_rpc import Interface
from contextlib import asynccontextmanager
import json

# Configuration for the serial interface
SERIAL_PORT = "/dev/ttyUSB0"  # Replace with your ESP32's serial port
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
    allow_origins=["*"],  # Adjust this as needed
    allow_credentials=True,
    allow_methods=["*"],  # Adjust this as needed
    allow_headers=["*"],  # Adjust this as needed
)


# Define Pydantic model for parsing JSON-based responses
class ESP32IdJsonResponse(BaseModel):
    board_uuid: str
    git_version: str


@app.get("/")
async def root():
    """
    Root endpoint for testing the API.
    """
    return {"message": "Welcome to the ESP32 FastAPI interface!"}


@app.get("/get-id-string")
async def get_id_string():
    """
    Fetch board UUID and Git version as a plain string from the ESP32.
    """
    global interface
    if not interface or not interface.is_open:
        return {"error": "Interface not available"}

    try:
        response = interface.call_method("getId")
        if response:
            return {"id_string": response}
        else:
            return {"error": "No response from ESP32"}
    except Exception as e:
        return {"error": f"Failed to call method: {e}"}


@app.get("/get-id-json")
async def get_id_json():
    """
    Fetch board UUID and Git version from the ESP32 and return it as JSON.
    """
    print("Boink! This is a call to get-id-json....")
    global interface
    if interface is not None and interface.is_open():
        try:
            # Call the ESP32 method and retrieve raw tuple data
            raw_data = interface.getIdJson()

            # Debugging: Log raw data and type
            print(f"Raw data received: {raw_data}")
            print(f"Type of raw data: {type(raw_data)}")

            # Check if raw_data is a tuple with expected fields
            if isinstance(raw_data, tuple) and len(raw_data) == 2:
                board_uuid = raw_data[0].decode("utf-8") if isinstance(raw_data[0], bytes) else raw_data[0]
                git_version = raw_data[1].decode("utf-8") if isinstance(raw_data[1], bytes) else raw_data[1]

                # Return the structured JSON response
                return {
                    "board_uuid": board_uuid,
                    "git_version": git_version,
                }

            # Handle unexpected data format
            print("Unexpected tuple format or size.")
            return {"error": "Unexpected data format received from ESP32"}

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
