import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sqlalchemy import create_engine, func
from models import db, Event, LedgerEntry, Reward

# Initialize the Flask application
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS)
# This allows external clients or browser pages to query the REST APIs
CORS(app)

# ------------------------------------------------------------------ #
# 1. Config Loading & Database Selection with Fallback
# ------------------------------------------------------------------ #
# Load configuration from config.json
config_path = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except Exception as err:
    print(f"Error loading config.json: {err}")
    config = {}

# Retrieve MySQL Database URI
mysql_uri = config.get("database", {}).get("uri", "mysql+pymysql://root:password@localhost/loyalty_db")
fallback_to_sqlite = False

# Database setup check
try:
    # Create engine and attempt a quick connection test
    temp_engine = create_engine(mysql_uri)
    conn = temp_engine.connect()
    conn.close()
    print("Database Connection: Successfully connected to MySQL database!")
except Exception as db_err:
    print("=" * 75)
    print("DATABASE CONNECTION WARNING:")
    print(f"Could not connect to MySQL using: {mysql_uri}")
    print(f"Reason: {db_err}")
    print("\n>>> FALLING BACK TO LOCAL SQLITE DATABASE ('loyalty.db') FOR DEMO PURPOSES <<<")
    print("Please make sure MySQL is running and the database 'loyalty_db' is created.")
    print("=" * 75)
    fallback_to_sqlite = True

# Apply connection URI based on availability
if fallback_to_sqlite:
    base_dir = os.path.abspath(os.path.dirname(__file__))
    sqlite_path = os.path.join(base_dir, "loyalty.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = mysql_uri

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Bind SQLAlchemy to the Flask app
db.init_app(app)


# ------------------------------------------------------------------ #
# 2. Database Initialization Helper
# ------------------------------------------------------------------ #
def init_database():
    """Create database tables and seed default rewards if catalog is empty."""
    db.create_all()
    
    # Check if rewards table is already seeded
    if Reward.query.count() == 0:
        rewards_data = config.get("reward_catalog", [
            {"name": "Coffee Coupon", "points_required": 100},
            {"name": "Movie Ticket", "points_required": 300},
            {"name": "Gift Card", "points_required": 500}
        ])
        for item in rewards_data:
            db.session.add(Reward(name=item["name"], points_required=item["points_required"]))
        db.session.commit()
        print("Seeded Reward Catalog successfully!")

with app.app_context():
    init_database()


# ------------------------------------------------------------------ #
# 3. Rules Engine Helper Function
# ------------------------------------------------------------------ #
def calculate_points(event_type: str, amount: float, timestamp: datetime) -> int:
    """
    Pure business logic function. Calculates point awards based on:
    - Base points rates from configuration.
    - Weekend multiplier (2.0x points for Saturday & Sunday).
    - Maximum cap limit per event type.
    """
    rules = config.get("rules", {})
    
    # 1. Fetch base rate points for event type
    base_rates = rules.get("base_points", {})
    base_rate = base_rates.get(event_type, 0)
    
    # Calculate starting points
    # For purchases, points = base_rate * transaction amount
    # For flat-rate items (signup, referral, review), points = flat base_rate
    if event_type == "purchase":
        points = base_rate * amount
    else:
        points = base_rate

    # 2. Apply Weekend Multiplier (Saturday=5, Sunday=6)
    if timestamp.weekday() in (5, 6):
        multiplier = rules.get("weekend_multiplier", 1.0)
        points *= multiplier

    # Convert to integer points
    points = int(points)

    # 3. Apply Maximum Points Cap Constraint
    caps = rules.get("max_points_per_event", {})
    max_cap = caps.get(event_type, None)
    if max_cap is not None:
        points = min(points, max_cap)
        
    return points


# ------------------------------------------------------------------ #
# 4. View Page Routes (HTML Templates)
# ------------------------------------------------------------------ #
@app.route("/")
def route_home():
    return render_template("index.html")

@app.route("/create-event")
def route_create_event():
    return render_template("create-event.html")

@app.route("/balance")
def route_balance():
    return render_template("balance.html")

@app.route("/rewards")
def route_rewards():
    return render_template("rewards.html")

@app.route("/ledger")
def route_ledger():
    return render_template("ledger.html")

@app.route("/reversal")
def route_reversal():
    return render_template("reversal.html")


# ------------------------------------------------------------------ #
# 5. REST API Endpoints
# ------------------------------------------------------------------ #

@app.route("/events", methods=["POST"])
def api_ingest_event():
    """
    POST /events
    Ingests a customer transaction event and awards points.
    Enforces idempotency using a UNIQUE constraint on the event_id field.
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    required = ["event_id", "user_id", "event_type", "amount", "timestamp"]
    missing = [field for field in required if field not in payload]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    event_id = str(payload["event_id"])
    user_id = str(payload["user_id"])
    event_type = str(payload["event_type"])
    
    try:
        amount = float(payload["amount"])
        if amount < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Amount must be a non-negative number."}), 400

    # Parse ISO timestamp
    try:
        timestamp_str = payload["timestamp"]
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except Exception:
        return jsonify({"error": "Invalid timestamp format. Use ISO-8601 (YYYY-MM-DDTHH:MM:SSZ)."}), 400

    # Check for Idempotency: Has this event_id already been processed?
    existing_event = Event.query.filter_by(event_id=event_id).first()
    if existing_event:
        return jsonify({"error": f"Event '{event_id}' has already been processed."}), 409

    # 1. Save raw Event record
    new_event = Event(
        event_id=event_id,
        user_id=user_id,
        event_type=event_type,
        amount=amount,
        timestamp=timestamp
    )
    db.session.add(new_event)

    # 2. Calculate Points via Rules Engine
    points = calculate_points(event_type, amount, timestamp)

    # 3. Create Ledger Credit Entry if points > 0
    if points > 0:
        credit_entry = LedgerEntry(
            user_id=user_id,
            event_id=event_id,
            points=points,
            entry_type="credit",
            description=f"Points earned for {event_type} (Amount: ${amount})"
        )
        db.session.add(credit_entry)

    try:
        db.session.commit()
    except Exception as commit_err:
        db.session.rollback()
        return jsonify({"error": "Failed to ingest event.", "detail": str(commit_err)}), 500

    return jsonify({
        "event_id": event_id,
        "user_id": user_id,
        "event_type": event_type,
        "points_awarded": points,
        "message": "Event processed and points awarded successfully."
    }), 201


@app.route("/balance/<string:user_id>", methods=["GET"])
def api_get_balance(user_id: str):
    """
    GET /balance/<user_id>
    Sums up points from all ledger rows for the user to return current balance.
    """
    # Sum points inside the database
    balance = db.session.query(func.sum(LedgerEntry.points)).filter(LedgerEntry.user_id == user_id).scalar() or 0
    return jsonify({
        "user_id": user_id,
        "balance": int(balance)
    }), 200


@app.route("/ledger/<string:user_id>", methods=["GET"])
def api_get_ledger(user_id: str):
    """
    GET /ledger/<user_id>
    Returns history of points transactions, newest first.
    """
    entries = LedgerEntry.query.filter_by(user_id=user_id).order_by(LedgerEntry.created_at.desc()).all()
    return jsonify({
        "user_id": user_id,
        "total_entries": len(entries),
        "ledger": [entry.to_dict() for entry in entries]
    }), 200


@app.route("/rewards", methods=["GET"])
def api_list_rewards():
    """
    GET /rewards
    Returns the seeded reward items in catalog.
    """
    rewards = Reward.query.order_by(Reward.points_required).all()
    return jsonify({
        "catalog": [r.to_dict() for r in rewards],
        "total": len(rewards)
    }), 200


@app.route("/redeem", methods=["POST"])
def api_redeem():
    """
    POST /redeem
    Redeems a reward from the catalog. Atomic balance checks are processed in a single transaction block.
    """
    payload = request.get_json(silent=True)
    if not payload or "user_id" not in payload or "reward_name" not in payload:
        return jsonify({"error": "user_id and reward_name are required."}), 400

    user_id = str(payload["user_id"])
    reward_name = str(payload["reward_name"])

    # Look up reward in catalog
    reward = Reward.query.filter_by(name=reward_name).first()
    if not reward:
        return jsonify({"error": f"Reward '{reward_name}' does not exist in the catalog."}), 404

    # Calculate current balance
    current_balance = db.session.query(func.sum(LedgerEntry.points)).filter(LedgerEntry.user_id == user_id).scalar() or 0
    if current_balance < reward.points_required:
        return jsonify({"error": f"Insufficient points. Required: {reward.points_required}, Available: {current_balance}."}), 402

    # Deduct points by appending a negative ledger entry
    debit_entry = LedgerEntry(
        user_id=user_id,
        event_id=None, # Redemptions aren't tied to standard transaction events
        points=-reward.points_required,
        entry_type="redeem",
        description=f"Redeemed: {reward.name} Voucher"
    )
    db.session.add(debit_entry)

    try:
        db.session.commit()
    except Exception as commit_err:
        db.session.rollback()
        return jsonify({"error": "Redemption transaction failed.", "detail": str(commit_err)}), 500

    return jsonify({
        "user_id": user_id,
        "reward": reward.name,
        "points_spent": reward.points_required,
        "remaining_balance": int(current_balance - reward.points_required),
        "message": f"Successfully claimed reward: {reward.name}!"
    }), 200


@app.route("/reverse/<string:event_id>", methods=["POST"])
def api_reverse_event(event_id: str):
    """
    POST /reverse/<event_id>
    Reverses points of a prior event by creating a compensating negative ledger entry.
    Enforces idempotency (cannot reverse the same event twice).
    """
    # Check if the original event exists
    original_event = Event.query.filter_by(event_id=event_id).first()
    if not original_event:
        return jsonify({"error": f"Original event '{event_id}' not found."}), 404

    # Idempotency: Check if a reversal entry already exists for this event
    prior_reversal = LedgerEntry.query.filter_by(event_id=event_id, entry_type="reversal").first()
    if prior_reversal:
        return jsonify({"error": f"Event '{event_id}' has already been reversed."}), 409

    # Sum all credits originally awarded to this event
    total_credit = db.session.query(func.sum(LedgerEntry.points)).filter(
        LedgerEntry.event_id == event_id,
        LedgerEntry.entry_type == "credit"
    ).scalar() or 0

    if total_credit == 0:
        return jsonify({"message": "No points were awarded for this event; reversal is unnecessary.", "points_reversed": 0}), 200

    # Write compensating ledger row (negative points)
    reversal_entry = LedgerEntry(
        user_id=original_event.user_id,
        event_id=event_id,
        points=-total_credit,
        entry_type="reversal",
        description=f"Reversal compensating entry for event '{event_id}'"
    )
    db.session.add(reversal_entry)

    try:
        db.session.commit()
    except Exception as commit_err:
        db.session.rollback()
        return jsonify({"error": "Reversal database write failed.", "detail": str(commit_err)}), 500

    new_balance = db.session.query(func.sum(LedgerEntry.points)).filter(LedgerEntry.user_id == original_event.user_id).scalar() or 0

    return jsonify({
        "event_id": event_id,
        "user_id": original_event.user_id,
        "points_reversed": int(total_credit),
        "new_balance": int(new_balance),
        "message": f"Successfully reversed {total_credit} points."
    }), 200


@app.route("/stats", methods=["GET"])
def api_get_stats():
    """
    GET /stats
    Provides global dashboard metrics.
    """
    try:
        total_balance = db.session.query(func.sum(LedgerEntry.points)).scalar() or 0
        total_events = db.session.query(func.count(Event.id)).scalar() or 0
        total_redemptions = db.session.query(func.count(LedgerEntry.id)).filter(LedgerEntry.entry_type == "redeem").scalar() or 0
        
        return jsonify({
            "total_balance": int(total_balance),
            "total_events_processed": int(total_events),
            "total_redemptions": int(total_redemptions)
        }), 200
    except Exception as stats_err:
        return jsonify({"error": "Failed to retrieve statistics.", "detail": str(stats_err)}), 500


# ------------------------------------------------------------------ #
# 6. Application Startup Execution
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    # Run the Flask app on localhost, port 5000 in debug mode
    app.run(host="0.0.0.0", port=5000, debug=True)
