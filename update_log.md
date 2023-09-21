## 2023/9/10
/user/bots 接口内容增加了image字段，对应模型的头像链接

## 2023/9/19
原来的admin字段改为level，0是管理员，1是普通用户，2是高级用户
/admin/user/add 接口变更，请求体中的admin字段改为level字段
/user/info 接口变更，请响应体的is_admin字段改为level字段
/admin/user/renew 请求体增加level字段

## 2023/9/20
增加用户分级限制，普通用户无法调用限次数的模型

## 2023/9/21
/admin/user/add 接口创建用户成功后返回uid
/admin/{uid}/delete 接口{user}改为{uid}
/admin/{uid}/renew 接口{user}改为{uid}
/admin/{uid}/resetPasswd 接口{user}改为{uid}
/admin/listUser 接口结果字段增加uid
/admin/getSetting 接口结果增加telegram_url, discord_url, weixin_url, qq_url字段
/admin/updateSetting 接口请求体增加telegram_url, discord_url, weixin_url, qq_url字段
/user/info 接口结果响应字段改为user, uid, level, expire_date