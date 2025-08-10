"""
Agent Applications Model for OpenWebUI
智能体应用数据模型，使用SQLite数据库存储
"""

import json
import time
import uuid
import logging
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, String, BigInteger, Boolean, Text, Integer
from open_webui.internal.db import Base, get_db, JSONField

log = logging.getLogger(__name__)


class AgentApp(Base):
    """智能体应用表"""

    __tablename__ = "agent_app"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # 应用名称（英文标识）
    display_name = Column(String, nullable=False)  # 显示名称（中文）
    description = Column(Text)  # 应用描述
    category = Column(
        String, default="general"
    )  # 分类：general, productivity, creative, analysis
    icon = Column(String)  # 应用图标（emoji或URL）
    app_type = Column(String, default="form")  # 应用类型：form, chat, tool
    status = Column(String, default="active")  # 状态：active, inactive, draft

    # 表单配置
    form_config = Column(JSONField, default={})  # 表单字段配置

    # AI配置
    ai_config = Column(JSONField, default={})  # AI模型和提示配置

    # 权限和限制
    access_control = Column(JSONField, default={})  # 访问权限配置
    usage_limit = Column(Integer, default=0)  # 使用次数限制(0=无限制)
    cost_per_use = Column(Integer, default=100)  # 每次使用消耗积分

    # 统计数据
    usage_count = Column(Integer, default=0)  # 总使用次数
    favorite_count = Column(Integer, default=0)  # 收藏次数
    rating = Column(Integer, default=0)  # 评分(0-5)

    # 元数据
    metadata = Column(JSONField, default={})  # 其他元数据

    # 审计字段
    created_by = Column(String, nullable=False)  # 创建者ID
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    updated_at = Column(BigInteger, default=lambda: int(time.time()))


class AgentAppSubmission(Base):
    """用户提交记录表"""

    __tablename__ = "agent_app_submission"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    app_id = Column(String, nullable=False)  # 应用ID
    user_id = Column(String, nullable=False)  # 用户ID
    session_id = Column(String)  # 对话会话ID

    # 提交数据
    form_data = Column(JSONField, default={})  # 表单数据
    files = Column(JSONField, default=[])  # 上传文件信息

    # 处理结果
    ai_response = Column(Text)  # AI响应内容
    status = Column(
        String, default="pending"
    )  # 状态：pending, processing, completed, failed
    cost_consumed = Column(Integer, default=0)  # 消耗的积分
    processing_time = Column(Integer)  # 处理时间(ms)
    error_message = Column(Text)  # 错误信息

    # 元数据
    metadata = Column(JSONField, default={})

    # 时间戳
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    completed_at = Column(BigInteger)


class AgentAppFavorite(Base):
    """用户收藏表"""

    __tablename__ = "agent_app_favorite"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    app_id = Column(String, nullable=False)  # 应用ID
    user_id = Column(String, nullable=False)  # 用户ID
    created_at = Column(BigInteger, default=lambda: int(time.time()))


class AgentAppStats(Base):
    """应用统计表"""

    __tablename__ = "agent_app_stats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    app_id = Column(String, nullable=False)  # 应用ID
    date = Column(String, nullable=False)  # 统计日期 YYYY-MM-DD

    # 使用统计
    daily_uses = Column(Integer, default=0)  # 日使用次数
    unique_users = Column(Integer, default=0)  # 独立用户数
    total_cost = Column(Integer, default=0)  # 总消耗积分
    avg_processing_time = Column(Integer, default=0)  # 平均处理时间
    success_rate = Column(Integer, default=100)  # 成功率(百分比)
    error_count = Column(Integer, default=0)  # 错误次数

    # 用户行为
    favorites_added = Column(Integer, default=0)  # 新增收藏数

    created_at = Column(BigInteger, default=lambda: int(time.time()))


# ========== 数据访问层 ==========


class AgentApps:
    """智能体应用数据访问类"""

    @staticmethod
    def create_app(
        name: str,
        display_name: str,
        description: str,
        form_config: dict,
        ai_config: dict,
        created_by: str,
        category: str = "general",
        icon: str = "🤖",
        cost_per_use: int = 100,
        access_control: dict = None,
    ) -> Optional[AgentApp]:
        """创建智能体应用"""
        try:
            with get_db() as db:
                app = AgentApp(
                    name=name,
                    display_name=display_name,
                    description=description,
                    category=category,
                    icon=icon,
                    form_config=form_config,
                    ai_config=ai_config,
                    cost_per_use=cost_per_use,
                    access_control=access_control or {},
                    created_by=created_by,
                )

                db.add(app)
                db.commit()
                db.refresh(app)

                log.info(f"Created agent app: {name}")
                return app

        except Exception as e:
            log.error(f"Error creating agent app: {e}")
            return None

    @staticmethod
    def get_app_by_id(app_id: str) -> Optional[AgentApp]:
        """根据ID获取应用"""
        try:
            with get_db() as db:
                return db.query(AgentApp).filter(AgentApp.id == app_id).first()
        except Exception as e:
            log.error(f"Error getting app by id: {e}")
            return None

    @staticmethod
    def get_apps(
        category: Optional[str] = None,
        search: Optional[str] = None,
        status: str = "active",
        limit: int = 20,
        offset: int = 0,
        user_id: Optional[str] = None,
    ) -> List[AgentApp]:
        """获取应用列表"""
        try:
            with get_db() as db:
                query = db.query(AgentApp).filter(AgentApp.status == status)

                if category:
                    query = query.filter(AgentApp.category == category)

                if search:
                    query = query.filter(
                        (AgentApp.display_name.contains(search))
                        | (AgentApp.description.contains(search))
                    )

                # 按使用次数和创建时间排序
                query = query.order_by(
                    AgentApp.usage_count.desc(), AgentApp.created_at.desc()
                )

                return query.offset(offset).limit(limit).all()

        except Exception as e:
            log.error(f"Error getting apps: {e}")
            return []

    @staticmethod
    def update_app(app_id: str, **kwargs) -> bool:
        """更新应用"""
        try:
            with get_db() as db:
                app = db.query(AgentApp).filter(AgentApp.id == app_id).first()
                if not app:
                    return False

                for key, value in kwargs.items():
                    if hasattr(app, key):
                        setattr(app, key, value)

                app.updated_at = int(time.time())
                db.commit()

                return True

        except Exception as e:
            log.error(f"Error updating app: {e}")
            return False

    @staticmethod
    def delete_app(app_id: str) -> bool:
        """删除应用"""
        try:
            with get_db() as db:
                app = db.query(AgentApp).filter(AgentApp.id == app_id).first()
                if not app:
                    return False

                db.delete(app)
                db.commit()

                log.info(f"Deleted agent app: {app_id}")
                return True

        except Exception as e:
            log.error(f"Error deleting app: {e}")
            return False

    @staticmethod
    def increment_usage_count(app_id: str):
        """增加使用次数"""
        try:
            with get_db() as db:
                app = db.query(AgentApp).filter(AgentApp.id == app_id).first()
                if app:
                    app.usage_count += 1
                    db.commit()

        except Exception as e:
            log.error(f"Error incrementing usage count: {e}")

    @staticmethod
    def get_categories() -> List[str]:
        """获取所有分类"""
        try:
            with get_db() as db:
                result = db.query(AgentApp.category).distinct().all()
                return [row[0] for row in result if row[0]]

        except Exception as e:
            log.error(f"Error getting categories: {e}")
            return []


class AgentAppSubmissions:
    """应用提交记录数据访问类"""

    @staticmethod
    def create_submission(
        app_id: str,
        user_id: str,
        form_data: dict,
        files: list = None,
        session_id: str = None,
    ) -> Optional[AgentAppSubmission]:
        """创建提交记录"""
        try:
            with get_db() as db:
                submission = AgentAppSubmission(
                    app_id=app_id,
                    user_id=user_id,
                    form_data=form_data,
                    files=files or [],
                    session_id=session_id,
                )

                db.add(submission)
                db.commit()
                db.refresh(submission)

                return submission

        except Exception as e:
            log.error(f"Error creating submission: {e}")
            return None

    @staticmethod
    def get_submission_by_id(submission_id: str) -> Optional[AgentAppSubmission]:
        """根据ID获取提交记录"""
        try:
            with get_db() as db:
                return (
                    db.query(AgentAppSubmission)
                    .filter(AgentAppSubmission.id == submission_id)
                    .first()
                )
        except Exception as e:
            log.error(f"Error getting submission: {e}")
            return None

    @staticmethod
    def update_submission_response(
        submission_id: str,
        ai_response: str,
        status: str = "completed",
        cost_consumed: int = 0,
        processing_time: int = None,
    ) -> bool:
        """更新提交记录的AI响应"""
        try:
            with get_db() as db:
                submission = (
                    db.query(AgentAppSubmission)
                    .filter(AgentAppSubmission.id == submission_id)
                    .first()
                )

                if submission:
                    submission.ai_response = ai_response
                    submission.status = status
                    submission.cost_consumed = cost_consumed
                    submission.completed_at = int(time.time())

                    if processing_time:
                        submission.processing_time = processing_time

                    db.commit()
                    return True

                return False

        except Exception as e:
            log.error(f"Error updating submission response: {e}")
            return False

    @staticmethod
    def get_user_submissions(
        user_id: str, app_id: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[AgentAppSubmission]:
        """获取用户提交历史"""
        try:
            with get_db() as db:
                query = db.query(AgentAppSubmission).filter(
                    AgentAppSubmission.user_id == user_id
                )

                if app_id:
                    query = query.filter(AgentAppSubmission.app_id == app_id)

                return (
                    query.order_by(AgentAppSubmission.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )

        except Exception as e:
            log.error(f"Error getting user submissions: {e}")
            return []


class AgentAppFavorites:
    """应用收藏数据访问类"""

    @staticmethod
    def add_favorite(app_id: str, user_id: str) -> bool:
        """添加收藏"""
        try:
            with get_db() as db:
                # 检查是否已收藏
                existing = (
                    db.query(AgentAppFavorite)
                    .filter(
                        AgentAppFavorite.app_id == app_id,
                        AgentAppFavorite.user_id == user_id,
                    )
                    .first()
                )

                if existing:
                    return True

                # 添加收藏记录
                favorite = AgentAppFavorite(app_id=app_id, user_id=user_id)

                db.add(favorite)

                # 更新应用收藏数
                app = db.query(AgentApp).filter(AgentApp.id == app_id).first()
                if app:
                    app.favorite_count += 1

                db.commit()
                return True

        except Exception as e:
            log.error(f"Error adding favorite: {e}")
            return False

    @staticmethod
    def remove_favorite(app_id: str, user_id: str) -> bool:
        """取消收藏"""
        try:
            with get_db() as db:
                favorite = (
                    db.query(AgentAppFavorite)
                    .filter(
                        AgentAppFavorite.app_id == app_id,
                        AgentAppFavorite.user_id == user_id,
                    )
                    .first()
                )

                if favorite:
                    db.delete(favorite)

                    # 更新应用收藏数
                    app = db.query(AgentApp).filter(AgentApp.id == app_id).first()
                    if app and app.favorite_count > 0:
                        app.favorite_count -= 1

                    db.commit()

                return True

        except Exception as e:
            log.error(f"Error removing favorite: {e}")
            return False

    @staticmethod
    def is_favorited(app_id: str, user_id: str) -> bool:
        """检查是否已收藏"""
        try:
            with get_db() as db:
                favorite = (
                    db.query(AgentAppFavorite)
                    .filter(
                        AgentAppFavorite.app_id == app_id,
                        AgentAppFavorite.user_id == user_id,
                    )
                    .first()
                )

                return favorite is not None

        except Exception as e:
            log.error(f"Error checking favorite: {e}")
            return False

    @staticmethod
    def get_user_favorites(user_id: str) -> List[str]:
        """获取用户收藏的应用ID列表"""
        try:
            with get_db() as db:
                favorites = (
                    db.query(AgentAppFavorite.app_id)
                    .filter(AgentAppFavorite.user_id == user_id)
                    .all()
                )

                return [fav[0] for fav in favorites]

        except Exception as e:
            log.error(f"Error getting user favorites: {e}")
            return []


# 导出主要类
__all__ = [
    "AgentApp",
    "AgentAppSubmission",
    "AgentAppFavorite",
    "AgentAppStats",
    "AgentApps",
    "AgentAppSubmissions",
    "AgentAppFavorites",
]
