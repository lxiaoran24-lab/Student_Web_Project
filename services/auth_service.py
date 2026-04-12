from models.db import db
from models.user_model import User


def create_user(username: str, email: str, password: str):
    if User.query.filter_by(username=username).first():
        return None, "用户名已存在"

    if User.query.filter_by(email=email).first():
        return None, "邮箱已存在"

    user = User(username=username, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user, None


def authenticate_user(username_or_email: str, password: str):
    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()

    if not user:
        return None

    if not user.check_password(password):
        return None

    return user