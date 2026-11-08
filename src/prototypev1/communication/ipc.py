
import socket
import json


class SensorPublisher:

    def __init__(
        self,
        host="127.0.0.1",
        port=8765
    ):
        self.address = (host, port)

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

    def publish(self, data):
        """Publish a sensor snapshot."""

        try:
            message = json.dumps(data).encode("utf-8")

            self.sock.sendto(
                message,
                self.address
            )

        except OSError:
            # Dashboard communication must not
            # interrupt controller operation.
            pass

    def close(self):
        self.sock.close()
