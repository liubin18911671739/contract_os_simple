#!/bin/bash
# Docker 部署快速启动脚本

set -e

echo "🚀 Contract OS Simple - Docker 部署"
echo "======================================"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查环境变量
if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在，从 .env.example 创建..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
    echo "⚠️  请编辑 .env 文件，设置 ZHIPU_API_KEY"
    echo "   nano .env"
    exit 1
fi

# 检查 API 密钥
if grep -q "your-key-here\|your-actual-api-key-here" .env; then
    echo "⚠️  请先在 .env 文件中设置有效的 ZHIPU_API_KEY"
    exit 1
fi

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data storage/contracts storage/kb_documents storage/reports

# 构建镜像
echo "🔨 构建 Docker 镜像..."
docker-compose build

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 健康检查
echo "🔍 检查服务状态..."
if curl -f http://localhost:8000/api/health &> /dev/null; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "📋 服务信息:"
    echo "   - API 地址: http://localhost:8000"
    echo "   - API 文档: http://localhost:8000/docs"
    echo "   - 健康检查: http://localhost:8000/api/health"
    echo ""
    echo "📊 查看日志:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 停止服务:"
    echo "   docker-compose down"
else
    echo "❌ 服务启动失败，请查看日志:"
    echo "   docker-compose logs"
    exit 1
fi
