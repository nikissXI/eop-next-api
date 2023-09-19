## 2023/9/10
/user/bots 接口内容增加了image字段，对应模型的头像链接

## 2023/9/19
原来的admin字段改为level，0是管理员，1是普通用户，2是高级用户
/admin/user/add 接口变更，请求体中的admin字段改为level字段
/user/info 接口变更，请响应体的is_admin字段改为level字段

新增修改用户级别的接口
/admin/{user}/level/{level}