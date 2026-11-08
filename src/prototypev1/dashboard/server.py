
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from contextlib import asynccontextmanager
from pathlib import Path

import asyncio
import json


# Latest controller snapshot
latest_state = None

# Connected browser clients
clients = set()


async def broadcast(data):

    disconnected = set()

    for client in clients:
        try:
            await client.send_json(data)

        except Exception:
            disconnected.add(client)

    clients.difference_update(disconnected)


class DashboardUDPProtocol(asyncio.DatagramProtocol):

    def datagram_received(self, data, address):

        global latest_state

        try:
            latest_state = json.loads(data.decode("utf-8"))

            # Forward the snapshot to browser clients
            asyncio.create_task(
                broadcast(latest_state)
            )

        except (ValueError, UnicodeDecodeError):
            print("Invalid controller message")


@asynccontextmanager
async def lifespan(app: FastAPI):

    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_datagram_endpoint(
        DashboardUDPProtocol,
        local_addr=("127.0.0.1", 8765)
    )

    print("Controller IPC listening on UDP port 8765")

    yield

    transport.close()


app = FastAPI(lifespan=lifespan)


# Static dashboard files
STATIC_DIR = Path(__file__).parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


@app.get("/")
async def index():

    return FileResponse(STATIC_DIR / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    clients.add(websocket)

    try:

        # Immediately send the latest available snapshot
        if latest_state is not None:
            await websocket.send_json(latest_state)

        # Keep connection alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass

    finally:
        clients.discard(websocket)
