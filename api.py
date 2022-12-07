from classes.Exceptions import ApiException
from classes.DataAccessObject import DataAccessObject
from database.SqlAlchemyDatabase import init_models, get_session
from database.models.User import User

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.websockets import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()
WEBSOCKET: WebSocket = None
app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiException)
async def internal_exception_handler(request: Request, exc: ApiException):
    exc.headers.update({"Access-Control-Allow-Origin": f"https://0.0.0.0:8080"})
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "message": ["error", exc.detail]
        },
        headers=exc.headers
    )
    # format headers by middleware
    cors_middleware = None
    for middleware in app.user_middleware:
        if middleware.cls == CORSMiddleware:
            cors_middleware = middleware
            break
    request_origin = request.headers.get("origin", "")
    if cors_middleware and "*" in cors_middleware.options["allow_origins"]:
        response.headers["Access-Control-Allow-Origin"] = "*"
    elif cors_middleware and request_origin in cors_middleware.options["allow_origins"]:
        response.headers["Access-Control-Allow-Origin"] = request_origin
    return response


@app.on_event("startup")
async def startup():
    await init_models(create=True)


@app.get("/init_score")
async def get_score(tg_id: int, db_session: AsyncSession = Depends(get_session)):
    dao = DataAccessObject(db_session)
    user = await dao.get_objects(User, property_filter=[(User.tg_id, tg_id)])
    if not user:
        return None, False
    return user[0][0].score, user[0][0].completed


@app.post("/add_user")
async def add_user(tg_id: int, name: str, db_session: AsyncSession = Depends(get_session)):
    dao = DataAccessObject(db_session)
    await dao.add_object(User(tg_id=tg_id, name=name, score=0, completed=False))
    return "Success"


@app.put("/score")
async def increase_score(delta: int, tg_id: int, db_session: AsyncSession = Depends(get_session)):
    dao = DataAccessObject(db_session)
    user = (await dao.get_objects(User, property_filter=[(User.tg_id, tg_id)]))[0][0]
    user.score += delta
    await db_session.commit()
    data = []
    users = await dao.get_objects(User)
    for el in users:
        user = el[0]
        data.append({"name": user.name, "score": user.score, "update_on": user.updated_at})
    data.sort(key=lambda el: (-el["score"], el["update_on"]))
    await WEBSOCKET.send_json([{"name": el["name"], "score": el["score"]} for el in data])
    return "success"


@app.put("/stop")
async def finish_quiz(tg_id: int, db_session: AsyncSession = Depends(get_session)):
    dao = DataAccessObject(db_session)
    user = (await dao.get_objects(User, property_filter=[(User.tg_id, tg_id)]))[0][0]
    user.completed = True
    await db_session.commit()
    return "success"


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global WEBSOCKET
    await websocket.accept()
    WEBSOCKET = websocket
    while True:
        await websocket.receive_text()


if __name__ == '__main__':
    uvicorn.run("api:app", host="localhost", port=8000, reload=True)
