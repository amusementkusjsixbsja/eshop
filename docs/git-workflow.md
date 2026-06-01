# Git 使用流程

## 仓库地址

```
https://github.com/amusementkusjsixbsja/eshop.git
```

## 分支策略

```
main ── 稳定可运行版本
  │
  ├── develop ── 集成分支（所有人合入这里）
  │
  ├── feat/xiaoa-frontend      ★ 小A：前端
  ├── feat/xiaoa-ai-service    ★ 小A：AI 服务
  ├── feat/xiaob-user-product  ★ 小B：用户与商品
  ├── feat/xiaoc-order-trade   ★ 小C：交易服务
  └── feat/xiaod-admin         ★ 小D：管理后台
```

## 日常流程

### 首次使用

```bash
# 克隆仓库
git clone https://github.com/amusementkusjsixbsja/eshop.git
cd eshop

# 切到自己的分支（示例：小B）
git checkout -b feat/xiaob-user-product
```

### 每天开发

```bash
# 1. 拉取最新 main（框架更新时）
git fetch origin
git rebase origin/main

# 2. 开发…只修改自己的文件夹
#    小B 只改 service-user-product/ 下的文件

# 3. 提交
git add service-user-product/  # 只 add 自己文件夹
git commit -m "[user-product] 实现了XX功能"
git push origin feat/xiaob-user-product
```

### 合并到 develop

```bash
# 在自己分支上完成一个独立功能后
# 在 GitHub 上创建 Pull Request：自己的分支 → develop
# 至少 1 人 Review → 合入
```

### 关键规则

1. **只改自己文件夹** — 这是零冲突的保证
2. **提交信息格式** — `[模块] 做了什么`
3. **每天至少提交一次** — 避免丢失进度
4. **不要直接 push main 和 develop** — 必须通过 PR
