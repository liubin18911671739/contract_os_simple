# API 文档 | API Documentation

本文档详细描述 Contract OS Simple 的所有 API 端点、请求/响应格式和使用示例。

This document provides comprehensive API endpoint documentation, request/response formats, and usage examples for Contract OS Simple.

## 目录 | Table of Contents

- [API 概述](#api-概述)
- [合同管理 API](#合同管理-api)
- [任务管理 API](#任务管理-api)
- [知识库管理 API](#知识库管理-api)
- [仪表盘 API](#仪表盘-api)
- [健康检查 API](#健康检查-api)
- [错误处理](#错误处理)
- [身份认证](#身份认证)

## API 概述

### 基础信息

- **Base URL**: `http://localhost:8000` (开发环境)
- **API 版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8
- **兼容性**: 100% 兼容原 Node.js 版本

### 交互式文档

FastAPI 自动生成交互式 API 文档：

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### 通用响应格式

#### 成功响应

```json
{
  "status": "success",
  "data": { ... }
}
```

#### 错误响应

```json
{
  "error": "错误描述信息",
  "detail": "详细错误信息（可选）"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 合同管理 API

### 1. 创建合同

创建新合同记录。

**端点**: `POST /api/contracts`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "contract_name": "供应商服务合同",
  "counterparty": "某某科技有限公司",
  "contract_type": "采购合同"
}
```

字段说明：
- `contract_name` (string, 必需): 合同名称
- `counterparty` (string, 可选): 合同对方
- `contract_type` (string, 可选): 合同类型

**响应示例**:
```json
{
  "id": "1",
  "contract_name": "供应商服务合同",
  "counterparty": "某某科技有限公司",
  "contract_type": "采购合同",
  "created_at": "2024-01-01T00:00:00Z",
  "versions": []
}
```

**错误示例**:
```json
{
  "error": "合同名称不能为空"
}
```

**cURL 示例**:
```bash
curl -X POST "http://localhost:8000/api/contracts" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_name": "供应商服务合同",
    "counterparty": "某某科技有限公司",
    "contract_type": "采购合同"
  }'
```

### 2. 获取合同详情

获取合同及其版本信息。

**端点**: `GET /api/contracts/{id}`

**路径参数**:
- `id` (string): 合同 ID

**响应示例**:
```json
{
  "id": "1",
  "contract_name": "供应商服务合同",
  "counterparty": "某某科技有限公司",
  "contract_type": "采购合同",
  "created_at": "2024-01-01T00:00:00Z",
  "versions": [
    {
      "id": "1",
      "version_number": 1,
      "file_name": "contract_v1.pdf",
      "upload_time": "2024-01-01T00:00:00Z",
      "status": "ACTIVE"
    }
  ]
}
```

**cURL 示例**:
```bash
curl -X GET "http://localhost:8000/api/contracts/1"
```

### 3. 上传合同版本

上传合同文件并创建新版本。

**端点**: `POST /api/contracts/{id}/versions`

**请求类型**: `multipart/form-data`

**表单字段**:
- `file` (file, 必需): 合同文件（PDF/DOCX/TXT）
- `version_number` (integer, 可选): 版本号，默认自动递增

**响应示例**:
```json
{
  "success": true,
  "id": "1"
}
```

**cURL 示例**:
```bash
curl -X POST "http://localhost:8000/api/contracts/1/versions" \
  -F "file=@/path/to/contract.pdf" \
  -F "version_number=1"
```

## 任务管理 API

### 4. 创建预审任务

创建新的合同预审任务并启动处理流程。

**端点**: `POST /api/precheck-tasks`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "contract_version_id": "1",
  "kb_collection_ids": ["1", "2"],
  "kb_mode": "STRICT",
  "template_id": null
}
```

字段说明：
- `contract_version_id` (string, 必需): 合同版本 ID
- `kb_collection_ids` (array, 必需): 知识库集合 ID 列表
- `kb_mode` (string, 可选): KB 模式，"STRICT" 或 "RELAXED"，默认 "STRICT"
- `template_id` (string, 可选): 报告模板 ID

**响应示例**:
```json
{
  "id": "1",
  "contract_name": "供应商服务合同",
  "status": "QUEUED",
  "progress": 0,
  "current_stage": null,
  "error_message": null,
  "cancel_requested": false,
  "kb_mode": "STRICT",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**cURL 示例**:
```bash
curl -X POST "http://localhost:8000/api/precheck-tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_version_id": "1",
    "kb_collection_ids": ["1", "2"],
    "kb_mode": "STRICT"
  }'
```

### 5. 获取任务详情

获取任务的当前状态和进度。

**端点**: `GET /api/precheck-tasks/{id}`

**路径参数**:
- `id` (string): 任务 ID

**响应示例**:
```json
{
  "id": "1",
  "contract_name": "供应商服务合同",
  "status": "PROCESSING",
  "progress": 75,
  "current_stage": "LLM_RISK",
  "error_message": null,
  "cancel_requested": false,
  "kb_mode": "STRICT",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z"
}
```

**状态说明**:
- `QUEUED`: 队列中
- `PARSING`: 解析中
- `STRUCTURING`: 结构化中
- `PROCESSING`: 处理中
- `COMPLETED`: 已完成
- `FAILED`: 失败
- `CANCELLED`: 已取消

**cURL 示例**:
```bash
curl -X GET "http://localhost:8000/api/precheck-tasks/1"
```

### 6. 列出任务

获取任务列表，支持分页、筛选和排序。

**端点**: `GET /api/precheck-tasks`

**查询参数**:
- `page` (integer, 可选): 页码，默认 1
- `limit` (integer, 可选): 每页数量，默认 10
- `status` (string, 可选): 按状态筛选
- `contract_id` (string, 可选): 按合同 ID 筛选
- `sort_by` (string, 可选): 排序字段，默认 "created_at"
- `order` (string, 可选): 排序方向，"asc" 或 "desc"，默认 "desc"

**响应示例**:
```json
{
  "tasks": [
    {
      "id": "1",
      "contract_name": "供应商服务合同",
      "status": "COMPLETED",
      "progress": 100,
      "current_stage": "DONE",
      "error_message": null,
      "cancel_requested": false,
      "kb_mode": "STRICT",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:10:00Z"
    },
    {
      "id": "2",
      "contract_name": "劳动合同",
      "status": "PROCESSING",
      "progress": 50,
      "current_stage": "KB_RETRIEVAL",
      "error_message": null,
      "cancel_requested": false,
      "kb_mode": "RELAXED",
      "created_at": "2024-01-01T01:00:00Z",
      "updated_at": "2024-01-01T01:05:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 10
}
```

**cURL 示例**:
```bash
# 获取第一页
curl -X GET "http://localhost:8000/api/precheck-tasks?page=1&limit=10"

# 筛选已完成任务
curl -X GET "http://localhost:8000/api/precheck-tasks?status=COMPLETED"

# 按创建时间升序排列
curl -X GET "http://localhost:8000/api/precheck-tasks?sort_by=created_at&order=asc"
```

### 7. 获取任务事件日志

获取任务的详细处理日志。

**端点**: `GET /api/precheck-tasks/{id}/events`

**路径参数**:
- `id` (string): 任务 ID

**响应示例**:
```json
[
  {
    "id": "1",
    "ts": "2024-01-01T00:00:01Z",
    "stage": "PARSING",
    "level": "INFO",
    "message": "开始解析文件",
    "meta": {
      "file_name": "contract.pdf",
      "file_size": 1024000
    }
  },
  {
    "id": "2",
    "ts": "2024-01-01T00:00:05Z",
    "stage": "PARSING",
    "level": "INFO",
    "message": "文件解析完成",
    "meta": {
      "text_length": 5000,
      "duration_ms": 4000
    }
  },
  {
    "id": "3",
    "ts": "2024-01-01T00:00:10Z",
    "stage": "LLM_RISK",
    "level": "ERROR",
    "message": "LLM API 调用失败",
    "meta": {
      "error": "API rate limit exceeded"
    }
  }
]
```

**日志级别**:
- `DEBUG`: 调试信息
- `INFO`: 一般信息
- `WARNING`: 警告
- `ERROR`: 错误

**cURL 示例**:
```bash
curl -X GET "http://localhost:8000/api/precheck-tasks/1/events"
```

### 8. 取消任务

取消正在处理的任务。

**端点**: `POST /api/precheck-tasks/{id}/cancel`

**路径参数**:
- `id` (string): 任务 ID

**响应示例**:
```json
{
  "success": true,
  "id": "1"
}
```

**cURL 示例**:
```bash
curl -X POST "http://localhost:8000/api/precheck-tasks/1/cancel"
```

### 9. 获取任务统计摘要

获取任务的风险统计信息。

**端点**: `GET /api/precheck-tasks/{id}/summary`

**路径参数**:
- `id` (string): 任务 ID

**响应示例**:
```json
{
  "clause_count": 25,
  "high_risks": 3,
  "medium_risks": 8,
  "low_risks": 12,
  "info_risks": 2
}
```

**cURL 示例**:
```bash
curl -X GET "http://localhost:8000/api/precheck-tasks/1/summary"
```

### 10. 获取任务条款和风险

获取任务的所有条款及对应的风险分析。

**端点**: `GET /api/precheck-tasks/{id}/clauses`

**路径参数**:
- `id` (string): 任务 ID

**响应示例**:
```json
[
  {
    "id": "1",
    "clause_id": "clause_001",
    "title": "第一条 合同标的",
    "text": "甲方向乙方采购...",
    "order_no": 1,
    "risk_id": "1",
    "risk_level": "HIGH",
    "risk_summary": "存在不平等条款风险",
    "risk_status": "PENDING"
  },
  {
    "id": "2",
    "clause_id": "clause_002",
    "title": "第二条 付款方式",
    "text": "付款方式为...",
    "order_no": 2,
    "risk_id": null,
    "risk_level": null,
    "risk_summary": null,
    "risk_status": null
  }
]
```

**风险级别**:
- `HIGH`: 高风险
- `MEDIUM`: 中风险
- `LOW`: 低风险
- `INFO`: 信息性

**风险状态**:
- `PENDING`: 待处理
- `APPROVED`: 已批准
- `MODIFIED`: 已修改
- `ESCALATED`: 已升级

**cURL 示例**:
```bash
curl -X GET "http://localhost:8000/api/precheck-tasks/1/clauses"
```

### 11. 设置任务结论

为任务设置审核结论。

**端点**: `POST /api/precheck-tasks/{id}/conclusion`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "conclusion": "APPROVE",
  "notes": "合同条款整体合规，建议签署"
}
```

字段说明：
- `conclusion` (string, 必需): 结论类型
  - `APPROVE`: 批准
  - `MODIFY`: 需要修改
  - `ESCALATE`: 需要升级处理
- `notes` (string, 可选): 审核备注

**响应示例**:
```json
{
  "success": true,
  "id": "1"
}
```

**cURL 示例**:
```bash
curl -X POST "http://localhost:8000/api/precheck-tasks/1/conclusion" \
  -H "Content-Type: application/json" \
  -d '{
    "conclusion": "APPROVE",
    "notes": "合同条款整体合规"
  }'
```

### 12. 生成报告

为任务生成审核报告。

**端点**: `POST /api/precheck-tasks/{id}/report`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "format": "html"
}
```

字段说明：
- `format` (string, 可选): 报告格式，"html" 或 "pdf"，默认 "html"

**响应示例**:
```json
{
  "success": true,
  "id": "1",
  "report_url": "/storage/reports/task_1_report.html"
}
```

**cURL 示例**:
```bash
curl -X POST "http://localhost:8000/api/precheck-tasks/1/report" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "html"
  }'
```

## 知识库管理 API

### 13. 创建知识库集合

创建新的知识库集合。

**端点**: `POST /api/kb/collections`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "合同法规知识库",
  "scope": "GLOBAL"
}
```

字段说明：
- `name` (string, 必需): 集合名称
- `scope` (string, 可选): 作用域，"GLOBAL" 或 "ORGANIZATION"，默认 "GLOBAL"

**响应示例**:
```json
{
  "id": "1",
  "name": "合同法规知识库",
  "scope": "GLOBAL",
  "version": 1,
  "is_enabled": true,
  "document_count": 0,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**cURL 示例**:
```bash
curl -X POST "http://localhost:8000/api/kb/collections" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "合同法规知识库",
    "scope": "GLOBAL"
  }'
```

### 14. 列出知识库集合

获取所有知识库集合。

**端点**: `GET /api/kb/collections`

**响应示例**:
```json
[
  {
    "id": "1",
    "name": "合同法规知识库",
    "scope": "GLOBAL",
    "version": 1,
    "is_enabled": true,
    "document_count": 15,
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": "2",
    "name": "合同最佳实践",
    "scope": "GLOBAL",
    "version": 1,
    "is_enabled": true,
    "document_count": 8,
    "created_at": "2024-01-02T00:00:00Z"
  }
]
```

**cURL 示例**:
```bash
curl -X GET "http://localhost:8000/api/kb/collections"
```

### 15. 获取知识库集合详情

获取知识库集合的详细信息。

**端点**: `GET /api/kb/collections/{id}`

**路径参数**:
- `id` (string): 集合 ID

**响应示例**:
```json
{
  "id": "1",
  "name": "合同法规知识库",
  "scope": "GLOBAL",
  "version": 1,
  "is_enabled": true,
  "document_count": 15,
  "created_at": "2024-01-01T00:00:00Z",
  "documents": [
    {
      "id": "1",
      "title": "合同法实施细则",
      "doc_type": "REGULATION",
      "upload_time": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**cURL 示例**:
```bash
curl -X GET "http://localhost:8000/api/kb/collections/1"
```

### 16. 删除知识库集合

删除知识库集合及其所有数据。

**端点**: `DELETE /api/kb/collections/{id}`

**路径参数**:
- `id` (string): 集合 ID

**响应示例**:
```json
{
  "success": true,
  "id": "1"
}
```

**cURL 示例**:
```bash
curl -X DELETE "http://localhost:8000/api/kb/collections/1"
```

### 17. 导入知识库文档

向知识库集合导入文档。

**端点**: `POST /api/kb/collections/{id}/documents`

**请求类型**: `multipart/form-data`

**表单字段**:
- `title` (string, 必需): 文档标题
- `doc_type` (string, 必需): 文档类型
- `file` (file, 必需): 文档文件

**响应示例**:
```json
{
  "success": true,
  "id": "1"
}
```

**cURL 示例**:
```bash
curl -X POST "http://localhost:8000/api/kb/collections/1/documents" \
  -F "title=合同法实施细则" \
  -F "doc_type=REGULATION" \
  -F "file=@/path/to/document.pdf"
```

## 仪表盘 API

### 18. 获取仪表盘统计数据

获取系统整体统计信息。

**端点**: `GET /api/dashboard/stats`

**响应示例**:
```json
{
  "total_tasks": 150,
  "active_tasks": 5,
  "completed_tasks": 140,
  "failed_tasks": 5,
  "total_contracts": 50,
  "total_kb_collections": 3
}
```

**cURL 示例**:
```bash
curl -X GET "http://localhost:8000/api/dashboard/stats"
```

## 健康检查 API

### 19. 健康检查

检查服务健康状态。

**端点**: `GET /api/health`

**响应示例**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**cURL 示例**:
```bash
curl -X GET "http://localhost:8000/api/health"
```

## 错误处理

### 错误响应格式

所有错误返回统一格式：

```json
{
  "error": "错误描述",
  "detail": "详细错误信息（可选）"
}
```

### 常见错误

#### 400 Bad Request

请求参数错误。

```json
{
  "error": "contract_name is required"
}
```

#### 404 Not Found

资源不存在。

```json
{
  "error": "Task not found"
}
```

#### 500 Internal Server Error

服务器内部错误。

```json
{
  "error": "Internal server error",
  "detail": "Failed to process LLM request"
}
```

## 身份认证

### 当前版本

当前版本暂未实现身份认证。所有端点都可以直接访问。

### 未来计划

计划支持以下认证方式：

- JWT Token 认证
- API Key 认证
- OAuth 2.0

### 使用示例

将来可能的使用方式：

```bash
# 使用 JWT Token
curl -X GET "http://localhost:8000/api/precheck-tasks" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 使用 API Key
curl -X GET "http://localhost:8000/api/precheck-tasks" \
  -H "X-API-Key: YOUR_API_KEY"
```

## 速率限制

### 当前版本

当前版本未实现速率限制。

### 推荐配置

生产环境建议使用 Nginx 配置速率限制：

```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        location /api/ {
            limit_req zone=api burst=20;
        }
    }
}
```

## 最佳实践

### 1. 轮询任务状态

创建任务后，使用轮询方式检查进度：

```javascript
async function checkTaskStatus(taskId) {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/precheck-tasks/${taskId}`);
    const task = await response.json();

    if (task.status === 'COMPLETED' || task.status === 'FAILED') {
      clearInterval(interval);
      console.log('Task completed:', task);
    }
  }, 2000); // 每 2 秒检查一次
}
```

### 2. 错误重试

对于网络错误，实现指数退避重试：

```javascript
async function retryRequest(url, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000));
    }
  }
}
```

### 3. 批量处理

对于大量任务，使用并发控制：

```javascript
async function processTasks(taskIds, concurrency = 3) {
  const results = [];
  for (let i = 0; i < taskIds.length; i += concurrency) {
    const batch = taskIds.slice(i, i + concurrency);
    const batchResults = await Promise.all(
      batch.map(id => fetch(`/api/precheck-tasks/${id}`))
    );
    results.push(...batchResults);
  }
  return results;
}
```

## 相关文档

- [开发指南](DEVELOPMENT_GUIDE.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
- [故障排除](TROUBLESHOOTING.md)
