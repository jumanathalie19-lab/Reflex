let currentRiderId = null;

const API = "/api";


// ============================================================
// LOAD RIDER DELIVERIES
// ============================================================

async function loadMyDeliveries() {

    const input =
        document.getElementById("riderIdInput");

    const container =
        document.getElementById("deliveries");

    const riderId =
        input.value.trim();


    if (!riderId) {

        container.innerHTML =
            "<p class='error'>Enter a Rider ID first.</p>";

        return;
    }


    currentRiderId = Number(riderId);

    container.innerHTML =
        "<p>Loading...</p>";


    try {

        const response = await fetch(
            `${API}/deliveries/mine?rider_id=${encodeURIComponent(riderId)}&status=active`
        );


        const deliveries =
            await response.json();


        if (!response.ok) {

            container.innerHTML = `
                <p class="error">
                    ${escapeHtml(
                        deliveries.error ||
                        "Could not load deliveries."
                    )}
                </p>
            `;

            return;
        }


        renderDeliveries(deliveries);


    } catch (error) {

        console.error(
            "Load rider deliveries error:",
            error
        );

        container.innerHTML =
            "<p class='error'>Unable to reach the server.</p>";
    }
}


// ============================================================
// RENDER DELIVERIES
// ============================================================

function renderDeliveries(deliveries) {

    const container =
        document.getElementById("deliveries");

    container.innerHTML = "";


    if (!deliveries || deliveries.length === 0) {

        container.innerHTML =
            "<p class='empty-hint'>No active deliveries right now.</p>";

        return;
    }


    deliveries.forEach(delivery => {

        const item =
            document.createElement("div");

        item.className = "delivery";


        item.innerHTML = `

            <strong>
                Delivery #${delivery.delivery_id}
            </strong>

            <p>
                Customer:
                ${escapeHtml(delivery.customer_name)}
            </p>

            <p>
                Phone:
                ${escapeHtml(delivery.customer_phone)}
            </p>

            <p>
                Address:
                ${escapeHtml(delivery.delivery_address)}
            </p>

            <p>
                Item:
                ${escapeHtml(delivery.item_description)}
            </p>

            <p>
                Status:
                <span class="status-badge">
                    ${escapeHtml(delivery.status)}
                </span>
            </p>

            ${renderActionForStatus(delivery)}

            <p
                id="result-${delivery.delivery_id}"
                class="result"
            ></p>
        `;


        container.appendChild(item);
    });
}


// ============================================================
// ACTION BASED ON DELIVERY STATUS
// ============================================================

function renderActionForStatus(delivery) {

    // --------------------------------------------------------
    // ASSIGNED → PICKED_UP
    // --------------------------------------------------------

    if (delivery.status === "ASSIGNED") {

        return `
            <button
                onclick="markPickedUp(${delivery.delivery_id})"
            >
                Mark as Picked Up
            </button>
        `;
    }


    // --------------------------------------------------------
    // PICKED_UP → QR CONFIRMATION
    // --------------------------------------------------------

    if (delivery.status === "PICKED_UP") {

        return `
            <div class="scan-row">

                <input
                    type="text"
                    id="qr-input-${delivery.delivery_id}"
                    placeholder="Enter scanned QR code"
                >

                <button
                    onclick="scanConfirm(${delivery.delivery_id})"
                >
                    Confirm Delivery
                </button>

            </div>
        `;
    }


    return "";
}


// ============================================================
// MARK PICKED UP
// ============================================================

async function markPickedUp(deliveryId) {

    const resultEl =
        document.getElementById(
            `result-${deliveryId}`
        );


    resultEl.textContent =
        "Updating delivery...";


    try {

        const response = await fetch(
            `${API}/deliveries/${deliveryId}/status`,
            {
                method: "PATCH",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    rider_id: currentRiderId,
                    status: "PICKED_UP"
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            resultEl.textContent =
                `Failed: ${
                    data.error ||
                    "Could not update delivery."
                }`;

            return;
        }


        resultEl.textContent =
            "Delivery marked as picked up.";


        // Refresh after a short moment
        setTimeout(
            loadMyDeliveries,
            500
        );


    } catch (error) {

        console.error(
            "Pick-up error:",
            error
        );

        resultEl.textContent =
            "Unable to reach the server.";
    }
}


// ============================================================
// QR CONFIRMATION
// ============================================================

async function scanConfirm(deliveryId) {

    const resultEl =
        document.getElementById(
            `result-${deliveryId}`
        );

    const qrInput =
        document.getElementById(
            `qr-input-${deliveryId}`
        );


    const qrCode =
        qrInput.value.trim();


    if (!qrCode) {

        resultEl.textContent =
            "Enter the scanned QR code first.";

        qrInput.focus();

        return;
    }


    resultEl.textContent =
        "Confirming QR code...";


    try {

        const response = await fetch(
            `${API}/deliveries/${deliveryId}/qr-confirm`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    rider_id: currentRiderId,
                    qr_code: qrCode
                })
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            resultEl.textContent =
                `Scan failed: ${
                    data.error ||
                    "Invalid QR code."
                } Please try again.`;

            return;
        }


        resultEl.textContent =
            "Delivery confirmed successfully.";


        // Delivery is now DELIVERED,
        // so it disappears from the active list.

        setTimeout(
            loadMyDeliveries,
            500
        );


    } catch (error) {

        console.error(
            "QR confirmation error:",
            error
        );

        resultEl.textContent =
            "Unable to reach the server.";
    }
}


// ============================================================
// HTML ESCAPING
// ============================================================

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {
        return "";
    }


    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}