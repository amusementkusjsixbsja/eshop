"""用户业务逻辑层。

★ 小B：将此文件填充为真实的数据库操作（当前为空，业务逻辑写在 routers/ 中作为 stub）。

当路由数量增多时，将业务逻辑从 router 迁移到此处：
  1. 注册：校验唯一性 → bcrypt → INSERT
  2. 登录：查询 → bcrypt 比对 → JWT 签发
  3. 查询个人信息 → SELECT
  4. 更新地址 → UPDATE

参考：shop_shared.infrastructure.database.get_cursor()
"""
