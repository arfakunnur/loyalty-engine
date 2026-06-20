from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy database object
# This is shared with app.py to configure database communication
db = SQLAlchemy()

class Event(db.Model):
    """
    Represents an inbound transaction event.
    Idempotency is enforced by the database via the UNIQUE constraint on event_id.
    """
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    timestamp = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.created_at.isoformat()
        }

class LedgerEntry(db.Model):
    """
    Immutable ledger. Represents points credit, debit, or reversal.
    Current balance for any user is computed by summing the points column for their user_id.
    """
    __tablename__ = "ledger"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    event_id = db.Column(db.String(64), nullable=True, index=True) # Nullable for Redemptions
    points = db.Column(db.Integer, nullable=False)                 # Negative for debits/redemptions
    entry_type = db.Column(db.String(16), nullable=False)          # 'credit' | 'redeem' | 'reversal'
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "points": self.points,
            "entry_type": self.entry_type,
            "description": self.description,
            "created_at": self.created_at.isoformat()
        }

class Reward(db.Model):
    """
    Catalog of redeemable items. Seeded from config.json on first launch.
    """
    __tablename__ = "rewards"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    points_required = db.Column(db.Integer, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "points_required": self.points_required
        }
