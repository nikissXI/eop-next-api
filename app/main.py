from database import *
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from models import *
from routers import *
from services import *
from utils import *
from utils.config import *
from uvicorn import run

################
### 后端定义
################
app = FastAPI(
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _():
    await db_init()
    await User.init_data()
    await Config.init_data()
    await login_poe()


@app.on_event("shutdown")
async def _():
    await db_close()


################
### 错误处理
################
@app.exception_handler(RequestValidationError)
async def _(request: Request, exc: RequestValidationError):
    return JSONResponse({"code": 2001, "msg": str(exc)}, 422)


@app.exception_handler(AuthFailed)
async def _(request: Request, exc: AuthFailed):
    return JSONResponse({"code": 1001, "msg": exc.error_type}, 403)


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
            "msg": "会话句柄不存在",
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
            "msg": f"用户【{exc.user}】不存在",
        },
        402,
    )


@app.exception_handler(UserOutdate)
async def _(request: Request, exc: UserOutdate):
    return JSONResponse(
        {
            "code": 2003,
            "msg": f"你的账号已过期，有效期至【{exc.date}】",
        },
        402,
    )


################
### 添加路由
################
app.include_router(user_routers.router, prefix=f"{API_PATH}/user", tags=["用户模块"])
app.include_router(bot_routers.router, prefix=f"{API_PATH}/bot", tags=["会话模块"])
app.include_router(admin_routers.router, prefix=f"{API_PATH}/admin", tags=["管理员模块"])

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
        # "file_default": {
        #     "formatter": "default",
        #     "class": "logging.handlers.TimedRotatingFileHandler",
        #     "filename": "./server.log",
        # },
        # "file_access": {
        #     "formatter": "access",
        #     "class": "logging.handlers.TimedRotatingFileHandler",
        #     "filename": "./server.log",
        # },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {
            "handlers": ["access"],
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
