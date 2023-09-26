from datetime import datetime, timedelta
from typing import Annotated
import database as db
from typing import List
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel


SECRET_KEY = "572e6a5c93a212130ceebdcef0aceb494d973772f6bcc61bc9f4dbfc92f393a3"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserCreate(BaseModel):
    username: str
    full_name: str
    disabled: bool = False


class UserInDB(UserCreate):
    hashed_password: str


class Post(BaseModel):
    post_id: int
    user_id: int
    content: str
    likes: int
    comment: list[str]


class PostCreate(BaseModel):
    user_id: int
    content: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

current_user = []


def verify_password(plain_password, hashed_password, username):
    user = db.get_userdetail(username)
    print(user)
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    if username == db.get_username(username):
        user_dict = db.get_userdetail(username)
        print(user_dict)
        return UserInDB(**user_dict)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password, username):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserCreate, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    global current_user
    current_user= user.username
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=UserCreate)
async def create_user(user_data: UserInDB):
    if user_data.username == db.get_username(user_data.username):
        raise HTTPException(status_code=404, detail="User already present")
    user_id = len(db.all_user()) + 1
    user_data = user_data.dict()
    user_data["user__id"] = user_id
    user_data["hashed_password"] = get_password_hash(user_data["hashed_password"])
    data = db.create_user(user_data)
    return {**user_data}


@app.post("/posts/", response_model=Post, dependencies=[Depends(get_current_active_user)])
async def create_post(post_data: PostCreate):
    if post_data.user_id != db.get_user(post_data.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    post_id = len(db.all_post()) + 1
    post_data = post_data.dict()
    post_data['post_id'] = post_id
    post_data['likes'] = 0
    post_data['comment'] = []

    data = db.create_post(post_data)
    return {**post_data}




@app.get("/users/me/", response_model=UserCreate)
async def read_users_me(
    current_user: Annotated[UserCreate, Depends(get_current_active_user)]
):
    print(current_user)
    return current_user


@app.put("/posts/{post_id}/like/", dependencies=[Depends(get_current_active_user)])
async def like_post(post_id: int):
    if post_id != db.get_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    res = db.like(post_id)
    return f"liked by {current_user}"


@app.put("/posts/{post_id}/comment", dependencies=[Depends(get_current_active_user)])
async def comment_post(post_id: int, comment: str):
    if post_id != db.get_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    res = db.comment(comment, post_id)
    return f"commented by {current_user} : {comment}"


@app.get("/posts/", response_model=List[Post], dependencies=[Depends(get_current_active_user)])
async def get_posts():
    return list(db.all_post())


@app.get("/users/", dependencies=[Depends(get_current_active_user)])
async def get_users():
    return list(db.all_user())