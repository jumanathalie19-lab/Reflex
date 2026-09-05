async function checkHealth() {
    const result = document.getElementById("health-result");

    try {
        const response = await fetch("/api/health");
        const data = await response.json();

        result.textContent = data.message;
    } catch (error) {
        result.textContent = "Unable to connect to the API.";
    }
}


async function loadDeliveries() {
    const container = document.getElementById("deliveries");

    try {
        const response = await fetch("/api/deliveries");
        const deliveries = await response.json();

        container.innerHTML = "";

        if (deliveries.length === 0) {
            container.innerHTML = "<p>No delivery requests found.</p>";
            return;
        }

        deliveries.forEach(delivery => {
            const item = document.createElement("div");

            item.className = "delivery";

            item.innerHTML = `
                <strong>Delivery #${delivery.delivery_id}</strong>
                <p>Customer: ${delivery.customer_name}</p>
                <p>Address: ${delivery.delivery_address}</p>
                <p>Item: ${delivery.item_description}</p>
                <p>Status: ${delivery.status}</p>
                <p>Rider: ${delivery.rider_name || "Not assigned"}</p>
                ${renderScanButton(delivery)}
            `;

            container.appendChild(item);
        });

    } catch (error) {
        container.innerHTML =
            "<p>Unable to load deliveries.</p>";
    }
}


// Only show the scan button once a delivery is Picked Up —
// before that there's nothing to confirm, after that it's already done.
function renderScanButton(delivery) {
    if (delivery.status !== "Picked Up") {
        return "";
    }

    return `
        <button onclick="scanConfirm(${delivery.delivery_id})">
            Scan to Confirm Delivery
        </button>
        <p id="scan-result-${delivery.delivery_id}"></p>
    `;
}


async function scanConfirm(deliveryId) {
    const resultEl = document.getElementById(`scan-result-${deliveryId}`);

    // No auth yet, so the rider identifies themselves and enters the
    // scanned code manually. This will move behind real auth + a camera
    // scan later — see trade-off log.
    const riderId = prompt("Enter your Rider ID:");
    const qrCode = prompt("Enter the QR code you just scanned:");

    if (!riderId || !qrCode) {
        resultEl.textContent = "Rider ID and QR code are both required.";
        return;
    }

    try {
        const response = await fetch(`/api/deliveries/${deliveryId}/qr-confirm`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                rider_id: parseInt(riderId, 10),
                qr_code: qrCode
            })
        });

        const data = await response.json();

        if (!response.ok) {
            resultEl.textContent = `Failed: ${data.error}`;
            return;
        }

        resultEl.textContent = "Delivery confirmed!";
        loadDeliveries(); // refresh the list so status updates everywhere
    } catch (error) {
        resultEl.textContent = "Unable to reach the server.";
    }
}
