
const svg = document.getElementById("map");
const grid = document.getElementById("grid");
const objects = document.getElementById("objects");

const connection = document.getElementById("connection");
const objectList = document.getElementById("object-list");

const center = 300;
const scale = 180;       // 1 meter = 180 pixels
const maxDistance = 1.5;


// Draw the spatial grid
function drawGrid() {

    // Distance rings
    for (let d = 0.5; d <= maxDistance; d += 0.5) {

        const radius = d * scale;

        const circle = document.createElementNS(
            "http://www.w3.org/2000/svg", "circle"
        );

        circle.setAttribute("cx", center);
        circle.setAttribute("cy", center);
        circle.setAttribute("r", radius);
        circle.setAttribute("class", "grid-ring");

        grid.appendChild(circle);

        const label = document.createElementNS(
            "http://www.w3.org/2000/svg", "text"
        );

        label.setAttribute("x", center + 5);
        label.setAttribute("y", center - radius + 15);
        label.setAttribute("class", "grid-label");
        label.textContent = `${d.toFixed(1)} m`;

        grid.appendChild(label);
    }

    // 18 directional sectors
    for (let angle = 0; angle < 360; angle += 20) {

        const rad = angle * Math.PI / 180;

        const x = center + maxDistance * scale * Math.sin(rad);
        const y = center - maxDistance * scale * Math.cos(rad);

        const line = document.createElementNS(
            "http://www.w3.org/2000/svg", "line"
        );

        line.setAttribute("x1", center);
        line.setAttribute("y1", center);
        line.setAttribute("x2", x);
        line.setAttribute("y2", y);
        line.setAttribute("class", "grid-line");

        grid.appendChild(line);
    }
}


// Update detected objects
function updateDashboard(data) {

    objects.innerHTML = "";
    objectList.innerHTML = "";

    data.objects.forEach((obj, index) => {

        const rad = obj.angle * Math.PI / 180;

        const x = center +
                  obj.distance * scale * Math.sin(rad);

        const y = center -
                  obj.distance * scale * Math.cos(rad);

        // Draw object
        const circle = document.createElementNS(
            "http://www.w3.org/2000/svg", "circle"
        );

        circle.setAttribute("cx", x);
        circle.setAttribute("cy", y);
        circle.setAttribute("r", 9);
        circle.setAttribute("class", "object");

        objects.appendChild(circle);

        // Add reading to sidebar
        const reading = document.createElement("div");

        reading.className = "reading";

        reading.textContent =
            `Object ${index + 1}: ` +
            `${obj.angle}° | ${obj.distance.toFixed(2)} m`;

        objectList.appendChild(reading);
    });
}


// Establish WebSocket connection
function connect() {

    const protocol =
        window.location.protocol === "https:" ? "wss:" : "ws:";

    const ws = new WebSocket(
        `${protocol}//${window.location.host}/ws`
    );

    ws.onopen = () => {
        connection.textContent = "Connected";
        connection.style.color = "#4ade80";
    };

    ws.onmessage = (event) => {

        const data = JSON.parse(event.data);

        updateDashboard(data);
    };

    ws.onclose = () => {

        connection.textContent = "Disconnected";
        connection.style.color = "#ef4444";

        setTimeout(connect, 2000);
    };

    ws.onerror = () => {
        ws.close();
    };
}


drawGrid();
connect();
