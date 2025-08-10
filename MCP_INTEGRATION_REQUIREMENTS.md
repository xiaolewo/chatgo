# OpenWebUI MCP（Model Context Protocol）集成需求文档

## 1. 项目背景

OpenWebUI 是一个基于 FastAPI 和 SvelteKit 的AI对话界面系统。本需求文档描述了如何将 Anthropic 的 Model Context Protocol (MCP) 集成到 OpenWebUI 中，使用户能够动态管理和使用各种MCP服务。

## 2. 核心需求

### 2.1 后台MCP服务管理

- **动态添加MCP服务**：管理员可以在后台随时添加新的MCP服务器
- **服务配置管理**：支持配置MCP服务器的连接参数、认证信息等
- **服务状态监控**：实时监控各MCP服务的连接状态和可用性
- **服务权限控制**：设置哪些用户或用户组可以访问特定的MCP服务

### 2.2 用户端功能

- **MCP服务展示**：在用户界面显示所有可用的MCP服务列表
- **服务选择器**：用户可以选择一个或多个MCP服务用于当前对话
- **工具调用集成**：将MCP服务的工具无缝集成到对话流程中
- **实时工具调用**：在对话中直接调用MCP服务提供的工具和资源

### 2.3 对话集成

- **上下文感知**：MCP工具调用能够理解并使用当前对话上下文
- **结果展示**：优雅地展示MCP工具调用的结果
- **错误处理**：友好地处理MCP服务不可用或调用失败的情况

## 3. 技术架构设计

### 3.1 后端架构

#### 3.1.1 数据模型

```python
# 新增数据表：mcp_services
class MCPService(Base):
    __tablename__ = "mcp_service"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)  # MCP服务器地址
    type = Column(String)  # stdio, http, websocket
    config = Column(JSON)  # 连接配置（如命令行参数、环境变量等）
    auth = Column(JSON)  # 认证信息（加密存储）
    status = Column(String, default="inactive")  # active, inactive, error
    capabilities = Column(JSON)  # 缓存的服务能力信息
    access_control = Column(JSON)  # 访问控制规则
    created_by = Column(String)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)

# 新增数据表：mcp_service_usage
class MCPServiceUsage(Base):
    __tablename__ = "mcp_service_usage"

    id = Column(String, primary_key=True)
    service_id = Column(String, ForeignKey("mcp_service.id"))
    user_id = Column(String, ForeignKey("user.id"))
    chat_id = Column(String, ForeignKey("chat.id"))
    tool_name = Column(String)
    request_data = Column(JSON)
    response_data = Column(JSON)
    status = Column(String)  # success, error
    created_at = Column(BigInteger)
```

#### 3.1.2 API 路由设计

```python
# /api/mcp/services - MCP服务管理
GET    /api/mcp/services          # 获取所有MCP服务列表
POST   /api/mcp/services          # 添加新的MCP服务
GET    /api/mcp/services/{id}     # 获取单个MCP服务详情
PUT    /api/mcp/services/{id}     # 更新MCP服务配置
DELETE /api/mcp/services/{id}     # 删除MCP服务
POST   /api/mcp/services/{id}/test # 测试MCP服务连接

# /api/mcp/tools - MCP工具调用
GET    /api/mcp/services/{id}/tools    # 获取MCP服务的可用工具列表
POST   /api/mcp/services/{id}/tools/{tool_name} # 调用特定工具

# /api/mcp/resources - MCP资源管理
GET    /api/mcp/services/{id}/resources # 获取MCP服务的资源列表
GET    /api/mcp/services/{id}/resources/{uri} # 获取特定资源内容
```

#### 3.1.3 MCP客户端管理器

```python
class MCPClientManager:
    """管理所有MCP服务的连接和调用"""

    def __init__(self):
        self.clients = {}  # service_id -> MCPClient

    async def connect_service(self, service_id: str, config: dict):
        """连接到MCP服务"""
        pass

    async def disconnect_service(self, service_id: str):
        """断开MCP服务连接"""
        pass

    async def call_tool(self, service_id: str, tool_name: str, params: dict):
        """调用MCP服务的工具"""
        pass

    async def get_resources(self, service_id: str):
        """获取MCP服务的资源列表"""
        pass
```

### 3.2 前端架构

#### 3.2.1 组件设计

1. **MCP服务管理页面** (`/admin/mcp`)

   - MCP服务列表组件
   - MCP服务添加/编辑弹窗
   - MCP服务测试面板

2. **用户端MCP选择器**

   - MCP服务选择下拉菜单
   - 已选择MCP服务标签展示
   - MCP工具快速访问面板

3. **对话集成组件**
   - MCP工具调用指示器
   - MCP结果展示卡片
   - MCP错误提示组件

#### 3.2.2 状态管理

```javascript
// stores/mcp.js
export const mcpStore = writable({
	services: [], // 所有可用的MCP服务
	activeServices: [], // 当前对话激活的MCP服务
	toolResults: {}, // 工具调用结果缓存
	connectionStatus: {} // 各服务连接状态
});
```

## 4. 实现步骤

### 第一阶段：基础框架搭建

1. 创建MCP服务数据模型和数据库迁移
2. 实现基础的MCP服务CRUD API
3. 开发MCP Python SDK客户端封装
4. 创建MCP服务管理后台界面

### 第二阶段：MCP协议支持

1. 实现stdio类型MCP服务连接
2. 实现HTTP类型MCP服务连接
3. 实现WebSocket类型MCP服务连接（可选）
4. 开发MCP工具调用API

### 第三阶段：用户端集成

1. 开发MCP服务选择器组件
2. 集成MCP工具到对话流程
3. 实现MCP结果展示组件
4. 添加MCP使用记录和统计

### 第四阶段：高级功能

1. 实现MCP服务健康检查和自动重连
2. 添加MCP工具调用的权限细粒度控制
3. 开发MCP工具的参数验证和安全检查
4. 实现MCP调用的并发控制和速率限制

## 5. 安全考虑

### 5.1 认证和授权

- MCP服务认证信息加密存储
- 基于角色的MCP服务访问控制
- MCP工具调用的审计日志

### 5.2 数据安全

- MCP调用参数的输入验证
- 敏感数据的脱敏处理
- MCP响应数据的安全过滤

### 5.3 网络安全

- 支持HTTPS/WSS安全连接
- MCP服务的IP白名单配置
- 连接超时和重试机制

## 6. 性能优化

### 6.1 连接池管理

- 复用MCP服务连接
- 连接池大小动态调整
- 空闲连接自动回收

### 6.2 缓存策略

- MCP服务能力信息缓存
- 工具调用结果缓存（可配置）
- 资源内容缓存

### 6.3 异步处理

- 异步MCP工具调用
- 批量工具调用支持
- 长时间运行任务的后台处理

## 7. 用户体验设计

### 7.1 MCP服务展示

- 清晰的服务分类和标签
- 服务能力的可视化展示
- 服务状态的实时指示

### 7.2 交互优化

- 拖拽式MCP服务选择
- 智能的工具推荐
- 快捷键支持

### 7.3 错误处理

- 友好的错误提示
- 自动故障恢复建议
- 详细的调试信息（开发模式）

## 8. 测试计划

### 8.1 单元测试

- MCP客户端连接测试
- 工具调用参数验证测试
- 权限控制逻辑测试

### 8.2 集成测试

- 端到端的MCP服务调用测试
- 多MCP服务并发调用测试
- 故障恢复测试

### 8.3 性能测试

- MCP服务连接压力测试
- 工具调用响应时间测试
- 内存泄漏检测

## 9. 文档和培训

### 9.1 开发文档

- MCP集成API文档
- MCP服务开发指南
- 故障排查手册

### 9.2 用户文档

- MCP服务使用指南
- 常见问题解答
- 最佳实践案例

## 10. 里程碑和时间线

| 阶段       | 任务               | 预计时间 |
| ---------- | ------------------ | -------- |
| 第一阶段   | 基础框架搭建       | 1-2周    |
| 第二阶段   | MCP协议支持        | 2-3周    |
| 第三阶段   | 用户端集成         | 2-3周    |
| 第四阶段   | 高级功能           | 2-3周    |
| 测试和优化 | 全面测试和性能优化 | 1-2周    |
| 文档完善   | 文档编写和用户培训 | 1周      |

## 11. 风险评估

### 11.1 技术风险

- MCP协议的兼容性问题
- 第三方MCP服务的稳定性
- 性能瓶颈和扩展性问题

### 11.2 安全风险

- MCP服务的恶意调用
- 数据泄露风险
- 服务拒绝攻击

### 11.3 缓解措施

- 建立MCP服务白名单机制
- 实施严格的速率限制
- 定期安全审计和更新

## 12. 成功指标

- MCP服务连接成功率 > 99%
- 工具调用平均响应时间 < 2秒
- 用户满意度评分 > 4.5/5
- 系统稳定性：99.9% uptime
- 支持同时连接的MCP服务数 > 10个

## 13. 未来扩展

- 支持自定义MCP服务开发框架
- MCP服务市场和社区共享
- AI驱动的MCP工具推荐
- 跨平台MCP服务编排
- MCP服务的可视化编程界面

---

## 附录：MCP协议概述

MCP（Model Context Protocol）是一个开放协议，用于实现AI助手与外部系统的标准化通信。主要特点：

- **工具（Tools）**：可调用的函数或API
- **资源（Resources）**：可访问的数据或文件
- **提示（Prompts）**：预定义的提示模板
- **采样（Sampling）**：请求LLM完成任务

支持的传输方式：

- **stdio**：通过标准输入/输出通信
- **HTTP**：RESTful API
- **WebSocket**：实时双向通信

更多信息请参考：[MCP官方文档](https://modelcontextprotocol.io)
