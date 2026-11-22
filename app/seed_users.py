from app.extensions import db
from app.models import User


ACCOUNTS = (
    ("user1", "user1", "user", "Покупатель", None, "+7 900 100-00-01"),
    ("user2", "user2", "picker", "Сборщик", None, ""),
    ("user3", "user3", "courier", "Курьер Алексей", 1, "+7 900 111-22-33"),
    ("admin", "admin", "admin", "Администратор", None, ""),
)


def seed_users():
    if User.query.first():
        return
    for username, password, role, display_name, courier_id, phone in ACCOUNTS:
        user = User(
            username=username,
            role=role,
            display_name=display_name,
            courier_id=courier_id,
            phone=phone,
        )
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
