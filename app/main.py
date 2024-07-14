from contextlib import asynccontextmanager

import models.error_resp_models as resp_models
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
from routers.admin_routers import router as admin_router
from routers.user_routers import router as user_router
from services.jwt_auth import AuthFailed
from services.poe_client import login_poe, scheduler
from utils.env_util import gv
from utils.tool_util import Custom404Middleware, fastapi_logger_config, logger
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
    logger.info("启动完成")
    yield
    await db_close()
    logger.info("程序退出")


app = FastAPI(
    lifespan=lifespan,
    description="""require Python environment >= 3.10

20XX 客户端处理错误  
- 2000    认证失败：密码错误、权限不足等  
- 2001    请求错误
- 2009    用户授权过期，无法创建和对话
- 2010    可用积分不足
  
30XX 服务器端处理错误
- 3001    后端出错
""",
    responses={
        422: {
            "description": "请求错误",
            "model": resp_models.Response422,
        },
    },
)
# HTTPS重定向
# app.add_middleware(HTTPSRedirectMiddleware)

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=gv.ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 屏蔽404的日志
app.add_middleware(Custom404Middleware)


################
### 错误处理
################
@app.exception_handler(RequestValidationError)
async def _(request: Request, exc: RequestValidationError):
    return JSONResponse({"code": 2001, "msg": repr(exc)}, 422)


@app.exception_handler(AuthFailed)
async def _(request: Request, exc: AuthFailed):
    return JSONResponse({"code": 2000, "msg": exc.error_type}, 401)


################
### 添加路由
################
app.include_router(user_router, prefix=f"{gv.API_PATH}/user", tags=["用户模块"])
app.include_router(admin_router, prefix=f"{gv.API_PATH}/admin", tags=["管理员模块"])

################
### 启动进程
################
if __name__ == "__main__":
    try:
        run(
            app,
            host=gv.HOST,
            port=gv.PORT,
            ssl_keyfile=gv.SSL_KEYFILE_PATH,
            ssl_certfile=gv.SSL_CERTFILE_PATH,
            log_config=fastapi_logger_config,
            headers=[("server", "EOP")],  # 修改响应头里的默认server字段
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"uvicorn出错：{repr(e)}")
