from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import serial
import json
import uvicorn
import asyncio
from contextlib import asynccontextmanager

# Initialize Serial Communication
SERIAL_PORT = "/dev/ttyUSB0"  # Replace with your ESP32's serial port
BAUD_RATE = 115200
ser = None  # Global variable for serial connection


# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT}")
    except serial.SerialException:
        ser = None
        print(f"Failed to connect to {SERIAL_PORT}. Ensure your ESP32 is connected.")

    yield  # Application runs here

    if ser and ser.is_open:
        print("Closing serial connection...")
        ser.close()


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
    if not ser:
        return {"error": "Serial connection not available"}

    # Send the `getId` command
    command = "getId\n"
    ser.write(command.encode())  # Send the command over Serial

    # Wait for a response
    response = ser.readline().decode().strip()
    if not response:
        return {"error": "No response from ESP32"}

    # Return the raw string response
    return {"id_string": response}


@app.get("/get-id-json")
async def get_id_json():
    """
    Fetch board UUID and Git version as JSON from the ESP32.
    """
    if not ser:
        return {"error": "Serial connection not available"}

    # Send the `getIdJson` command
    command = "getIdJson\n"
    ser.write(command.encode())  # Send the command over Serial

    # Wait for a response
    response = ser.readline().decode().strip()
    if not response:
        return {
            "board_uuid": "unknown",
            "git_version": "unknown",
            "error": "No response from ESP32",
        }

    # Parse the JSON response
    try:
        data = json.loads(response)
        # Validate keys to ensure they match the model
        board_uuid = data.get("board_uuid", "unknown")
        git_version = data.get("git_version", "unknown")
        return {"board_uuid": board_uuid, "git_version": git_version}
    except json.JSONDecodeError:
        return {
            "board_uuid": "unknown",
            "git_version": "unknown",
            "error": "Invalid JSON response from ESP32",
            "raw_response": response,
        }


# Main entry point for running the server
if __name__ == "__main__":

    def handle_exit(sig, frame):
        print("Received signal to terminate, shutting down...")
        asyncio.get_event_loop().stop()

    # Register signal handlers
    import signal

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
