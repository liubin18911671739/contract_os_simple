# 测试指南

## 快速开始

### 运行所有测试

```bash
# 从项目根目录运行
pytest

# 或者指定测试目录
pytest server/tests
```

### 运行特定测试文件

```bash
pytest server/tests/test_task_service.py
```

### 运行特定测试

```bash
pytest server/tests/test_task_service.py::test_create_task
```

### 运行测试并查看覆盖率

```bash
# 生成覆盖率报告
pytest --cov=server --cov-report=html

# 查看报告（macOS）
open htmlcov/index.html

# 查看报告（Linux）
xdg-open htmlcov/index.html

# 查看报告（Windows）
start htmlcov/index.html
```

## 测试环境变量

测试会自动使用测试环境变量（在 `server/tests/conftest.py` 中设置）：

- `ZHIPU_API_KEY=test_key_for_unit_tests`
- `DATABASE_PATH=/tmp/test_db.db`
- `STORE_ROOT=/tmp/test_storage`

无需手动配置 `.env` 文件。

## 测试结构

```
server/tests/
├── conftest.py              # 测试配置和 fixtures
├── test_task_service.py     # TaskService 测试
├── test_agents.py           # Agent 测试
└── benchmarks.py            # 性能基准测试
```

## 可用的 Fixtures

### test_db
创建临时测试数据库：

```python
@pytest.mark.asyncio
async def test_something(test_db):
    # test_db 是一个 AsyncSession 实例
    result = await test_db.execute(query)
```

### test_settings
创建测试配置：

```python
def test_something(test_settings):
    # test_settings 是一个 Settings 实例
    assert test_settings.zhipu_api_key == "test_key"
```

### sample_contract_text
示例合同文本：

```python
def test_something(sample_contract_text):
    # 返回标准的测试合同文本
    assert "SOFTWARE DEVELOPMENT AGREEMENT" in sample_contract_text
```

### sample_kb_document
示例 KB 文档：

```python
def test_something(sample_kb_document):
    # 返回标准的测试 KB 文档
    assert "Software Contract Risk Guidelines" in sample_kb_document
```

## 编写测试

### 基本测试示例

```python
import pytest
from server.services.task_service import TaskService

@pytest.mark.asyncio
async def test_create_task(test_db):
    """Test creating a new task"""
    service = TaskService(test_db)
    task_id = await service.create_task(
        contract_version_id="version_123",
        kb_collection_ids=["kb_col_1"],
        kb_mode="STRICT",
    )
    assert task_id is not None
    assert task_id.startswith("task_")
```

### 使用 mock 的测试示例

```python
import pytest
from unittest.mock import patch
from server.agents.parse_agent import ParseAgent

@pytest.mark.asyncio
async def test_parse_agent(test_db, sample_contract_text):
    """Test ParseAgent with mocked file service"""
    with patch("server.agents.parse_agent.FileService") as mock_fs:
        mock_fs.return_value.get_file_content.return_value \
            = sample_contract_text.encode()

        agent = ParseAgent(test_db)
        result = await agent.execute(version_id="123", {})

    assert result is not None
```

## 性能测试

运行性能基准测试：

```bash
python server/tests/benchmarks.py
```

这会输出：
- 任务处理性能
- 数据库查询性能
- LLM 分析性能（模拟）
- KB 检索性能（模拟）

## 故障排除

### ImportError: No module named 'server'

**问题**: pytest 无法找到 server 模块

**解决方案**: 确保从项目根目录运行 pytest

```bash
# ✓ 正确
cd /path/to/contract_os_simple
pytest server/tests

# ✗ 错误
cd server/tests
pytest .
```

### ValidationError: Field required

**问题**: 缺少必需的环境变量

**解决方案**: 测试会自动设置测试环境变量。如果仍有问题，确保 conftest.py 在导入 server 模块前设置了环境变量。

### 数据库锁定错误

**问题**: 测试数据库文件被锁定

**解决方案**: 每个测试使用独立的临时数据库，自动清理。如果仍有问题：

```bash
# 清理临时文件
rm -f /tmp/test_db*
rm -rf /tmp/test_storage
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r server/requirements.txt

    - name: Run tests
      run: |
        pytest --cov=server --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 最佳实践

1. **使用 fixtures**: 复用测试数据和配置
2. **隔离测试**: 每个测试应该独立，不依赖其他测试
3. **清理资源**: 使用临时文件和数据库
4. **mock 外部依赖**: LLM API、文件系统等
5. **描述性命名**: 测试名称应该清楚描述测试内容
6. **异步测试**: 使用 `@pytest.mark.asyncio` 装饰器
7. **覆盖率目标**: 努力达到 > 80% 的覆盖率

## 相关文档

- [pytest 文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [SQLAlchemy 异步测试](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
