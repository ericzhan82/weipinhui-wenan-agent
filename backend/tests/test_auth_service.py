from app.auth import create_access_token, decode_access_token, hash_password, verify_password
from app.models import User


def test_password_hash_and_signed_token_round_trip(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret")
    stored = hash_password("secret")
    user = User(id=7, email="admin@example.com", display_name="Admin", password_hash=stored, is_system_admin=True)

    assert verify_password("secret", stored) is True
    assert verify_password("wrong", stored) is False

    payload = decode_access_token(create_access_token(user))

    assert payload["sub"] == 7
    assert payload["email"] == "admin@example.com"
