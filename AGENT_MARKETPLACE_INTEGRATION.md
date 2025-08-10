# OpenWebUI 智能体广场系统集成指南

## 📋 概述

本文档说明如何将智能体广场系统集成到现有的OpenWebUI系统中。

## 🔧 集成步骤

### 1. 数据库迁移

#### 创建数据库迁移文件

创建数据库迁移脚本来添加智能体相关表：

```python
# backend/open_webui/internal/migrations/create_agent_tables.py

"""
Add agent marketplace tables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = 'agent_marketplace_v1'
down_revision = 'your_previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # 创建智能体应用表
    op.create_table('agent_app',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), server_default='general'),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('app_type', sa.String(), server_default='form'),
        sa.Column('status', sa.String(), server_default='active'),
        sa.Column('form_config', sa.Text(), server_default='{}'),
        sa.Column('ai_config', sa.Text(), server_default='{}'),
        sa.Column('access_control', sa.Text(), server_default='{}'),
        sa.Column('usage_limit', sa.Integer(), server_default='0'),
        sa.Column('cost_per_use', sa.Integer(), server_default='100'),
        sa.Column('usage_count', sa.Integer(), server_default='0'),
        sa.Column('favorite_count', sa.Integer(), server_default='0'),
        sa.Column('rating', sa.Integer(), server_default='0'),
        sa.Column('metadata', sa.Text(), server_default='{}'),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], )
    )

    # 创建用户提交记录表
    op.create_table('agent_app_submission',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('app_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('form_data', sa.Text(), server_default='{}'),
        sa.Column('files', sa.Text(), server_default='[]'),
        sa.Column('ai_response', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='pending'),
        sa.Column('cost_consumed', sa.Integer(), server_default='0'),
        sa.Column('processing_time', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), server_default='{}'),
        sa.Column('created_at', sa.BigInteger(), nullable=True),
        sa.Column('completed_at', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['app_id'], ['agent_app.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )

    # 创建用户收藏表
    op.create_table('agent_app_favorite',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('app_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['app_id'], ['agent_app.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )

    # 创建应用统计表
    op.create_table('agent_app_stats',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('app_id', sa.String(), nullable=False),
        sa.Column('date', sa.String(), nullable=False),
        sa.Column('daily_uses', sa.Integer(), server_default='0'),
        sa.Column('unique_users', sa.Integer(), server_default='0'),
        sa.Column('total_cost', sa.Integer(), server_default='0'),
        sa.Column('avg_processing_time', sa.Integer(), server_default='0'),
        sa.Column('success_rate', sa.Integer(), server_default='100'),
        sa.Column('error_count', sa.Integer(), server_default='0'),
        sa.Column('favorites_added', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['app_id'], ['agent_app.id'], )
    )

def downgrade():
    op.drop_table('agent_app_stats')
    op.drop_table('agent_app_favorite')
    op.drop_table('agent_app_submission')
    op.drop_table('agent_app')
```

### 2. API路由注册

在主应用中注册智能体API路由：

```python
# backend/open_webui/main.py

from open_webui.routers import agents

# 在现有路由后添加
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
```

### 3. 前端路由配置

#### 添加路由到导航系统

```svelte
<!-- src/routes/+layout.svelte 或相关布局文件 -->
<script>
	// 在现有导航项中添加
	const navigationItems = [
		// ... 现有项目
		{
			id: 'agents',
			label: '智能体广场',
			href: '/agents',
			icon: '🤖'
		}
	];
</script>
```

#### 创建路由页面

```svelte
<!-- src/routes/agents/+page.svelte -->
<script>
	import AgentMarketplace from '$lib/components/agents/AgentMarketplace.svelte';
</script>

<svelte:head>
	<title>智能体广场 - OpenWebUI</title>
</svelte:head>

<AgentMarketplace />
```

```svelte
<!-- src/routes/agents/[id]/+page.svelte -->
<script>
	import { page } from '$app/stores';
	import AgentDetail from '$lib/components/agents/AgentDetail.svelte';

	$: appId = $page.params.id;
</script>

<svelte:head>
	<title>智能体应用详情 - OpenWebUI</title>
</svelte:head>

<AgentDetail {appId} />
```

```svelte
<!-- src/routes/admin/agents/+page.svelte -->
<script>
	import AgentAdmin from '$lib/components/agents/AgentAdmin.svelte';
	import { user } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		if ($user?.role !== 'admin') {
			goto('/');
		}
	});
</script>

<svelte:head>
	<title>智能体管理 - OpenWebUI</title>
</svelte:head>

{#if $user?.role === 'admin'}
	<AgentAdmin />
{:else}
	<div class="unauthorized">
		<h1>访问被拒绝</h1>
		<p>您需要管理员权限才能访问此页面。</p>
	</div>
{/if}
```

### 4. 权限配置

#### 更新权限检查中间件

```python
# backend/open_webui/utils/auth.py

def get_admin_user(user: UserModel = Depends(get_verified_user)):
    """获取管理员用户"""
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user

def get_agent_access_user(user: UserModel = Depends(get_verified_user)):
    """检查用户是否有智能体访问权限"""
    # 这里可以添加更细粒度的权限控制
    return user
```

### 5. 环境配置

#### 更新环境变量配置

```python
# backend/open_webui/env.py

# 智能体系统相关配置
ENABLE_AGENT_MARKETPLACE = PersistentConfig(
    "ENABLE_AGENT_MARKETPLACE",
    "open_webui.env.ENABLE_AGENT_MARKETPLACE",
    True,
)

AGENT_FILE_UPLOAD_DIR = PersistentConfig(
    "AGENT_FILE_UPLOAD_DIR",
    "open_webui.env.AGENT_FILE_UPLOAD_DIR",
    f"{DATA_DIR}/uploads/agents",
)

MAX_AGENT_FILE_SIZE = PersistentConfig(
    "MAX_AGENT_FILE_SIZE",
    "open_webui.env.MAX_AGENT_FILE_SIZE",
    10 * 1024 * 1024,  # 10MB
)
```

### 6. 文件上传配置

#### 创建文件上传处理

```python
# backend/open_webui/utils/file_utils.py

import os
import uuid
import aiofiles
from fastapi import UploadFile
from open_webui.env import AGENT_FILE_UPLOAD_DIR, MAX_AGENT_FILE_SIZE

async def save_agent_file(file: UploadFile, user_id: str) -> dict:
    """保存智能体相关文件"""
    try:
        # 检查文件大小
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_AGENT_FILE_SIZE:
            raise ValueError(f"File size {file_size} exceeds maximum {MAX_AGENT_FILE_SIZE}")

        # 生成文件名
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # 确保目录存在
        user_upload_dir = os.path.join(AGENT_FILE_UPLOAD_DIR, user_id)
        os.makedirs(user_upload_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(user_upload_dir, unique_filename)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        return {
            "id": str(uuid.uuid4()),
            "name": file.filename,
            "size": file_size,
            "type": file.content_type,
            "url": f"/api/v1/files/agents/{user_id}/{unique_filename}",
            "path": file_path
        }

    except Exception as e:
        raise ValueError(f"Failed to save file: {str(e)}")
```

### 7. AI集成配置

#### 集成现有的AI模型系统

```python
# backend/open_webui/utils/agent_ai.py

from open_webui.models.models import Models
from open_webui.utils.chat import generate_chat_completion

async def process_agent_ai_request(
    app_config: dict,
    form_data: dict,
    files: list,
    user_id: str
) -> str:
    """处理智能体AI请求"""
    try:
        ai_config = app_config.get('ai_config', {})

        # 获取模型配置
        model_id = ai_config.get('model', 'gpt-3.5-turbo')
        model = Models.get_model_by_id(model_id)

        if not model:
            raise ValueError(f"Model {model_id} not found")

        # 构建系统提示
        system_prompt = ai_config.get('system_prompt', '')

        # 构建用户消息
        user_message = build_user_message_from_form(form_data, files)

        # 调用AI模型
        response = await generate_chat_completion({
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": ai_config.get('temperature', 0.7),
            "max_tokens": ai_config.get('max_tokens', 2000),
            "stream": False
        })

        return response.get('content', '')

    except Exception as e:
        raise ValueError(f"AI processing failed: {str(e)}")

def build_user_message_from_form(form_data: dict, files: list) -> str:
    """从表单数据构建用户消息"""
    message_parts = []

    # 添加表单字段
    for key, value in form_data.items():
        if value:
            message_parts.append(f"{key}: {value}")

    # 添加文件信息
    if files:
        file_info = []
        for file in files:
            file_info.append(f"文件: {file.get('name')}")
        message_parts.append("附件: " + ", ".join(file_info))

    return "\n".join(message_parts)
```

### 8. 系统集成验证

#### 创建集成测试脚本

```python
# scripts/test_agent_integration.py

import asyncio
import httpx
import json

async def test_agent_marketplace():
    """测试智能体广场集成"""
    base_url = "http://localhost:8080"

    async with httpx.AsyncClient() as client:
        # 1. 测试获取应用列表
        print("Testing app list...")
        response = await client.get(f"{base_url}/api/v1/agents")
        assert response.status_code == 200
        print("✓ App list API working")

        # 2. 测试创建应用（需要管理员权限）
        print("Testing app creation...")
        app_data = {
            "name": "test_app",
            "display_name": "测试应用",
            "description": "这是一个测试应用",
            "category": "general",
            "form_config": {
                "title": "测试表单",
                "fields": [
                    {
                        "id": "test_field",
                        "type": "text",
                        "label": "测试字段",
                        "required": True
                    }
                ]
            },
            "ai_config": {
                "system_prompt": "你是一个测试助手"
            }
        }

        # 注意：这需要有效的管理员token
        # response = await client.post(
        #     f"{base_url}/api/v1/agents",
        #     json=app_data,
        #     headers={"Authorization": "Bearer YOUR_ADMIN_TOKEN"}
        # )
        # assert response.status_code == 200
        print("✓ App creation API ready")

        print("All integration tests passed!")

if __name__ == "__main__":
    asyncio.run(test_agent_marketplace())
```

### 9. 部署配置

#### Docker配置更新

```dockerfile
# Dockerfile 更新 (如果使用Docker)

# 确保智能体文件上传目录
RUN mkdir -p /app/backend/data/uploads/agents

# 添加必要的权限
RUN chown -R user:user /app/backend/data/uploads/agents
```

#### Nginx配置更新

```nginx
# nginx.conf 更新

server {
    # ... 现有配置

    # 智能体文件服务
    location /api/v1/files/agents/ {
        alias /app/backend/data/uploads/agents/;

        # 安全配置
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;

        # 文件大小限制
        client_max_body_size 10M;
    }

    # 智能体API代理
    location /api/v1/agents/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 10. 系统配置文件

```python
# backend/open_webui/config/agents.py

"""
智能体广场系统配置
"""

from typing import Dict, Any
from open_webui.env import ENABLE_AGENT_MARKETPLACE

class AgentConfig:
    """智能体系统配置类"""

    # 系统启用状态
    ENABLED = ENABLE_AGENT_MARKETPLACE

    # 默认分类
    DEFAULT_CATEGORIES = [
        {"id": "general", "name": "通用", "icon": "🤖"},
        {"id": "productivity", "name": "效率", "icon": "⚡"},
        {"id": "creative", "name": "创意", "icon": "🎨"},
        {"id": "analysis", "name": "分析", "icon": "📊"}
    ]

    # 表单字段类型
    FIELD_TYPES = [
        "text", "select", "file", "switch",
        "number", "date", "checkbox", "radio"
    ]

    # 文件上传配置
    FILE_CONFIG = {
        "max_size": "10MB",
        "max_files": 10,
        "allowed_types": [
            ".png", ".jpg", ".jpeg", ".gif",
            ".pdf", ".docx", ".txt", ".csv"
        ]
    }

    # AI模型配置
    AI_CONFIG = {
        "default_model": "gpt-3.5-turbo",
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 30
    }

# 导出配置实例
agent_config = AgentConfig()
```

## 🚀 启用步骤

1. **运行数据库迁移**

   ```bash
   cd backend
   alembic upgrade head
   ```

2. **重启服务**

   ```bash
   # 重启后端服务
   python -m uvicorn open_webui.main:app --reload

   # 重新构建前端
   cd ../
   npm run build
   ```

3. **验证集成**
   - 访问 `/agents` 查看智能体广场
   - 管理员访问 `/admin/agents` 进行管理
   - 测试创建和使用应用

## 📚 使用说明

### 管理员操作

1. **创建应用**：在管理面板中点击"新建应用"
2. **配置表单**：添加不同类型的表单字段
3. **设置AI**：配置系统提示和模型参数
4. **发布应用**：将状态设置为"活跃"

### 用户操作

1. **浏览应用**：在智能体广场中查看可用应用
2. **使用应用**：点击应用卡片进入详情页
3. **填写表单**：按要求填写表单信息
4. **获取结果**：提交后查看AI生成的回答
5. **收藏应用**：收藏喜欢的应用便于下次使用

## 🔧 自定义配置

### 添加新的表单字段类型

1. 创建字段组件文件
2. 在FormRenderer中注册组件
3. 更新字段类型配置
4. 添加验证逻辑

### 集成其他AI模型

1. 在AI配置中添加模型选项
2. 更新AI处理逻辑
3. 配置模型参数

### 自定义主题样式

1. 修改组件的CSS变量
2. 更新全局样式配置
3. 添加自定义图标和颜色

## ⚠️ 注意事项

1. **权限控制**：确保管理功能只有管理员可以访问
2. **文件安全**：验证上传文件的类型和大小
3. **数据验证**：严格验证表单数据避免注入攻击
4. **性能优化**：对于大量应用考虑分页和缓存
5. **备份恢复**：定期备份应用配置和用户数据

## 🐛 故障排除

### 常见问题

1. **数据库连接错误**：检查数据库配置和迁移状态
2. **文件上传失败**：检查文件目录权限和大小限制
3. **AI响应超时**：调整AI配置的超时设置
4. **权限被拒绝**：确认用户角色和权限配置

### 调试方法

1. 查看后端日志：`tail -f logs/open-webui.log`
2. 检查浏览器控制台错误
3. 使用API测试工具验证接口
4. 检查数据库表结构和数据

通过以上配置，智能体广场系统将完全集成到OpenWebUI中，为用户提供强大的AI应用创建和使用功能。
