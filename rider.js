let currentRiderId = null;

async function loadMyDeliveries() {
    const input = document.getElementById("riderIdInput");
    const container = document.getElementById("deliveries");
    const riderId = input.value.trim();

    if (!riderId) {
        container.innerHTML = "<p class='error'>Enter a Rider ID first.</p>";
        return;
    }

    currentRiderId = riderId;
    container.innerHTML = "<p>Loading...</p>";

    try {
        // Mark's endpoint — deliberately /deliveries/mine, not /deliveries,
        // since that path is already used by the dispatcher's OPEN-deliveries
        // view (see mark_status.py's comment on why this path was chosen).
        const response = await fetch(`/deliveries/mine?rider_id=${encodeURIComponent(riderId)}&status=active`);
        const deliveries = await response.json();

        if (!response.ok) {
            container.innerHTML = `<p class="error">${deliveries.error || "Could not load deliveries."}</p>`;
            return;
        }

        renderDeliveries(deliveries);
    } catch (error) {
        container.innerHTML = "<p class='error'>Unable to reach the server.</p>";
    }
}

function renderDeliveries(deliveries) {
    const container = document.getElementById("deliveries");
    container.innerHTML = "";

    if (deliveries.length === 0) {
        container.innerHTML = "<p class='empty-hint'>No active deliveries right now.</p>";
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
            <p>Status: <span class="status-badge">${delivery.status}</span></p>
            ${renderActionForStatus(delivery)}
            <p id="result-${delivery.delivery_id}" class="result"></p>
        `;
        container.appendChild(item);
    });
}

// Only one action is ever available per delivery — the forward-only
// transition rules mean a delivery is either waiting to be picked up
// or waiting to be scanned, never both, never neither.
function renderActionForStatus(delivery) {
    if (delivery.status === "ASSIGNED") {
        return `<button onclick="markPickedUp(${delivery.delivery_id})">Mark as Picked Up</button>`;
    }

    if (delivery.status === "PICKED_UP") {
        return `
            <div class="scan-row">
                <input type="text" id="qr-input-${delivery.delivery_id}" placeholder="Scanned QR code">
                <button onclick="scanConfirm(${delivery.delivery_id})">Scan to Confirm Delivery</button>
            </div>
        `;
    }

    return "";
}

async function markPickedUp(deliveryId) {
    const resultEl = document.getElementById(`result-${deliveryId}`);
    resultEl.textContent = "Updating...";

    try {
        // Mark's endpoint.
        const response = await fetch(`/deliveries/${deliveryId}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rider_id: parseInt(currentRiderId, 10), status: "PICKED_UP" })
        });
        const data = await response.json();

        if (!response.ok) {
            resultEl.textContent = `Failed: ${data.error}`;
            return;
        }

        loadMyDeliveries(); // refresh so the scan action appears
    } catch (error) {
        resultEl.textContent = "Unable to reach the server.";
    }
}

async function scanConfirm(deliveryId) {
    const resultEl = document.getElementById(`result-${deliveryId}`);
    const qrInput = document.getElementById(`qr-input-${deliveryId}`);
    const qrCode = qrInput.value.trim();

    if (!qrCode) {
        resultEl.textContent = "Enter the scanned QR code first.";
        return;
    }

    resultEl.textContent = "Confirming...";

    try {
        // George's endpoint.
        const response = await fetch(`/deliveries/${deliveryId}/qr-confirm`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rider_id: parseInt(currentRiderId, 10), qr_code: qrCode })
        });
        const data = await response.json();

        if (!response.ok) {
            // A failed scan is logged server-side but does NOT advance
            // status — this matches George's doc: the rider stays at
            // PICKED_UP and is prompted to rescan.
            resultEl.textContent = `Scan failed: ${data.error}. Please rescan.`;
            return;
        }

        resultEl.textContent = "Delivered!";
        loadMyDeliveries(); // refresh — this delivery will now disappear
                            // from the active list, since DELIVERED is
                            // no longer "active" per Mark's filter
    } catch (error) {
        resultEl.textContent = "Unable to reach the server.";
    }
}