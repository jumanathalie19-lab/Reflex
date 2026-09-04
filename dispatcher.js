async function loadOpenDeliveries() {
    const container = document.getElementById("deliveries");
    container.innerHTML = "<p>Loading...</p>";

    try {
        const [deliveriesRes, ridersRes] = await Promise.all([
            fetch("/deliveries"),
            fetch("/riders")
        ]);
        const deliveries = await deliveriesRes.json();
        const riders = await ridersRes.json();

        renderDeliveries(deliveries, riders);
    } catch (error) {
        container.innerHTML = "<p class='error'>Unable to reach the server.</p>";
    }
}

function renderDeliveries(deliveries, riders) {
    const container = document.getElementById("deliveries");
    container.innerHTML = "";

    if (deliveries.length === 0) {
        container.innerHTML = "<p class='empty-hint'>No open deliveries right now.</p>";
        return;
    }

    const riderOptions = riders
        .map(r => `<option value="${r.user_id}">${r.name}</option>`)
        .join("");

    deliveries.forEach(delivery => {
        const item = document.createElement("div");
        item.className = "delivery";
        item.innerHTML = `
            <strong>Delivery #${delivery.delivery_id}</strong>
            <p>Customer: ${delivery.customer_name}</p>
            <p>Address: ${delivery.delivery_address}</p>
            <p>Item: ${delivery.item_description}</p>
            <div class="assign-row">
                <select id="rider-select-${delivery.delivery_id}">
                    <option value="">Choose a rider...</option>
                    ${riderOptions}
                </select>
                <button onclick="assignDelivery(${delivery.delivery_id})">Assign</button>
            </div>
            <p id="result-${delivery.delivery_id}" class="result"></p>
        `;
        container.appendChild(item);
    });
}

async function assignDelivery(deliveryId) {
    const dispatcherId = document.getElementById("dispatcherIdInput").value.trim();
    const riderId = document.getElementById(`rider-select-${deliveryId}`).value;
    const resultEl = document.getElementById(`result-${deliveryId}`);

    if (!dispatcherId) {
        resultEl.textContent = "Enter your Dispatcher ID first.";
        return;
    }
    if (!riderId) {
        resultEl.textContent = "Choose a rider first.";
        return;
    }

    resultEl.textContent = "Assigning...";

    try {
        const response = await fetch(`/deliveries/${deliveryId}/assign`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                rider_id: parseInt(riderId, 10),
                dispatcher_id: parseInt(dispatcherId, 10)
            })
        });
        const data = await response.json();

        if (!response.ok) {
            resultEl.textContent = `Failed: ${data.error}`;
            return;
        }

        loadOpenDeliveries(); // refresh — this delivery leaves the open list
    } catch (error) {
        resultEl.textContent = "Unable to reach the server.";
    }
}