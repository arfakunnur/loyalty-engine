/**
 * ==========================================================================
 * JavaScript Core Logic for Loyalty Points Engine Frontend
 * Connects HTML templates to Flask REST APIs using modern Fetch API.
 * Uses relative path calls since templates are served by Flask.
 * ==========================================================================
 */

// Set API Base URL to the current server origin (e.g., http://localhost:5000)
const API_BASE_URL = window.location.origin;

// Run setup code once the page finishes loading
document.addEventListener("DOMContentLoaded", () => {
    // Read the current path to decide which page logic to load
    const path = window.location.pathname;

    // Highlight current page in navigation
    highlightActiveNav(path);

    if (path === "/" || path === "/index.html") {
        loadDashboardStats();
    } else if (path === "/create-event") {
        setupEventIngestion();
    } else if (path === "/balance") {
        setupBalanceChecker();
    } else if (path === "/rewards") {
        setupRewardsCatalog();
    } else if (path === "/ledger") {
        setupLedgerViewer();
    } else if (path === "/reversal") {
        setupReversalProcessor();
    }
});

/**
 * Navigation utility: sets active navigation link
 */
function highlightActiveNav(currentPath) {
    const navLinks = document.querySelectorAll(".nav-menu a");
    navLinks.forEach(link => {
        const href = link.getAttribute("href");
        // Matches root "/" or exact path matches
        if (href === currentPath || (currentPath === "/index.html" && href === "/")) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
}

/**
 * Display helper: Renders custom alert panels in form grids
 */
function showAlert(elementId, message, type = "success") {
    const container = document.getElementById(elementId);
    if (!container) return;

    container.innerHTML = `
        <div class="alert alert-${type}">
            <span>${type === 'success' ? '✓' : type === 'error' ? '⚠' : 'ℹ'}</span>
            <div>${message}</div>
        </div>
    `;
}

/**
 * Formatter: Parses ISO timestamps to localized strings
 */
function formatTimestamp(isoString) {
    if (!isoString) return "-";
    try {
        const date = new Date(isoString);
        return date.toLocaleString();
    } catch (e) {
        return isoString;
    }
}

/**
 * Generator: Utility to build randomized Event IDs for testing
 */
function generateRandomUUID() {
    return 'evt-' + Math.random().toString(36).substring(2, 11).toUpperCase() + 
           '-' + Math.floor(1000 + Math.random() * 9000);
}


/* ==========================================================================
   1. Dashboard Page (/)
   ========================================================================== */
async function loadDashboardStats() {
    const balanceVal = document.getElementById("stat-balance");
    const eventsVal = document.getElementById("stat-events");
    const redemptionsVal = document.getElementById("stat-redemptions");
    const statusContainer = document.getElementById("dashboard-status");

    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
        const data = await response.json();
        
        if (balanceVal) balanceVal.innerText = data.total_balance.toLocaleString();
        if (eventsVal) eventsVal.innerText = data.total_events_processed.toLocaleString();
        if (redemptionsVal) redemptionsVal.innerText = data.total_redemptions.toLocaleString();
    } catch (error) {
        console.error("Dashboard stats load error:", error);
        showAlert("dashboard-status", "Could not load stats: Server offline.", "error");
        if (balanceVal) balanceVal.innerText = "0";
        if (eventsVal) eventsVal.innerText = "0";
        if (redemptionsVal) redemptionsVal.innerText = "0";
    }
}


/* ==========================================================================
   2. Ingest Event Page (/create-event)
   ========================================================================== */
function setupEventIngestion() {
    const eventForm = document.getElementById("event-form");
    const uuidBtn = document.getElementById("btn-generate-uuid");
    const eventIdInput = document.getElementById("event_id");

    if (eventIdInput) eventIdInput.value = generateRandomUUID();

    if (uuidBtn && eventIdInput) {
        uuidBtn.addEventListener("click", () => {
            eventIdInput.value = generateRandomUUID();
        });
    }

    if (eventForm) {
        eventForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const eventId = document.getElementById("event_id").value.trim();
            const userId = document.getElementById("user_id").value.trim();
            const eventType = document.getElementById("event_type").value;
            const amount = parseFloat(document.getElementById("amount").value);
            const alertElement = "event-alert-container";
            
            if (!eventId || !userId || isNaN(amount)) {
                showAlert(alertElement, "Please input all required parameters.", "error");
                return;
            }

            const timestamp = new Date().toISOString();
            const payload = { event_id: eventId, user_id: userId, event_type: eventType, amount: amount, timestamp: timestamp };

            try {
                const response = await fetch(`${API_BASE_URL}/events`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();

                if (response.status === 201) {
                    showAlert(alertElement, `<strong>Success!</strong> Awarded <strong>${result.points_awarded}</strong> points to user '${result.user_id}'.`, "success");
                    eventIdInput.value = generateRandomUUID(); // Roll ID for next event
                } else if (response.status === 409) {
                    showAlert(alertElement, `<strong>Conflict:</strong> ${result.error}`, "error");
                } else {
                    showAlert(alertElement, `<strong>Error:</strong> ${result.error || "Inbound ingest failed."}`, "error");
                }
            } catch (err) {
                showAlert(alertElement, "Connection failed. Backend server offline.", "error");
            }
        });
    }
}


/* ==========================================================================
   3. Balance Page (/balance)
   ========================================================================== */
function setupBalanceChecker() {
    const balanceForm = document.getElementById("balance-form");
    const balanceVal = document.getElementById("balance-value");
    const balanceUserLabel = document.getElementById("balance-user");
    const balanceResultDiv = document.getElementById("balance-result");

    if (balanceForm) {
        balanceForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const userId = document.getElementById("user_id").value.trim();
            const alertElement = "balance-alert-container";
            
            if (!userId) {
                showAlert(alertElement, "User ID is required.", "error");
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/balance/${userId}`);
                if (!response.ok) throw new Error("API Connection Failed");
                const data = await response.json();

                if (balanceVal) balanceVal.innerText = data.balance.toLocaleString();
                if (balanceUserLabel) balanceUserLabel.innerText = data.user_id;
                if (balanceResultDiv) balanceResultDiv.style.display = "block";
                document.getElementById(alertElement).innerHTML = ""; // Clear errors
            } catch (err) {
                showAlert(alertElement, "Failed to connect to backend server.", "error");
            }
        });
    }
}


/* ==========================================================================
   4. Rewards Page (/rewards)
   ========================================================================== */
async function setupRewardsCatalog() {
    const rewardsGrid = document.getElementById("rewards-grid");
    const redeemAlert = "redeem-alert-container";
    
    let catalog = [
        { name: "Coffee Coupon", points_required: 100, icon: "☕" },
        { name: "Movie Ticket", points_required: 300, icon: "🎟️" },
        { name: "Gift Card", points_required: 500, icon: "🎁" }
    ];

    try {
        const response = await fetch(`${API_BASE_URL}/rewards`);
        if (response.ok) {
            const data = await response.json();
            if (data.catalog && data.catalog.length > 0) {
                catalog = data.catalog.map(item => {
                    let icon = "⭐";
                    if (item.name.toLowerCase().includes("coffee")) icon = "☕";
                    else if (item.name.toLowerCase().includes("movie")) icon = "🎟️";
                    else if (item.name.toLowerCase().includes("gift")) icon = "🎁";
                    return { ...item, icon };
                });
            }
        }
    } catch (err) {
        console.warn("Could not query rewards from API. Falling back to default list.");
    }

    if (rewardsGrid) {
        rewardsGrid.innerHTML = "";
        catalog.forEach(item => {
            const card = document.createElement("div");
            card.className = "reward-item";
            card.innerHTML = `
                <div>
                    <div class="reward-icon">${item.icon}</div>
                    <div class="reward-name">${item.name}</div>
                    <div class="reward-cost">${item.points_required} <span>Points</span></div>
                </div>
                <button class="btn btn-redeem-item" data-reward="${item.name}">Redeem Reward</button>
            `;
            rewardsGrid.appendChild(card);
        });

        const redeemButtons = document.querySelectorAll(".btn-redeem-item");
        redeemButtons.forEach(btn => {
            btn.addEventListener("click", async (e) => {
                const rewardName = e.target.getAttribute("data-reward");
                const userIdInput = document.getElementById("user_id");
                
                if (!userIdInput) return;
                const userId = userIdInput.value.trim();

                if (!userId) {
                    showAlert(redeemAlert, "Please input a User ID first.", "error");
                    userIdInput.focus();
                    return;
                }

                try {
                    const response = await fetch(`${API_BASE_URL}/redeem`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ user_id: userId, reward_name: rewardName })
                    });
                    const data = await response.json();

                    if (response.status === 200) {
                        showAlert(redeemAlert, `<strong>Redeemed!</strong> Spent <strong>${data.points_spent}</strong> points on ${data.reward}. Remaining balance: <strong>${data.remaining_balance}</strong> points.`, "success");
                    } else if (response.status === 402) {
                        showAlert(redeemAlert, `<strong>Denied:</strong> ${data.error}`, "error");
                    } else {
                        showAlert(redeemAlert, `<strong>Error:</strong> ${data.error || "Claim failed."}`, "error");
                    }
                } catch (err) {
                    showAlert(redeemAlert, "Communication with server failed.", "error");
                }
            });
        });
    }
}


/* ==========================================================================
   5. Ledger Page (/ledger)
   ========================================================================== */
function setupLedgerViewer() {
    const ledgerForm = document.getElementById("ledger-form");
    const tableBody = document.getElementById("ledger-table-body");
    const ledgerResultDiv = document.getElementById("ledger-result");

    if (ledgerForm) {
        ledgerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const userId = document.getElementById("user_id").value.trim();
            const alertElement = "ledger-alert-container";
            
            if (!userId) {
                showAlert(alertElement, "User ID is required.", "error");
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/ledger/${userId}`);
                const data = await response.json();

                if (response.ok) {
                    document.getElementById(alertElement).innerHTML = "";
                    if (ledgerResultDiv) ledgerResultDiv.style.display = "block";
                    if (tableBody) {
                        tableBody.innerHTML = "";
                        if (data.ledger && data.ledger.length > 0) {
                            data.ledger.forEach(entry => {
                                const row = document.createElement("tr");
                                let typeBadge = "";
                                if (entry.entry_type === "credit") {
                                    typeBadge = `<span class="badge badge-credit">Credit</span>`;
                                } else if (entry.entry_type === "redeem") {
                                    typeBadge = `<span class="badge badge-redeem">Redeem</span>`;
                                } else if (entry.entry_type === "reversal") {
                                    typeBadge = `<span class="badge badge-reversal">Reversal</span>`;
                                }

                                const pointSign = entry.points > 0 ? `+${entry.points}` : entry.points;
                                const pointColor = entry.points > 0 ? "var(--color-matcha)" : "var(--color-berry)";

                                row.innerHTML = `
                                    <td style="font-family: monospace; font-size: 0.85rem;">${entry.event_id || "—"}</td>
                                    <td>${typeBadge}</td>
                                    <td style="color: ${pointColor}; font-weight: 700;">${pointSign}</td>
                                    <td>${entry.description || ""}</td>
                                    <td>${formatTimestamp(entry.created_at)}</td>
                                `;
                                tableBody.appendChild(row);
                            });
                        } else {
                            tableBody.innerHTML = `
                                <tr>
                                    <td colspan="5" class="empty-state">
                                        <div class="empty-icon">📭</div>
                                        <div>No transactions found for User ID "${userId}"</div>
                                    </td>
                                </tr>
                            `;
                        }
                    }
                } else {
                    showAlert(alertElement, `Failed: ${data.error || "Connection error."}`, "error");
                }
            } catch (err) {
                showAlert(alertElement, "Connection to Flask server failed.", "error");
            }
        });
    }
}


/* ==========================================================================
   6. Reversal Page (/reversal)
   ========================================================================== */
function setupReversalProcessor() {
    const reversalForm = document.getElementById("reversal-form");

    if (reversalForm) {
        reversalForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const eventId = document.getElementById("event_id").value.trim();
            const alertElement = "reversal-alert-container";

            if (!eventId) {
                showAlert(alertElement, "Event ID is required.", "error");
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/reverse/${eventId}`, { method: "POST" });
                const data = await response.json();

                if (response.status === 200) {
                    if (data.points_reversed > 0) {
                        showAlert(alertElement, `<strong>Reversed!</strong> Cancelled <strong>${data.points_reversed}</strong> points. User: ${data.user_id}. New Balance: <strong>${data.new_balance}</strong>.`, "success");
                    } else {
                        showAlert(alertElement, `Reversal applied: ${data.message}`, "info");
                    }
                } else if (response.status === 404) {
                    showAlert(alertElement, `Event ID "${eventId}" was not found.`, "error");
                } else if (response.status === 409) {
                    showAlert(alertElement, `Conflict: ${data.error}`, "error");
                } else {
                    showAlert(alertElement, `Error: ${data.error}`, "error");
                }
            } catch (err) {
                showAlert(alertElement, "Connection failed. Server offline.", "error");
            }
        });
    }
}
