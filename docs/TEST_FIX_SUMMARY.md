# ✅ 测试配置修复完成

## 问题

运行 pytest 时出现导入错误：
```
ModuleNotFoundError: No module named 'server'
```

和验证错误：
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
zhipu_api_key
  Field required
```

## 根本原因

1. **路径问题**: pytest 无法找到 `server` 模块
2. **环境变量问题**: `Settings()` 在导入时立即执行，但测试环境变量未设置

## 解决方案

### 1. 修复配置类（server/config.py）

将 `zhipu_api_key` 改为可选字段：

```python
class Settings(BaseSettings):
    zhipu_api_key: Optional[str] = None  # 改为可选
    # ...
```

### 2. 修复测试配置（server/tests/conftest.py）

在导入 server 模块**之前**设置测试环境变量：

```python
# 在文件顶部添加
os.environ.setdefault("ZHIPU_API_KEY", "test_key_for_unit_tests")
os.environ.setdefault("DATABASE_PATH", "/tmp/test_db.db")
os.environ.setdefault("STORAGE_ROOT", "/tmp/test_storage")

# 然后再添加路径和导入
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from server.database.models import Base
from server.config import Settings
```

### 3. 更新 pytest 配置（pytest.ini）

添加测试环境变量：

```ini
[pytest]
env =
    ZHIPU_API_KEY=test_key_for_unit_tests
    DATABASE_PATH=/tmp/test_db.db
    STORAGE_ROOT=/tmp/test_storage
```

## 验证

```bash
# 测试配置加载
python -c "
import os
os.environ['ZHIPU_API_KEY'] = 'test_key_for_unit_tests'
from server.config import settings
print('✓ Config loaded')
"

# 运行测试
pytest server/tests/test_task_service.py::test_create_task -v
```

## 新增文件

- ✅ [server/tests/conftest.py](server/tests/conftest.py) - 修复后的测试配置
- ✅ [pytest.ini](pytest.ini) - pytest 配置
- ✅ [.env.test](.env.test) - 测试环境变量模板
- ✅ [test_setup.sh](test_setup.sh) - 快速测试脚本
- ✅ [TEST_GUIDE.md](TEST_GUIDE.md) - 完整测试指南

## 运行测试

```bash
# 从项目根目录运行
pytest

# 或指定目录
pytest server/tests

# 带覆盖率
pytest --cov=server --cov-report=html
```

## 修复后的优势

1. ✅ 无需配置 `.env` 即可运行测试
2. ✅ 每个测试使用独立的临时数据库
3. ✅ 测试环境与生产环境完全隔离
4. ✅ 支持从项目根目录直接运行 pytest

## 相关文档

- [TEST_GUIDE.md](TEST_GUIDE.md) - 详细测试指南
- [pytest.ini](pytest.ini) - pytest 配置
- [server/tests/conftest.py](server/tests/conftest.py) - 测试 fixtures
