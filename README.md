# 本仓库为纯后端，前端需自行另外实现

接口文档运行后访问路径/docs或/redoc  

require Python environment >= 3.11

安装依赖库 pip install -r requirements.txt

运行 python main.py

把config.txt.example改名config.txt，并按需求进行填写配置  

初始管理员账号 admin/admin 密码密文 8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918

20XX 客户端处理错误  
- 2000    认证失败：密码错误、权限不足等  
- 2001    请求错误
- 2003    文件类型不支持
- 2004    文件过大
- 2005    会话已被删除
- 2009    用户授权过期，无法创建和对话
- 2010    可用积分不足
  
30XX 服务器端处理错误
- 3001    后端出错


# 登陆凭证获取
poe登录凭证需要3个值，获取方法如下  
浏览器登陆[poe官网](https://poe.com/)，打开开发者工具（一般是按F12），再F11（刷新），找到网络监听模块，搜索链接 https://poe.com/api/gql_POST ，然后在请求头中找到图中的三个值  
分别为p-b，p-lat，Poe-Formkey  
<img width="100%" src="https://raw.githubusercontent.com/nikissXI/eop-next-api/main/readme_img/1.jpg"/>  

# 更新日志
## 2024/09/01
- 完全重构
## 2024/06/25
- 完全重构