"""
Enhanced Knowledge Base System for OpenWebUI
增强的知识库系统，包含细粒度权限控制、版本管理和智能功能
"""

import json
import time
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy import (
    Column,
    String,
    BigInteger,
    Boolean,
    Text,
    Integer,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from open_webui.internal.db import Base, get_db
from open_webui.models.users import Users
from open_webui.models.groups import Groups

log = logging.getLogger(__name__)


# ========== 数据模型 ==========


class PermissionType(Enum):
    """权限类型枚举"""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SHARE = "share"
    ADMIN = "admin"


class AuditAction(Enum):
    """审计动作枚举"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SHARE = "share"
    IMPORT = "import"
    EXPORT = "export"
    REINDEX = "reindex"


@dataclass
class DocumentPermission:
    """文档权限数据类"""

    document_id: str
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    permission_type: PermissionType = PermissionType.READ
    expires_at: Optional[int] = None
    created_at: int = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = int(time.time())

    def is_expired(self) -> bool:
        """检查权限是否过期"""
        if self.expires_at is None:
            return False
        return int(time.time()) > self.expires_at


# ========== 数据库模型 ==========


class DocumentPermissions(Base):
    """文档权限表"""

    __tablename__ = "document_permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False, index=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=True)
    group_id = Column(String, ForeignKey("group.id"), nullable=True)
    permission_type = Column(String, nullable=False)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    expires_at = Column(BigInteger, nullable=True)
    created_by = Column(String, ForeignKey("user.id"))

    # 关系
    user = relationship("User", foreign_keys=[user_id])
    group = relationship("Group", foreign_keys=[group_id])
    creator = relationship("User", foreign_keys=[created_by])


class KnowledgeAuditLog(Base):
    """知识库审计日志表"""

    __tablename__ = "knowledge_audit_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    action = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)  # 'knowledge', 'document', 'file'
    details = Column(JSON, default={})
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(BigInteger, default=lambda: int(time.time()))

    # 关系
    user = relationship("User")


class KnowledgeVersion(Base):
    """知识库版本控制表"""

    __tablename__ = "knowledge_version"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_id = Column(String, ForeignKey("knowledge.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content_hash = Column(String, nullable=False)  # 内容哈希值
    file_ids = Column(JSON, default=[])
    metadata = Column(JSON, default={})
    created_by = Column(String, ForeignKey("user.id"))
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    commit_message = Column(Text)
    parent_version_id = Column(
        String, ForeignKey("knowledge_version.id"), nullable=True
    )

    # 关系
    knowledge = relationship("Knowledge")
    creator = relationship("User")
    parent_version = relationship("KnowledgeVersion", remote_side=[id])


class KnowledgeStatistics(Base):
    """知识库统计表"""

    __tablename__ = "knowledge_statistics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_id = Column(
        String, ForeignKey("knowledge.id"), nullable=False, unique=True
    )
    total_documents = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_queries = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    avg_query_time = Column(Integer, default=0)  # 毫秒
    last_accessed = Column(BigInteger)
    last_updated = Column(BigInteger)
    popular_queries = Column(JSON, default=[])  # 热门查询列表
    usage_by_day = Column(JSON, default={})  # 每日使用统计

    # 关系
    knowledge = relationship("Knowledge")


# ========== 权限管理服务 ==========


class EnhancedPermissionManager:
    """增强的权限管理器"""

    @staticmethod
    def check_knowledge_access(
        user_id: str, knowledge_id: str, action: PermissionType, knowledge_obj=None
    ) -> bool:
        """
        检查知识库访问权限

        Args:
            user_id: 用户ID
            knowledge_id: 知识库ID
            action: 权限动作
            knowledge_obj: 知识库对象（可选，避免重复查询）

        Returns:
            bool: 是否有权限
        """
        try:
            user = Users.get_user_by_id(user_id)
            if not user:
                return False

            # 管理员拥有所有权限
            if user.role == "admin":
                return True

            # 获取知识库对象
            if not knowledge_obj:
                from open_webui.models.knowledge import Knowledges

                knowledge_obj = Knowledges.get_knowledge_by_id(knowledge_id)

            if not knowledge_obj:
                return False

            # 所有者拥有所有权限
            if knowledge_obj.user_id == user_id:
                return True

            # 检查知识库级别的访问控制
            if (
                hasattr(knowledge_obj, "access_control")
                and knowledge_obj.access_control
            ):
                from open_webui.utils.access_control import has_access

                action_str = (
                    action.value if isinstance(action, PermissionType) else action
                )
                if has_access(user_id, action_str, knowledge_obj.access_control):
                    return True

            # 检查文档级别权限
            if action in [PermissionType.READ, PermissionType.WRITE]:
                return EnhancedPermissionManager._check_document_permissions(
                    user_id, knowledge_id, action
                )

            return False

        except Exception as e:
            log.error(f"Error checking knowledge access: {e}")
            return False

    @staticmethod
    def _check_document_permissions(
        user_id: str, knowledge_id: str, action: PermissionType
    ) -> bool:
        """检查文档级别权限"""
        with get_db() as db:
            # 获取用户的组
            user = Users.get_user_by_id(user_id)
            user_groups = user.groups if user else []

            # 查询文档权限
            query = db.query(DocumentPermissions).filter(
                DocumentPermissions.document_id == knowledge_id,
                DocumentPermissions.permission_type == action.value,
            )

            # 检查用户权限或组权限
            permissions = query.filter(
                (DocumentPermissions.user_id == user_id)
                | (
                    DocumentPermissions.group_id.in_(user_groups)
                    if user_groups
                    else False
                )
            ).all()

            for perm in permissions:
                # 检查是否过期
                if perm.expires_at and perm.expires_at < int(time.time()):
                    continue
                return True

            return False

    @staticmethod
    def grant_permission(
        document_id: str,
        grantee_id: str,
        permission_type: PermissionType,
        is_group: bool = False,
        expires_in_days: Optional[int] = None,
        granted_by: str = None,
    ) -> bool:
        """
        授予权限

        Args:
            document_id: 文档ID
            grantee_id: 被授权者ID（用户或组）
            permission_type: 权限类型
            is_group: 是否为组权限
            expires_in_days: 过期天数
            granted_by: 授权者ID

        Returns:
            bool: 是否成功
        """
        try:
            with get_db() as db:
                # 检查是否已存在相同权限
                existing = db.query(DocumentPermissions).filter(
                    DocumentPermissions.document_id == document_id,
                    DocumentPermissions.permission_type == permission_type.value,
                )

                if is_group:
                    existing = existing.filter(
                        DocumentPermissions.group_id == grantee_id
                    )
                else:
                    existing = existing.filter(
                        DocumentPermissions.user_id == grantee_id
                    )

                if existing.first():
                    log.info(
                        f"Permission already exists for {grantee_id} on {document_id}"
                    )
                    return True

                # 创建新权限
                expires_at = None
                if expires_in_days:
                    expires_at = int(time.time()) + (expires_in_days * 86400)

                permission = DocumentPermissions(
                    document_id=document_id,
                    user_id=grantee_id if not is_group else None,
                    group_id=grantee_id if is_group else None,
                    permission_type=permission_type.value,
                    expires_at=expires_at,
                    created_by=granted_by,
                )

                db.add(permission)
                db.commit()

                log.info(
                    f"Granted {permission_type.value} permission to {grantee_id} on {document_id}"
                )
                return True

        except Exception as e:
            log.error(f"Error granting permission: {e}")
            return False

    @staticmethod
    def revoke_permission(
        document_id: str,
        grantee_id: str,
        permission_type: Optional[PermissionType] = None,
        is_group: bool = False,
    ) -> bool:
        """撤销权限"""
        try:
            with get_db() as db:
                query = db.query(DocumentPermissions).filter(
                    DocumentPermissions.document_id == document_id
                )

                if is_group:
                    query = query.filter(DocumentPermissions.group_id == grantee_id)
                else:
                    query = query.filter(DocumentPermissions.user_id == grantee_id)

                if permission_type:
                    query = query.filter(
                        DocumentPermissions.permission_type == permission_type.value
                    )

                deleted = query.delete()
                db.commit()

                log.info(
                    f"Revoked {deleted} permissions for {grantee_id} on {document_id}"
                )
                return deleted > 0

        except Exception as e:
            log.error(f"Error revoking permission: {e}")
            return False


# ========== 审计日志服务 ==========


class AuditLogger:
    """审计日志记录器"""

    @staticmethod
    def log(
        user_id: str,
        action: AuditAction,
        resource_id: str,
        resource_type: str,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        记录审计日志

        Args:
            user_id: 用户ID
            action: 动作类型
            resource_id: 资源ID
            resource_type: 资源类型
            details: 详细信息
            ip_address: IP地址
            user_agent: 用户代理
        """
        try:
            with get_db() as db:
                log_entry = KnowledgeAuditLog(
                    user_id=user_id,
                    action=action.value,
                    resource_id=resource_id,
                    resource_type=resource_type,
                    details=details or {},
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

                db.add(log_entry)
                db.commit()

        except Exception as e:
            log.error(f"Error logging audit: {e}")

    @staticmethod
    def get_logs(
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """查询审计日志"""
        try:
            with get_db() as db:
                query = db.query(KnowledgeAuditLog)

                if resource_id:
                    query = query.filter(KnowledgeAuditLog.resource_id == resource_id)
                if user_id:
                    query = query.filter(KnowledgeAuditLog.user_id == user_id)
                if action:
                    query = query.filter(KnowledgeAuditLog.action == action.value)
                if start_time:
                    query = query.filter(KnowledgeAuditLog.timestamp >= start_time)
                if end_time:
                    query = query.filter(KnowledgeAuditLog.timestamp <= end_time)

                logs = (
                    query.order_by(KnowledgeAuditLog.timestamp.desc())
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "id": log.id,
                        "user_id": log.user_id,
                        "action": log.action,
                        "resource_id": log.resource_id,
                        "resource_type": log.resource_type,
                        "details": log.details,
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent,
                        "timestamp": log.timestamp,
                    }
                    for log in logs
                ]

        except Exception as e:
            log.error(f"Error getting audit logs: {e}")
            return []


# ========== 版本控制服务 ==========


class VersionControl:
    """版本控制管理器"""

    @staticmethod
    def create_version(
        knowledge_id: str,
        file_ids: List[str],
        created_by: str,
        commit_message: str = "",
        parent_version_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        创建新版本

        Returns:
            str: 版本ID
        """
        try:
            with get_db() as db:
                # 计算内容哈希
                content_hash = hashlib.sha256(
                    json.dumps(sorted(file_ids)).encode()
                ).hexdigest()

                # 获取版本号
                last_version = (
                    db.query(KnowledgeVersion)
                    .filter(KnowledgeVersion.knowledge_id == knowledge_id)
                    .order_by(KnowledgeVersion.version_number.desc())
                    .first()
                )

                version_number = 1
                if last_version:
                    version_number = last_version.version_number + 1

                # 创建版本记录
                version = KnowledgeVersion(
                    knowledge_id=knowledge_id,
                    version_number=version_number,
                    content_hash=content_hash,
                    file_ids=file_ids,
                    created_by=created_by,
                    commit_message=commit_message or f"Version {version_number}",
                    parent_version_id=parent_version_id
                    or (last_version.id if last_version else None),
                )

                db.add(version)
                db.commit()

                log.info(
                    f"Created version {version_number} for knowledge {knowledge_id}"
                )
                return version.id

        except Exception as e:
            log.error(f"Error creating version: {e}")
            return None

    @staticmethod
    def get_version_history(knowledge_id: str, limit: int = 20) -> List[Dict]:
        """获取版本历史"""
        try:
            with get_db() as db:
                versions = (
                    db.query(KnowledgeVersion)
                    .filter(KnowledgeVersion.knowledge_id == knowledge_id)
                    .order_by(KnowledgeVersion.version_number.desc())
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "id": v.id,
                        "version_number": v.version_number,
                        "content_hash": v.content_hash,
                        "file_ids": v.file_ids,
                        "created_by": v.created_by,
                        "created_at": v.created_at,
                        "commit_message": v.commit_message,
                        "parent_version_id": v.parent_version_id,
                    }
                    for v in versions
                ]

        except Exception as e:
            log.error(f"Error getting version history: {e}")
            return []

    @staticmethod
    def restore_version(knowledge_id: str, version_id: str, restored_by: str) -> bool:
        """恢复到指定版本"""
        try:
            with get_db() as db:
                version = (
                    db.query(KnowledgeVersion)
                    .filter(
                        KnowledgeVersion.id == version_id,
                        KnowledgeVersion.knowledge_id == knowledge_id,
                    )
                    .first()
                )

                if not version:
                    log.error(f"Version {version_id} not found")
                    return False

                # 创建恢复版本
                restore_version_id = VersionControl.create_version(
                    knowledge_id=knowledge_id,
                    file_ids=version.file_ids,
                    created_by=restored_by,
                    commit_message=f"Restored to version {version.version_number}",
                    parent_version_id=version_id,
                )

                if restore_version_id:
                    # 更新知识库的文件列表
                    from open_webui.models.knowledge import Knowledges

                    knowledge = Knowledges.get_knowledge_by_id(knowledge_id)
                    if knowledge and knowledge.data:
                        knowledge.data["file_ids"] = version.file_ids
                        Knowledges.update_knowledge_by_id(knowledge_id, knowledge)

                    log.info(
                        f"Restored knowledge {knowledge_id} to version {version.version_number}"
                    )
                    return True

                return False

        except Exception as e:
            log.error(f"Error restoring version: {e}")
            return False


# ========== 统计分析服务 ==========


class StatisticsManager:
    """统计管理器"""

    @staticmethod
    def update_statistics(
        knowledge_id: str, event_type: str, details: Optional[Dict] = None
    ):
        """
        更新统计信息

        Args:
            knowledge_id: 知识库ID
            event_type: 事件类型 ('query', 'view', 'update', 'document_add', 'document_remove')
            details: 详细信息
        """
        try:
            with get_db() as db:
                stats = (
                    db.query(KnowledgeStatistics)
                    .filter(KnowledgeStatistics.knowledge_id == knowledge_id)
                    .first()
                )

                if not stats:
                    stats = KnowledgeStatistics(knowledge_id=knowledge_id)
                    db.add(stats)

                # 更新统计数据
                current_time = int(time.time())
                today = datetime.now().strftime("%Y-%m-%d")

                if event_type == "query":
                    stats.total_queries += 1
                    if details and "query_time" in details:
                        # 更新平均查询时间
                        if stats.avg_query_time == 0:
                            stats.avg_query_time = details["query_time"]
                        else:
                            stats.avg_query_time = int(
                                (
                                    stats.avg_query_time * (stats.total_queries - 1)
                                    + details["query_time"]
                                )
                                / stats.total_queries
                            )

                    # 记录热门查询
                    if details and "query" in details:
                        popular_queries = stats.popular_queries or []
                        query_text = details["query"]

                        # 更新或添加查询
                        found = False
                        for q in popular_queries:
                            if q["text"] == query_text:
                                q["count"] += 1
                                found = True
                                break

                        if not found:
                            popular_queries.append({"text": query_text, "count": 1})

                        # 保留前20个热门查询
                        popular_queries.sort(key=lambda x: x["count"], reverse=True)
                        stats.popular_queries = popular_queries[:20]

                elif event_type == "view":
                    stats.total_views += 1

                elif event_type == "document_add":
                    stats.total_documents += details.get("count", 1)
                    stats.total_tokens += details.get("tokens", 0)

                elif event_type == "document_remove":
                    stats.total_documents -= details.get("count", 1)
                    stats.total_tokens -= details.get("tokens", 0)

                # 更新每日使用统计
                usage_by_day = stats.usage_by_day or {}
                if today not in usage_by_day:
                    usage_by_day[today] = {"queries": 0, "views": 0, "updates": 0}

                if event_type == "query":
                    usage_by_day[today]["queries"] += 1
                elif event_type == "view":
                    usage_by_day[today]["views"] += 1
                elif event_type in ["update", "document_add", "document_remove"]:
                    usage_by_day[today]["updates"] += 1

                # 只保留最近30天的数据
                cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                usage_by_day = {
                    k: v for k, v in usage_by_day.items() if k >= cutoff_date
                }
                stats.usage_by_day = usage_by_day

                # 更新时间戳
                stats.last_accessed = current_time
                if event_type in ["update", "document_add", "document_remove"]:
                    stats.last_updated = current_time

                db.commit()

        except Exception as e:
            log.error(f"Error updating statistics: {e}")

    @staticmethod
    def get_statistics(knowledge_id: str) -> Optional[Dict]:
        """获取统计信息"""
        try:
            with get_db() as db:
                stats = (
                    db.query(KnowledgeStatistics)
                    .filter(KnowledgeStatistics.knowledge_id == knowledge_id)
                    .first()
                )

                if stats:
                    return {
                        "total_documents": stats.total_documents,
                        "total_tokens": stats.total_tokens,
                        "total_queries": stats.total_queries,
                        "total_views": stats.total_views,
                        "avg_query_time": stats.avg_query_time,
                        "last_accessed": stats.last_accessed,
                        "last_updated": stats.last_updated,
                        "popular_queries": stats.popular_queries,
                        "usage_by_day": stats.usage_by_day,
                    }

                return None

        except Exception as e:
            log.error(f"Error getting statistics: {e}")
            return None

    @staticmethod
    def get_analytics_report(
        knowledge_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """
        生成分析报告

        Returns:
            Dict: 分析报告数据
        """
        stats = StatisticsManager.get_statistics(knowledge_id)
        if not stats:
            return {}

        report = {
            "summary": {
                "total_documents": stats["total_documents"],
                "total_tokens": stats["total_tokens"],
                "total_queries": stats["total_queries"],
                "total_views": stats["total_views"],
                "avg_query_time_ms": stats["avg_query_time"],
            },
            "trends": {},
            "insights": [],
        }

        # 分析趋势
        if stats["usage_by_day"]:
            usage_data = stats["usage_by_day"]

            # 过滤日期范围
            if start_date:
                usage_data = {k: v for k, v in usage_data.items() if k >= start_date}
            if end_date:
                usage_data = {k: v for k, v in usage_data.items() if k <= end_date}

            # 计算趋势
            total_queries = sum(v["queries"] for v in usage_data.values())
            total_views = sum(v["views"] for v in usage_data.values())
            total_updates = sum(v["updates"] for v in usage_data.values())

            report["trends"] = {
                "daily_usage": usage_data,
                "total_queries": total_queries,
                "total_views": total_views,
                "total_updates": total_updates,
                "avg_daily_queries": (
                    total_queries / len(usage_data) if usage_data else 0
                ),
                "avg_daily_views": total_views / len(usage_data) if usage_data else 0,
            }

        # 生成洞察
        if stats["popular_queries"]:
            top_queries = stats["popular_queries"][:5]
            report["insights"].append(
                {
                    "type": "popular_queries",
                    "title": "Top 5 Popular Queries",
                    "data": top_queries,
                }
            )

        if stats["avg_query_time"] > 1000:
            report["insights"].append(
                {
                    "type": "performance",
                    "title": "Performance Alert",
                    "message": f'Average query time is {stats["avg_query_time"]}ms, consider optimization',
                }
            )

        return report


# 导出主要类和函数
__all__ = [
    "PermissionType",
    "AuditAction",
    "DocumentPermission",
    "EnhancedPermissionManager",
    "AuditLogger",
    "VersionControl",
    "StatisticsManager",
    "DocumentPermissions",
    "KnowledgeAuditLog",
    "KnowledgeVersion",
    "KnowledgeStatistics",
]
