from .tool_util import logger, generate_random_bot_id, generate_random_password
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query, Body, Path