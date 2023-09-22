接口文档运行后访问路径/docs或/redoc  

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
- 2099    其他请求错误
  
30XX 服务器处理错误
- 3001    服务器出错
- 3008    Poe登陆失败


# 登陆凭证获取
poe登录凭证需要两个值，获取方法如下：  

**p_b值** 浏览器登陆[poe官网](https://poe.com/)，打开开发者工具（一般是按F12），依次点击应用程序、存储、Cookie，就可以看到p_b的值了  
<img width="100%" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_talk_with_poe_ai/readme_img/2.jpg"/>  

**formkey值** 浏览器登陆[poe官网](https://poe.com/)，打开开发者工具（一般是按F12），然后随便跟一个ai发一句话，点网络，选Fetch/XHR，随便一个请求，在标头那，往下找到请求标头那类，里面有一个Poe-Formkey字段，后面就是值了  
<img width="100%" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_talk_with_poe_ai/readme_img/3.jpg"/>  

# 更新日志
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
- 增加失效会话判断处理
- /user/bots 改为 /bot/list
- talk的响应type增加 expired 账号过期，denied 权限不足，deleted 会话不存在，disable 会话无法使用