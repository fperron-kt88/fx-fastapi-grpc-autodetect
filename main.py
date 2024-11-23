from fastapi import FastAPI
from pydantic import BaseModel
import serial  # PySerial library for serial communication
import json

app = FastAPI()

# Initialize Serial Communication
SERIAL_PORT = "/dev/ttyUSB0"  # Replace with your ESP32's serial port
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except serial.SerialException:
    ser = None
    print(f"Failed to connect to {SERIAL_PORT}. Ensure your ESP32 is connected.")

# Define Pydantic model for parsing responses (example: board UUID and Git version)
class ESP32IdResponse(BaseModel):
    board_uuid: str
    git_version: str


@app.get("/")
async def root():
    """
    Root endpoint for testing the API.
    """
    return {"message": "Welcome to the ESP32 FastAPI interface!"}


@app.get("/get-id", response_model=ESP32IdResponse)
async def get_id():
    """
    Fetch board UUID and Git version from the ESP32.
    """
    if not ser:
        return {"error": "Serial connection not available"}

    # Send a command to the ESP32 to fetch the ID
    command = "getId\n"  # Command must match ESP32's interface
    ser.write(command.encode())  # Send the command over Serial

    # Wait for a response
    response = ser.readline().decode().strip()
    if not response:
        return {"error": "No response from ESP32"}

    # Parse the JSON response from the ESP32
    try:
        data = json.loads(response)
        return data
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from ESP32", "raw_response": response}


@app.post("/send-command")
async def send_command(command: str):
    """
    Send a custom command to the ESP32 and retrieve the response.
    """
    if not ser:
        return {"error": "Serial connection not available"}

    # Send the command to the ESP32
    ser.write((command + "\n").encode())

    # Wait for a response
    response = ser.readline().decode().strip()
    return {"command": command, "response": response}

