import json

from fastapi_login.exceptions import InvalidCredentialsException
from fastapi_login import LoginManager


class NotAuthenticatedException(Exception):
    pass


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
manager = LoginManager(SECRET_KEY, '/login', use_cookie=True,
                       not_authenticated_exception=NotAuthenticatedException, cookie_name="access-token")


with open('users.json') as f:
    fake_users_db = json.load(f)


@manager.user_loader()
def load_user(user_id: str):
    user = fake_users_db.get(user_id)
    return user


# async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
#     print(1)
#     credentials_exception = HTTPException(
#         status_code=401,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except InvalidTokenError:
#         raise credentials_exception
#     user = get_user(fake_users_db, username=token_data.username)
#     if user is None:
#         raise credentials_exception
#     if user.disabled:
#         raise HTTPException(status_code=418, detail="Inactive user")
#     return user


# @app.post("/token")
# async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response) -> Token:
#     user = authenticate_user(form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=401,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token = create_access_token(
#         data={"sub": user.username}, expires_delta=timedelta(minutes=config['jwt_expiration_time'])
#     )
#     response.set_cookie(key='Authorization', value=f'Bearer {access_token}')
#     print('set cookie')
#     return Token(access_token=access_token, token_type="bearer")