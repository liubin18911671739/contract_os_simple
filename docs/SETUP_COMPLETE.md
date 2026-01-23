# ✅ 安装完成！

## 环境设置状态

- ✅ Python 虚拟环境已创建: `.venv`
- ✅ 所有依赖已安装
- ✅ 数据库已初始化: `data/database.db`
- ✅ 存储目录已创建: `storage/`

## 快速启动

### 1. 激活虚拟环境
```bash
source .venv/bin/activate
```

### 2. 配置环境变量
编辑 `.env` 文件，添加你的智谱AI API密钥：
```bash
nano .env  # 或使用你喜欢的编辑器
```

修改这一行：
```bash
ZHIPU_API_KEY=your-actual-api-key-here
```

**重要**: 确保你的智谱AI账户有足够的余额（embedding和rerank需要API调用）

### 3. 初始化示例数据（可选）
```bash
python scripts/seed_kb.py
```

这将创建两个示例知识库集合：
- Contract Regulations
- Contract Best Practices

**注意**: 如果API余额不足，集合仍会被创建，但文档不会导入embedding。你可以稍后通过API或UI导入。

### 4. 启动后端
```bash
cd server
python main.py
```

后端将运行在: `http://localhost:8000`
API文档: `http://localhost:8000/docs`

### 5. 启动前端（新终端）
```bash
cd client
npm install  # 如果还没安装
npm run dev
```

前端将运行在: `http://localhost:5173`

## 验证安装

检查所有关键包：
```bash
source .venv/bin/activate
python -c "import fastapi, sqlalchemy, faiss, zhipuai; print('✓ 所有包已正确安装')"
```

检查数据库：
```bash
ls -la data/database.db
```

## 项目结构
```
contract_os_simple/
├── .venv/              # Python虚拟环境
├── server/             # Python后端
├── client/             # React前端
├── data/               # 数据库文件
│   └── database.db     # SQLite数据库
├── storage/            # 文件存储
│   ├── contracts/
│   ├── kb_documents/
│   └── reports/
├── scripts/            # 工具脚本
└── .env               # 环境配置
```

## 故障排除

### IDE 显示"未安装包"
这是因为IDE可能没有选择虚拟环境。在VSCode中：
1. 按 `Cmd+Shift+P` (Mac) 或 `Ctrl+Shift+P` (Windows/Linux)
2. 输入 "Python: Select Interpreter"
3. 选择 `.venv` 虚拟环境

### 依赖问题
如果遇到依赖问题，重新安装：
```bash
source .venv/bin/activate
pip install -r server/requirements.txt --force-reinstall
```

### 数据库问题
如果数据库有问题，重新初始化：
```bash
rm data/database.db
source .venv/bin/activate
python scripts/init_db.py
```

## 下一步

1. **配置智谱AI密钥** - 编辑 `.env` 文件
2. **启动后端** - `cd server && python main.py`
3. **测试API** - 访问 http://localhost:8000/docs
4. **启动前端** - `cd client && npm run dev`
5. **创建测试任务** - 通过UI或API

## 有用的命令

```bash
# 激活虚拟环境
source .venv/bin/activate

# 停用虚拟环境
deactivate

# 查看已安装的包
pip list

# 启动后端（开发模式，自动重载）
cd server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 初始化示例KB数据
python scripts/seed_kb.py

# 查看数据库（SQLite命令行）
sqlite3 data/database.db ".tables"
```

## 需要帮助？

查看详细文档：
- [README.md](./README.md) - 完整项目文档
- [QUICKSTART.md](./QUICKSTART.md) - 10分钟快速指南
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 实现细节
