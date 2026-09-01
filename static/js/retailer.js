const form = document.getElementById("deliveryForm");
const message = document.getElementById("message");

form.addEventListener("submit", async function (event) {

    event.preventDefault();

    const deliveryData = {
        retailer_id: Number(document.getElementById("retailer_id").value),
        customer_name: document.getElementById("customer_name").value,
        customer_phone: document.getElementById("customer_phone").value,
        delivery_address: document.getElementById("delivery_address").value,
        item_description: document.getElementById("item_description").value
    };

    message.textContent = "Submitting delivery request...";

    try {

        const response = await fetch("/api/deliveries", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(deliveryData)
        });

        const result = await response.json();

        if (response.ok) {

            message.textContent =
                "Delivery request submitted successfully!";

            form.reset();

            document.getElementById("retailer_id").value = 1;

        } else {

            message.textContent =
                result.message || "Failed to submit delivery request.";

        }

    } catch (error) {

        console.error(error);

        message.textContent =
            "Could not connect to the Reflex server.";
    }
});
