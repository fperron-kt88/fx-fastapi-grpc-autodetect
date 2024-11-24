import json
import time
from simple_rpc import Interface
import serial.tools.list_ports
from threading import Lock


class DeviceManager:
    def __init__(self, baud_rate=115200, max_retries=5, retry_delay=2, connection_timeout=10):
        """
        Initialize the device manager with connection settings.
        """
        self.baud_rate = baud_rate
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection_timeout = connection_timeout
        self.interface = None
        self.device_uuid = None
        self.last_known_port = None
        self.lock = Lock()  # Ensure thread-safe reconnection

    def scan_ports(self):
        """
        Scan for available serial ports, filtering out irrelevant entries.
        """
        all_ports = [port.device for port in serial.tools.list_ports.comports()]
        valid_ports = [port for port in all_ports if "ttyUSB" in port]
        print(f"Filtered valid ports: {valid_ports}")
        return valid_ports

    def _fetch_device_uuid(self):
        """
        Fetch the UUID from the connected device.
        """
        if not self.interface or not self.interface.is_open:
            raise RuntimeError("Cannot fetch UUID: Interface is not connected.")

        raw_data = self.interface.getDeviceId()
        if not (isinstance(raw_data, tuple) and len(raw_data) > 0):
            raise RuntimeError("Invalid data format received from the device.")

        return raw_data[0].decode("utf-8") if isinstance(raw_data[0], bytes) else raw_data[0]

    def _validate_or_set_uuid(self):
        """
        Validate the device UUID or set it if it's the first connection.
        """
        current_uuid = self._fetch_device_uuid()
        print(f"Device UUID: {current_uuid}")

        if self.device_uuid is None:
            print(f"Accepting new UUID: {current_uuid}")
            self.device_uuid = current_uuid
        elif self.device_uuid != current_uuid:
            raise RuntimeError(
                f"Device UUID mismatch: expected {self.device_uuid}, got {current_uuid}"
            )

    def connect(self):
        """
        Attempt to connect to the device by scanning ports and validating UUID.
        """
        retries = 0
        start_time = time.time()

        while retries < self.max_retries:
            available_ports = self.scan_ports()
            print(f"Available ports: {available_ports}")

            for port in available_ports:
                try:
                    print(f"Attempting to connect to port: {port}, and baud: {self.baud_rate}...")
                    self.interface = Interface(port, self.baud_rate)
                    if self.interface.is_open:
                        print(f"Connected to {port}")
                        self.last_known_port = port
                        self._validate_or_set_uuid()
                        return  # Successfully connected
                except Exception as e:
                    print(f"Failed to connect on {port}: {e}")

            retries += 1
            elapsed_time = time.time() - start_time
            print(f"Retry {retries}/{self.max_retries} failed. Elapsed time: {elapsed_time:.2f}s")
            if elapsed_time > self.connection_timeout:
                raise RuntimeError(f"Connection timeout exceeded ({self.connection_timeout} seconds). Ports tried: {available_ports}")
            time.sleep(self.retry_delay)

        raise RuntimeError(f"Failed to connect after {self.max_retries} retries.")

    def disconnect(self):
        """
        Disconnect from the device.
        """
        if self.interface and self.interface.is_open:
            print("Closing interface...")
            self.interface.close()
            self.interface = None

    def is_connected(self):
        """
        Check if the device is connected and UUID matches.
        """
        if self.interface and self.interface.is_open:
            try:
                current_uuid = self._fetch_device_uuid()
                if self.device_uuid == current_uuid:
                    return True
                print(f"UUID mismatch: expected {self.device_uuid}, got {current_uuid}")
            except Exception as e:
                print(f"Connection check failed: {e}")

            # Close the interface on failure
            self.disconnect()

        return False

    def reconnect(self):
        """
        Attempt to reconnect to the device after a disconnection.
        """
        with self.lock:  # Ensure thread-safe reconnection
            print("Reconnecting to device...")
            self.disconnect()
            try:
                self.connect()
                print("Reconnection successful.")
            except Exception as e:
                print(f"Reconnection failed: {e}")

    def get_active_interface(self):
        """
        Return the currently active serial interface or attempt to reconnect.
        """
        if self.is_connected():
            return {"active_interface": self.last_known_port}

        try:
            self.reconnect()
            if self.is_connected():
                return {"active_interface": self.last_known_port}
        except Exception as e:
            return {"error": f"Failed to reconnect: {str(e)}"}

        return {"error": "No active interface found"}

    def get_device_id(self):
        """
        Fetch unique identification data from the device.
        """
        if not self.is_connected():
            self.reconnect()

        if not self.is_connected():
            return {"error": "Interface not available"}

        try:
            raw_data = self.interface.getDeviceId()
            field_names = [
                "board_uuid",
                "git_version",
                "api_version",
                "hw_version",
                "device_name",
            ]

            if isinstance(raw_data, tuple) and len(raw_data) == len(field_names):
                return {field: value.decode("utf-8") if isinstance(value, bytes) else value
                        for field, value in zip(field_names, raw_data)}

            return {"error": "Unexpected data format"}
        except Exception as e:
            self.reconnect()
            return {"error": str(e)}

    def clear_uuid(self):
        """
        Clear the stored UUID, allowing a new device to connect.
        """
        print(f"Clearing stored UUID. Previous UUID: {self.device_uuid}")
        self.device_uuid = None

