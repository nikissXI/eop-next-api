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
- 2099    其他请求错误
  
30XX 服务器处理错误
- 3001    服务器出错
- 3008    Poe登陆失败
