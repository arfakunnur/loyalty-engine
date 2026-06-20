# Loyalty Points Engine ☕

A simple, beginner-friendly **Flask (Python) + MySQL/SQLite** transactional engine with a responsive, warm café-themed **HTML/CSS/JS frontend** for managing customer loyalty points. Served entirely through Flask.

This project is designed as an interview assignment. It implements a clean, flat architecture containing robust database-level idempotency, a configurable rules engine, and an append-only immutable ledger.

---

## 📂 Simplified Project Structure

```text
loyalty-engine/
│
├── app.py                  # Main Flask application (Routing, API, Rules Engine)
├── models.py               # Database schemas (SQLAlchemy: Event, LedgerEntry, Reward)
├── config.json             # Rules engine parameters and Reward Catalog config
├── requirements.txt        # Python application dependencies
├── README.md               # Documentation and interview guide (You are here)
│
├── templates/              # HTML layout templates served by Flask
│   ├── index.html          # Main Dashboard
│   ├── create-event.html   # Log transaction events (credits points)
│   ├── balance.html        # View user balance
│   ├── rewards.html        # Reward Catalog & redemption interface
│   ├── ledger.html         # Audit logs / Transaction history
│   └── reversal.html       # Cancel/Reverse prior events
│
└── static/                 # Static asset files
    ├── css/
    │   └── style.css       # Cozy Beans café layout and styling
    ├── js/
    │   └── app.js          # API calls to Flask endpoints (using Fetch API)
    └── images/
        └── coffee_cup_watermark.png  # Hand-drawn watermark graphic
```

---

## 🚀 Setup & Execution Instructions

Follow these simple steps to run the application locally.

### Step 1: Install Dependencies

1. **Open your terminal** in the `loyalty-engine` project folder.
2. **Create and activate a virtual environment (Recommended):**
   ```powershell
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Windows (Command Prompt)
   python -m venv venv
   .\venv\Scripts\activate.bat

   # macOS / Linux
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Configure the Database

* By default, the application is configured to connect to a **MySQL** database (`loyalty_db`) using the credentials in `config.json`.
* **SQLite Fallback:** If the application cannot connect to MySQL, it will automatically print a warning and fallback to a local SQLite database file named `loyalty.db` in the project folder. This ensures the app runs out of the box with zero setup!

### Step 3: Run the Server

1. **Launch the application:**
   ```bash
   python app.py
   ```
2. **Access the application:**
   Open your browser and navigate to:
   👉 **`http://localhost:5000`**

*Note: The database tables and default rewards (Coffee Coupon, Movie Ticket, Gift Card) are automatically initialized and seeded on first run.*

---

## 🧠 Key Interview Highlights (How to Explain the Code)

If asked about the system's architecture during your interview, highlight these key design patterns:

1. **Immutable Append-Only Ledger**:
   We never run SQL `UPDATE` operations on point balances. A customer's balance is computed dynamically by summing all points (`SUM(points)`) in the `ledger` table. This mimics double-entry banking systems, providing a perfect audit trail and preventing data tampering.

2. **System-wide Idempotency Key**:
   To prevent duplicate processing if a client retries a request, the API checks if the unique `event_id` already exists. The database enforces a `UNIQUE` constraint on the `event_id` column. Duplicate events fail fast, returning a `409 Conflict` status.

3. **Compensating Reversal Pattern**:
   When reversing an event (e.g., if a transaction is refunded), we do not delete the original rows. Instead, we append a new `reversal` entry with negative points. This preserves the transaction history, making auditing straightforward.

4. **Rules Engine Isolation**:
   Point calculation logic (base rates, multipliers, caps) is defined in `config.json` and computed inside `app.py`. Weekend events automatically receive a `2.0x` multiplier (calculated using Python's `timestamp.weekday()`), and single-event points are capped to prevent abuse.

5. **Self-Contained Serve Pattern**:
   The frontend is served directly by the Flask server using `render_template` and `static_url_path`. This eliminates CORS issues and simplifies deployment, making the entire project easy to run with a single command.

---

## 🛠️ API Reference Summary

The backend exposes the following REST API endpoints:

* **`POST /events`**: Ingest customer transactions (purchase, signup, referral, checkin, review).
* **`GET /balance/<user_id>`**: Returns the computed balance for a customer.
* **`GET /ledger/<user_id>`**: Returns transaction history for a customer (credits, redemptions, reversals).
* **`GET /rewards`**: Returns the list of redeemable rewards.
* **`POST /redeem`**: Atomically checks balance and spends points to redeem a reward.
* **`POST /reverse/<event_id>`**: Reverses a prior event and deducts points via compensating entry.
* **`GET /stats`**: Returns overall system metrics (total active points, total processed events, total redemptions).
