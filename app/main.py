from contextlib import asynccontextmanager

from database.config_db import Config
from database.db import db_close, db_init
from database.user_db import User
from fastapi import (
    FastAPI,
    Request,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models.error_models import Response422
from routers.admin_routers import UserNotExist
from routers.admin_routers import router as admin_router
from routers.bot_routers import (
    BotDisable,
    BotNotFound,
    LevelError,
    ModelNotFound,
    NoChat,
    UserOutdate,
)
from routers.bot_routers import router as bot_router
from routers.user_routers import router as user_router
from services.jwt_auth import AuthFailed
from services.poe_client import login_poe, scheduler
from utils.env_util import (
    API_PATH,
    HOST,
    ORIGINS,
    PORT,
    SSL_CERTFILE_PATH,
    SSL_KEYFILE_PATH,
)
from uvicorn import run

################
### 后端定义
################


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_init()
    await User.init_data()
    await Config.init_data()
    await login_poe()
    scheduler.start()

    yield

    await db_close()


app = FastAPI(
    lifespan=lifespan,
    description="""require Python environment >= 3.10

20XX 客户端处理错误  
- 2000    认证失败：密码错误、权限不足等  
- 2001    请求错误
- 2002    模型不存在
- 2003    用户不存在
- 2004    用户已存在
- 2005    会话不存在
- 2006    尚未发起对话
- 2009    用户过期，无法创建和对话
- 2010    用户等级不足
- 2011    该会话已失效，无法使用
- 2099    其他请求错误
  
30XX 服务器处理错误
- 3001    服务器出错
- 3008    Poe登陆失败
""",
    responses={
        422: {
            "description": "请求错误",
            "model": Response422,
        },
    },
)
# HTTPS重定向
# app.add_middleware(HTTPSRedirectMiddleware)

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


################
### 错误处理
################
@app.exception_handler(RequestValidationError)
async def _(request: Request, exc: RequestValidationError):
    return JSONResponse({"code": 2001, "msg": repr(exc)}, 422)


@app.exception_handler(AuthFailed)
async def _(request: Request, exc: AuthFailed):
    return JSONResponse({"code": 2000, "msg": exc.error_type}, 401)


@app.exception_handler(ModelNotFound)
async def _(request: Request, exc: ModelNotFound):
    return JSONResponse(
        {
            "code": 2002,
            "msg": f"模型【{exc.model}】不存在，可用模型：ChatGPT, Claude, ChatGPT4, Claude-2-100k。",
        },
        402,
    )


@app.exception_handler(BotNotFound)
async def _(request: Request, exc: BotNotFound):
    return JSONResponse(
        {
            "code": 2005,
            "msg": "会话不存在",
        },
        402,
    )


@app.exception_handler(NoChat)
async def _(request: Request, exc: NoChat):
    return JSONResponse(
        {
            "code": 2006,
            "msg": "尚未发起对话",
        },
        402,
    )


@app.exception_handler(UserNotExist)
async def _(request: Request, exc: UserNotExist):
    return JSONResponse(
        {
            "code": 2003,
            "msg": "用户不存在",
        },
        402,
    )


@app.exception_handler(UserOutdate)
async def _(request: Request, exc: UserOutdate):
    return JSONResponse(
        {
            "code": 2009,
            "msg": f"你的账号已过期，有效期至【{exc.date}】，无法创建和对话",
        },
        402,
    )


@app.exception_handler(LevelError)
async def _(request: Request, exc: LevelError):
    return JSONResponse(
        {
            "code": 2010,
            "msg": "你的账号等级不足，需升级用户权限",
        },
        402,
    )


@app.exception_handler(BotDisable)
async def _(request: Request, exc: BotDisable):
    return JSONResponse(
        {
            "code": 2011,
            "msg": "该会话已失效，无法使用",
        },
        402,
    )


################
### 添加路由
################
app.include_router(user_router, prefix=f"{API_PATH}/user", tags=["用户模块"])
app.include_router(bot_router, prefix=f"{API_PATH}/bot", tags=["会话模块"])
app.include_router(admin_router, prefix=f"{API_PATH}/admin", tags=["管理员模块"])

################
### 日志配置
################
custom_logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s - %(levelprefix)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s - %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file_default": {
            "formatter": "default",
            "class": "logging.FileHandler",
            "filename": "./server.log",
        },
        "file_access": {
            "formatter": "access",
            "class": "logging.FileHandler",
            "filename": "./server.log",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default", "file_default"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {
            "handlers": ["access", "file_access"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

################
### 启动进程
################
if __name__ == "__main__":
    run(
        app,
        host=HOST,
        port=PORT,
        ssl_keyfile=SSL_KEYFILE_PATH,
        ssl_certfile=SSL_CERTFILE_PATH,
        log_config=custom_logging_config,
        headers=[("server", "huaQ")],  # 修改响应头里的默认server字段
    )
