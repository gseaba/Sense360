from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse 
import asyncio
import math
import time 

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="dashboard/static"),
    name="static"
)

@app.get("/")
async def index():
    return FileResponse("dashboard/static/index.html")


def get_test_data():
    """Temporary simulated controller data."""

    t = time.time()

    return {
        "timestamp": t,
        "objects": [
            {
                "angle": 0,
                "distance": 0.5
            },
            {
                "angle": 40,
                "distance": 0.8 + 0.1 * math.sin(t)
            },
            {
                "angle": 90,
                "distance": 1.1
            },
            {
                "angle": 180,
                "distance": 0.7
            }
        ]
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = get_test_data()

            await websocket.send_json(data)

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print("Dashboard client disconnected")