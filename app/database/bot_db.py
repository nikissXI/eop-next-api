from tortoise import fields
from .db import Model
from time import time
from random import randint


class Bot(Model):
    id = fields.TextField(pk=True)  # uid-bot_id （两个ID组合）
    handle = fields.TextField()
    bot_id = fields.IntField()
    display_name = fields.TextField()  # 访问详情时更新
    description = fields.TextField()  # 访问详情时更新
    image_link = fields.TextField()  # 访问详情时更新
