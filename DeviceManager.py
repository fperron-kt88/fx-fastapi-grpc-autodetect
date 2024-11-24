import json
from simple_rpc import Interface


class DeviceManager:
    def __init__(self, serial_port, baud_rate):
        """
        Initialize the device manager with the serial interface.
        """
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.interface = None

    def connect(self):
        """
        Connect to the device via the serial interface.
        """
        try:
            print("Initializing Interface...")
            self.interface = Interface(self.serial_port, self.baud_rate)
            if not self.interface.is_open:
                raise RuntimeError("Failed to open interface.")
            print(f"Connected to {self.serial_port}")
        except Exception as e:
            print(f"Error initializing Interface: {e}")
            self.interface = None
            raise

    def disconnect(self):
        """
        Disconnect from the device.
        """
        if self.interface and self.interface.is_open:
            print("Closing interface...")
            self.interface.close()

    def is_connected(self):
        """
        Check if the device is connected.
        """
        return self.interface is not None and self.interface.is_open

    def get_device_id(self):
        """
        Fetch unique identification data from the device.
        """
        if not self.is_connected():
            return {"error": "Interface not available"}

        try:
            raw_data = self.interface.getDeviceId()

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
                return {
                    field: (
                        value.decode("utf-8") if isinstance(value, bytes) else value
                    )
                    for field, value in zip(field_names, raw_data)
                }

            print("Unexpected tuple format or size.")
            return {"error": "Unexpected data format"}
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}
