from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import bcrypt


def utc_now():
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for wallet-only auth
    wallet_address = db.Column(db.String(42), unique=True, nullable=True)  # Ethereum address
    role = db.Column(db.String(20), default='user')  # user, admin, transfer_agent
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    last_login = db.Column(db.DateTime, nullable=True)

    def __init__(
        self,
        username: str,
        email: str,
        password_hash: str | None = None,
        wallet_address: str | None = None,
        role: str = 'user',
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        last_login: datetime | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.wallet_address = wallet_address
        self.role = role
        self.is_active = is_active
        self.created_at = created_at or utc_now()
        self.updated_at = updated_at or utc_now()
        self.last_login = last_login

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        """Verify password against stored hash"""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'wallet_address': self.wallet_address,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def to_public_dict(self):
        """Return only public information"""
        return {
            'id': self.id,
            'username': self.username,
            'wallet_address': self.wallet_address,
            'role': self.role
        }
