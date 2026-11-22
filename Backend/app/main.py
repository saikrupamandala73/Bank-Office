import pathlib
import sys

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, engine, ensure_schema, get_db
from app.models import User
from app.routes_finance import router as finance_router
from app.schemas import UserCreate, UserRead

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

app = FastAPI(title="Backend API")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)
ensure_schema(engine)

app.include_router(finance_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/demo/reset", status_code=status.HTTP_200_OK)
def demo_reset():
    from seed import reset_and_seed

    counts = reset_and_seed()
    return {"status": "reset", **counts}


@app.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserRead)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User)).all()


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
