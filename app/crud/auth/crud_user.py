from app.api.deps import DB
from app.core import get_password_hash
from app.models import UserModel
from app.schemas import UserCreate


def get_user_by_email(db: DB, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()


def create_user(db: DB, payload: UserCreate):
    hash = get_password_hash(payload.password)

    user_dict = payload.model_dump(exclude={"password"})
    user_dict["password_hash"] = hash

    user = UserModel(**user_dict)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
