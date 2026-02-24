## FastAPI Auth Flow – Theory + Implementation Guide

This document explains a basic but industry-aligned authentication flow for your FastAPI app:

- **Signup (register)**
- **Login**
- **Hashed passwords with salt**
- **JWT access tokens + refresh tokens**

It mixes **theory** (what and why) with **implementation guidance** (how to do it in this project).

---

## 1. Big Picture: How Modern Auth Works

### **Goals**

- **Identify users** securely (login).
- **Create accounts** (signup).
- **Protect sensitive routes** (only logged-in users can call them).
- **Limit damage** if tokens are stolen (short-lived access tokens, refresh tokens, revocation).

### **Core Ideas**

- **Passwords are never stored in plain text** → only **salted, hashed** versions.
- **Clients don’t keep server-side sessions** → they send **JWT access tokens** with each request.
- **Access tokens expire quickly** → reduce damage if stolen.
- **Refresh tokens live longer** → let users stay logged in without re-entering password.

---

## 2. Passwords: Hashing and Salting

### **Concept**

- A **hash function** takes input (password) and outputs a fixed string (hash).
- A **salt** is random data added before hashing:
  - `hash = H(password + salt)`
  - Ensures:
    - Same password used by different users → different hashes.
    - Precomputed tables (rainbow tables) are useless.

### **In practice (FastAPI + Python)**

- Use a library, **never build your own crypto**.
- Common choice: `passlib[bcrypt]`.

**Implementation pattern:**

- On **signup**:

  - Take plain password.
  - `hashed_password = get_password_hash(plain_password)`.
  - Store `hashed_password` in the database (not the plain password).

- On **login**:
  - Get user from DB → `user.hashed_password`.
  - `verify_password(plain_password, user.hashed_password)`:
    - `True` → password is correct.
    - `False` → reject login.

**Typical helper functions (in `auth.py`):**

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

---

## 3. Tokens: Access Token vs Refresh Token

### **Access Token**

- **Short-lived** (e.g. 15–30 minutes).
- Sent with each protected API request:
  - Header: `Authorization: Bearer <access_token>`.
- Contains:
  - `sub`: user id (subject).
  - `exp`: expiry timestamp.
  - Maybe roles/permissions.
- If stolen:
  - Attacker has limited time window → **better security**.

### **Refresh Token**

- **Longer-lived** (e.g. 7–30 days).
- Used only to get a new access token at `/refresh`.
- Not sent with every request.
- If stolen:
  - Attacker can keep minting new access tokens.
- Therefore:
  - Store more carefully (prefer **httpOnly cookie** in real web apps).
  - Optionally store/track in DB to revoke if necessary.

---

## 4. JWTs: How Tokens Are Built and Verified

### **What is a JWT?**

- JSON Web Token: a signed JSON payload.
- Has three parts: `header.payload.signature` (Base64URL encoded).
- Server signs with a **secret** (`SECRET_KEY` + algorithm like HS256).

**Example payload:**

```json
{
  "sub": "123",
  "type": "access",
  "exp": 1730000000
}
```

### **Implementation pattern (using `python-jose`)**

In `auth.py`:

```python
from datetime import datetime, timedelta, timezone
from jose import jwt

SECRET_KEY = "REPLACE_WITH_ENV_SECRET"   # use env var in real app
ALGORITHM = "HS256"

def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

Then:

```python
from datetime import timedelta

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(subject: str) -> str:
    return _create_token(
        data={"sub": subject, "type": "access"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

def create_refresh_token(subject: str) -> str:
    return _create_token(
        data={"sub": subject, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
```

To decode/verify:

```python
from jose import JWTError, jwt

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

---

## 5. Data Models: DB vs Pydantic

### **SQLAlchemy model (DB layer)**

Represents the **database table**. Example (`database_models.py`):

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
```

### **Pydantic models (request/response layer)**

Represent **what the API receives and returns**. Example (`models.py`):

```python
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True  # map from ORM objects

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

---

## 6. Endpoints and Flow

### **1) Signup (`POST /signup`)**

**Theory:**

- Create user safely:
  - Validate input.
  - Check if email already exists.
  - Hash password.
  - Store `hashed_password` in DB.
  - Return user data (no password).

**Implementation outline (in `main.py`):**

```python
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import UserCreate, UserRead
from database_models import UserModel
from auth import get_password_hash

@app.post("/signup", response_model=UserRead)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_pw = get_password_hash(user_in.password)

    user = UserModel(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hashed_pw,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
```

---

### **2) Login (`POST /login`)**

**Theory:**

- Prove user identity, then issue tokens:
  - Find user by email.
  - Verify password.
  - If correct → create access & refresh tokens.
  - Return tokens to the client.

**Implementation outline:**

```python
from models import UserLogin, Token
from auth import verify_password, create_access_token, create_refresh_token

@app.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    return Token(access_token=access_token, refresh_token=refresh_token)
```

---

### **3) Refresh (`POST /refresh`)**

**Theory:**

- Access token expires → client calls `/refresh` with **refresh token**.
- Server:
  - Verifies refresh token JWT.
  - Ensures `type == "refresh"`.
  - Gets user id from `sub`.
  - Issues new access token (and often a new refresh token).

**Implementation outline:**

```python
from pydantic import BaseModel
from models import Token
from auth import decode_token, create_access_token, create_refresh_token

class RefreshRequest(BaseModel):
    refresh_token: str

@app.post("/refresh", response_model=Token)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(UserModel).get(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    new_access = create_access_token(subject=str(user.id))
    new_refresh = create_refresh_token(subject=str(user.id))

    return Token(access_token=new_access, refresh_token=new_refresh)
```

---

### **4) Protecting Routes: `get_current_user` Dependency**

**Theory:**

- For endpoints that require auth, you:
  - Read `Authorization: Bearer <access_token>`.
  - Verify token.
  - Ensure `type == "access"`.
  - Load user and inject into endpoint as dependency.

**Implementation outline:**

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(UserModel).get(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
```

Use it in routes:

```python
@app.get("/me", response_model=UserRead)
def read_me(current_user: UserModel = Depends(get_current_user)):
    return current_user
```

---

## 7. Client-Side Responsibilities (Quick Summary)

- **Signup**:

  - Call `POST /signup` with `{ "name": "...", "email": "...", "password": "..." }`.

- **Login**:

  - Call `POST /login` with `{ "email": "...", "password": "..." }`.
  - Store `access_token` and `refresh_token` (for learning, you can use localStorage/in-memory; for production, use httpOnly cookie for refresh token).

- **Calling protected APIs**:

  - Add header: `Authorization: Bearer <access_token>`.

- **When access token expires**:

  - Call `POST /refresh` with `{ "refresh_token": "..." }`.
  - Replace stored tokens with the new ones.

- **Logout**:
  - Remove access token and refresh token from client storage.
  - (Advanced) server: revoke refresh token(s) in DB.
