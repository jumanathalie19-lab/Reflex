const API = "/api";

/*
|--------------------------------------------------------------------------
| Dispatcher ID
|--------------------------------------------------------------------------
| For now there is no login system, so we use a dispatcher ID.
| Change this to an actual Dispatcher user ID in your database.
|--------------------------------------------------------------------------
*/

const DISPATCHER_ID = 2;

const deliveriesContainer = document.getElementById("deliveries");
const ridersContainer = document.getElementById("riders");
const deliveryCount = document.getElementById("deliveryCount");
const riderCount = document.getElementById("riderCount");
const message = document.getElementById("message");
const refreshBtn = document.getElementById("refreshBtn");


function showMessage(text, type = "") {
    message.textContent = text;
    message.className = type;
}


/*
|--------------------------------------------------------------------------
| Load dispatcher data
|--------------------------------------------------------------------------
*/

async function loadDispatcherData() {

    refreshBtn.disabled = true;
    refreshBtn.textContent = "Refreshing...";

    try {

        await Promise.all([
            loadOpenDeliveries(),
            loadRiders()
        ]);

    } catch (error) {

        console.error("Dispatcher loading error:", error);

        showMessage(
            "Could not load dispatcher data.",
            "error"
        );

    } finally {

        refreshBtn.disabled = false;
        refreshBtn.textContent = "Refresh";
    }
}


/*
|--------------------------------------------------------------------------
| Load OPEN deliveries
|--------------------------------------------------------------------------
*/

async function loadOpenDeliveries() {

    deliveriesContainer.innerHTML =
        '<p class="empty">Loading deliveries...</p>';

    try {

        const response = await fetch(
            `${API}/deliveries/open`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Failed to load deliveries."
            );
        }

        deliveryCount.textContent = data.length;

        if (data.length === 0) {

            deliveriesContainer.innerHTML = `
                <div class="empty">
                    <h3>No open deliveries</h3>
                    <p>
                        New retailer requests will appear here.
                    </p>
                </div>
            `;

            return;
        }

        deliveriesContainer.innerHTML = data.map(delivery => {

            return `
                <div class="delivery-card">

                    <div class="delivery-header">

                        <div>
                            <h3>
                                Delivery #${delivery.delivery_id}
                            </h3>

                            <span class="status">
                                ${delivery.status}
                            </span>
                        </div>

                    </div>

                    <div class="delivery-details">

                        <p>
                            <strong>Customer:</strong>
                            ${escapeHtml(delivery.customer_name)}
                        </p>

                        <p>
                            <strong>Phone:</strong>
                            ${escapeHtml(delivery.customer_phone)}
                        </p>

                        <p>
                            <strong>Address:</strong>
                            ${escapeHtml(delivery.delivery_address)}
                        </p>

                        <p>
                            <strong>Item:</strong>
                            ${escapeHtml(delivery.item_description)}
                        </p>

                        <p>
                            <strong>Retailer ID:</strong>
                            ${delivery.retailer_id}
                        </p>

                    </div>

                    <div class="assign-row">

                        <select
                            id="rider-${delivery.delivery_id}"
                        >
                            <option value="">
                                Select Rider
                            </option>
                        </select>

                        <button
                            onclick="assignDelivery(${delivery.delivery_id})"
                        >
                            Assign Rider
                        </button>

                    </div>

                </div>
            `;

        }).join("");

        /*
        | Populate every rider dropdown
        */
        populateRiderDropdowns();

    } catch (error) {

        console.error(error);

        deliveriesContainer.innerHTML = `
            <div class="error-box">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}


/*
|--------------------------------------------------------------------------
| Load riders
|--------------------------------------------------------------------------
*/

let riders = [];

async function loadRiders() {

    ridersContainer.innerHTML =
        '<p class="empty">Loading riders...</p>';

    try {

        const response = await fetch(
            `${API}/riders`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Failed to load riders."
            );
        }

        riders = data;

        riderCount.textContent = data.length;

        if (data.length === 0) {

            ridersContainer.innerHTML = `
                <div class="empty">
                    <h3>No riders found</h3>
                    <p>
                        Add users with the Rider role first.
                    </p>
                </div>
            `;

            return;
        }

        ridersContainer.innerHTML = data.map(rider => {

            return `
                <div class="rider-card">

                    <div class="rider-avatar">
                        ${escapeHtml(
                            rider.name
                                ? rider.name.charAt(0).toUpperCase()
                                : "R"
                        )}
                    </div>

                    <div class="rider-info">

                        <h3>
                            ${escapeHtml(rider.name)}
                        </h3>

                        <p>
                            Rider ID: ${rider.user_id}
                        </p>

                        <p>
                            ${escapeHtml(rider.phone || "No phone")}
                        </p>

                    </div>

                </div>
            `;

        }).join("");

        populateRiderDropdowns();

    } catch (error) {

        console.error(error);

        ridersContainer.innerHTML = `
            <div class="error-box">
                ${escapeHtml(error.message)}
            </div>
        `;
    }
}


/*
|--------------------------------------------------------------------------
| Populate rider dropdowns
|--------------------------------------------------------------------------
*/

function populateRiderDropdowns() {

    if (!riders.length) {
        return;
    }

    riders.forEach(rider => {

        const selects = document.querySelectorAll(
            "select[id^='rider-']"
        );

        selects.forEach(select => {

            /*
            Don't add duplicate options
            */
            if (
                select.querySelector(
                    `option[value="${rider.user_id}"]`
                )
            ) {
                return;
            }

            const option = document.createElement("option");

            option.value = rider.user_id;

            option.textContent =
                `${rider.name} — ID ${rider.user_id}`;

            select.appendChild(option);
        });

    });
}


/*
|--------------------------------------------------------------------------
| Assign delivery
|--------------------------------------------------------------------------
*/

async function assignDelivery(deliveryId) {

    const select =
        document.getElementById(`rider-${deliveryId}`);

    const riderId = Number(select.value);

    if (!riderId) {

        showMessage(
            "Please select a rider first.",
            "error"
        );

        return;
    }

    const button =
        select.parentElement.querySelector("button");

    button.disabled = true;
    button.textContent = "Assigning...";

    try {

        const response = await fetch(
            `${API}/deliveries/${deliveryId}/assign`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    rider_id: riderId,
                    dispatcher_id: DISPATCHER_ID
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.error || "Failed to assign delivery."
            );
        }

        showMessage(
            `Delivery #${deliveryId} assigned successfully.`,
            "success"
        );

        /*
        | Reload the open deliveries.
        | The assigned delivery should disappear because
        | its status is now ASSIGNED.
        */
        await loadOpenDeliveries();

    } catch (error) {

        console.error("Assignment error:", error);

        showMessage(
            error.message || "Could not assign delivery.",
            "error"
        );

        button.disabled = false;
        button.textContent = "Assign Rider";
    }
}


/*
|--------------------------------------------------------------------------
| Basic HTML escaping
|--------------------------------------------------------------------------
*/

function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


/*
|--------------------------------------------------------------------------
| Initial load
|--------------------------------------------------------------------------
*/

document.addEventListener(
    "DOMContentLoaded",
    loadDispatcherData
);