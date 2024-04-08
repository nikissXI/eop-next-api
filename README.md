接口文档运行后访问路径/docs或/redoc  

# 本仓库为纯后端，前端需自行另外实现

require Python environment >= 3.10

安装依赖库 pip install -r requirements.txt

运行 python main.py

把.env.example改名.env  
配置文件是 .env

初始管理员账号 nikiss/nikiss 密码密文 f303aabb3a5bd6a547e3fdbf664bc7e093db187339048c74a0b19f8ebab42d3c

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


# 登陆凭证获取
poe登录凭证需要3个值，获取方法如下  
浏览器登陆[poe官网](https://poe.com/)，打开开发者工具（一般是按F12），再F11（刷新），找到网络监听模块，搜索链接https://poe.com/api/gql_POST，然后在请求头中找到图中的三个值  
分别为p-b，p-lat，Poe-Formkey  
<img width="100%" src="https://raw.githubusercontent.com/nikissXI/eop-next-api/main/readme_img/1.jpg"/>  

# 更新日志
## 2024/4/8
- 需要一个新的登陆凭证字段p-lat
- 优化了ws重连机制

## 2023/10/6
- /bot/talk 接口改动，还有挺多东西改动（反正没啥人用，随便啦~

## 2023/9/10
- /user/bots 接口内容增加了image字段，对应模型的头像链接

## 2023/9/19
原来的admin字段改为level，0是管理员，1是普通用户，2是高级用户
- /admin/user/add 接口变更，请求体中的admin字段改为level字段
- /user/info 接口变更，请响应体的is_admin字段改为level字段
- /admin/user/renew 请求体增加level字段

## 2023/9/20
- 增加用户分级限制，普通用户无法调用限次数的模型

## 2023/9/21
- /admin/user/add 接口创建用户成功后返回uid
- /admin/{uid}/delete 接口{user}改为{uid}
- /admin/{uid}/renew 接口{user}改为{uid}
- /admin/{uid}/resetPasswd 接口{user}改为{uid}
- /admin/listUser 接口结果字段增加uid
- /admin/getSetting 接口结果增加telegram_url, discord_url, weixin_url, qq_url字段
- /admin/updateSetting 接口请求体增加telegram_url, discord_url, weixin_url, qq_url字段
- /user/info 接口结果响应字段改为user, uid, level, expire_date

## 2023/9/22
- /bot/limited 接口移除，新增接口 /admin/accountInfo
- 会话列表接口 /user/bots 改为 /bot/list，且响应字段增加 disable 用于判断是否可用
- talk的响应type增加 expired 账号过期，denied 权限不足，deleted 会话不存在，disable 会话无法使用
- PATCH /bot/{eop_id} 接口增加 2011 响应码（会话失效）
- 支持热更新最新模型

## 2023/9/30
- /bot/talk 接口，type：start改为type：msg_info，type：end移除，type：response的data改为{"complete": true/false,"content": 内容}
