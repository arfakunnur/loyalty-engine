# Loyalty Points Engine

A simple Loyalty Points Engine built using Flask, SQLite/MySQL, HTML, CSS, and JavaScript.

This project was developed as part of a backend engineering assignment. The main objective is to process customer transaction events, award loyalty points based on configurable rules, maintain a transaction ledger, allow reward redemption, and support event reversals.

To make the project easier to demonstrate, I also created a simple web interface using HTML, CSS, and JavaScript.

---

## Project Structure

```text
loyalty-engine/
│
├── app.py
├── models.py
├── config.json
├── requirements.txt
├── README.md
│
├── templates/
│   ├── index.html
│   ├── create-event.html
│   ├── balance.html
│   ├── rewards.html
│   ├── ledger.html
│   └── reversal.html
│
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── app.js
    └── images/
```

---

## Technologies Used

### Backend

* Python
* Flask
* SQLAlchemy
* SQLite / MySQL

### Frontend

* HTML
* CSS
* JavaScript

### API Testing

* Postman

---

## How to Run the Project

### 1. Create Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/Mac:

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://localhost:5000
```

The database and default rewards will be created automatically when the application runs for the first time.

---

## Features

### Event Ingestion

Users can submit transaction events such as purchases, referrals, deposits, or bill payments.

Each event contains:

* Event ID
* User ID
* Event Type
* Amount
* Timestamp

---

### Rules Engine

The system calculates loyalty points based on rules stored in `config.json`.

Examples:

* Different event types earn different points.
* Weekend transactions can receive bonus points.
* Maximum points per event can be limited.

Because the rules are stored in a configuration file, they can be changed without modifying the application code.

---

### Points Ledger

Instead of directly updating a user's balance, every transaction is stored in a ledger.

Examples:

```text
+20 Points (Purchase)
+10 Points (Referral)
-50 Points (Reward Redemption)
```

The current balance is calculated by adding all ledger entries.

This helps maintain a complete history of all transactions.

---

### Reward Redemption

Users can redeem rewards using their available points.

Sample rewards:

* Coffee Coupon
* Movie Ticket
* Gift Card

The system checks whether the user has enough points before allowing redemption.

---

### Event Reversal

If a transaction needs to be cancelled, the system creates a reversal entry instead of deleting the original transaction.

Example:

```text
Original Event: +20 Points

Reversal Entry: -20 Points
```

This keeps the full transaction history available for auditing.

---

## API Endpoints

### Create Event

```http
POST /events
```

Processes a new transaction and awards points.

---

### Check Balance

```http
GET /balance/<user_id>
```

Returns the current points balance of a user.

---

### View Ledger

```http
GET /ledger/<user_id>
```

Returns the transaction history for a user.

---

### View Rewards

```http
GET /rewards
```

Returns all available rewards.

---

### Redeem Reward

```http
POST /redeem
```

Allows a user to redeem a reward using points.

---

### Reverse Event

```http
POST /reverse/<event_id>
```

Reverses a previously processed event.

---

## Design Decisions

### Why Use a Ledger?

Instead of storing only the latest balance, every points transaction is stored as a separate record.

Benefits:

* Easy to track transaction history
* Easy to audit
* No loss of information

---

### Why Use Event ID?

Each event has a unique Event ID.

This prevents the same transaction from being processed twice if the API receives duplicate requests.

---

### Why Store Rules in config.json?

Business rules can change over time.

By storing them in a configuration file, changes can be made without modifying the application code.

---

### Why Use Reversal Instead of Delete?

Deleting records removes history.

Creating a reversal entry keeps the original transaction visible while correcting the balance.

---

## Challenges Faced

### Preventing Duplicate Events

The main challenge was ensuring that the same event could not be processed twice.

This was solved by using a unique Event ID and checking it before processing.

### Maintaining Transaction History

Instead of updating balances directly, I used a ledger system where every transaction is stored separately.

### Implementing Reversals

Rather than deleting data, reversal entries were added to maintain a complete audit trail.

---

## Future Improvements

* User Authentication
* Admin Dashboard
* Role-Based Access Control
* PostgreSQL Support
* Reporting and Analytics

---

## AI Usage Disclosure

AI tools were used to help with project planning, code structure suggestions, and reviewing implementation ideas.

## Author
Arfajhan c Kunnur
