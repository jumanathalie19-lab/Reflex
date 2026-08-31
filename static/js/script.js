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
            `;

            container.appendChild(item);
        });

    } catch (error) {
        container.innerHTML =
            "<p>Unable to load deliveries.</p>";
    }
}