import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from open_webui.internal.db import Base, JSONField, get_db
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, JSON, Boolean, Integer, Float

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# MidJourney Tasks DB Schema
####################


class MidJourneyTask(Base):
    __tablename__ = "midjourney_task"

    # 任务标识
    task_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    mj_task_id = Column(String, nullable=True)  # MidJourney API返回的任务ID
    parent_task_id = Column(String, nullable=True)  # 父任务ID（用于动作任务）

    # 任务内容
    prompt = Column(Text, nullable=False)
    final_prompt = Column(Text, nullable=True)
    mode = Column(String, default="fast")  # fast, relax, turbo
    aspect_ratio = Column(String, default="1:1")
    negative_prompt = Column(Text, nullable=True)

    # 任务状态
    status = Column(
        String, default="submitted"
    )  # submitted, processing, completed, failed, cancelled
    progress = Column(Integer, default=0)
    message = Column(Text, default="")
    error_message = Column(Text, nullable=True)

    # 结果数据
    image_url = Column(Text, nullable=True)
    seed = Column(BigInteger, nullable=True)
    credits_used = Column(Integer, default=0)

    # JSON字段存储复杂数据
    reference_images = Column(JSONField, nullable=True)  # 参考图片数据
    advanced_params = Column(JSONField, nullable=True)  # 高级参数
    actions = Column(JSONField, nullable=True)  # 可用动作按钮

    # 动作任务相关
    action_type = Column(String, nullable=True)  # upscale, variation, reroll
    button_index = Column(Integer, nullable=True)
    custom_id = Column(String, nullable=True)

    # 时间戳
    created_at = Column(BigInteger, nullable=False)
    completed_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=False)


class MidJourneyTaskModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    user_id: str
    mj_task_id: Optional[str] = None
    parent_task_id: Optional[str] = None

    prompt: str
    final_prompt: Optional[str] = None
    mode: str = "fast"
    aspect_ratio: str = "1:1"
    negative_prompt: Optional[str] = None

    status: str = "submitted"
    progress: int = 0
    message: str = ""
    error_message: Optional[str] = None

    image_url: Optional[str] = None
    seed: Optional[int] = None
    credits_used: int = 0

    reference_images: Optional[List[Dict[str, Any]]] = None
    advanced_params: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None

    action_type: Optional[str] = None
    button_index: Optional[int] = None
    custom_id: Optional[str] = None

    created_at: int
    completed_at: Optional[int] = None
    updated_at: int


####################
# Forms
####################


class MidJourneyTaskForm(BaseModel):
    task_id: str
    user_id: str
    mj_task_id: Optional[str] = None
    parent_task_id: Optional[str] = None

    prompt: str
    final_prompt: Optional[str] = None
    mode: str = "fast"
    aspect_ratio: str = "1:1"
    negative_prompt: Optional[str] = None

    status: str = "submitted"
    progress: int = 0
    message: str = ""
    error_message: Optional[str] = None

    image_url: Optional[str] = None
    seed: Optional[int] = None
    credits_used: int = 0

    reference_images: Optional[List[Dict[str, Any]]] = None
    advanced_params: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None

    action_type: Optional[str] = None
    button_index: Optional[int] = None
    custom_id: Optional[str] = None


class MidJourneyTaskResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[int] = None
    image_url: Optional[str] = None
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    actions: Optional[List[Dict[str, Any]]] = None
    seed: Optional[int] = None
    final_prompt: Optional[str] = None


class MidJourneyTasksTable:
    def __init__(self):
        with get_db() as db:
            # 创建表（如果不存在）
            try:
                Base.metadata.create_all(bind=db.bind)
            except Exception as e:
                log.error(f"Failed to create MidJourney tasks table: {e}")

    def insert_new_task(
        self, form_data: MidJourneyTaskForm
    ) -> Optional[MidJourneyTaskModel]:
        """插入新的MidJourney任务"""
        current_time = int(time.time())
        task = MidJourneyTaskModel(
            **{
                **form_data.model_dump(),
                "created_at": current_time,
                "updated_at": current_time,
            }
        )

        try:
            with get_db() as db:
                result = MidJourneyTask(**task.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)

                if result:
                    return MidJourneyTaskModel.model_validate(result)
                else:
                    return None
        except Exception as e:
            log.exception(f"Failed to insert new MidJourney task: {e}")
            return None

    def get_task_by_id(self, task_id: str) -> Optional[MidJourneyTaskModel]:
        """根据任务ID获取任务"""
        try:
            with get_db() as db:
                task = (
                    db.query(MidJourneyTask)
                    .filter(MidJourneyTask.task_id == task_id)
                    .first()
                )
                if task:
                    return MidJourneyTaskModel.model_validate(task)
                return None
        except Exception as e:
            log.exception(f"Failed to get task by id {task_id}: {e}")
            return None

    def get_tasks_by_user_id(
        self, user_id: str, limit: int = 50
    ) -> List[MidJourneyTaskModel]:
        """获取用户的任务列表"""
        try:
            with get_db() as db:
                tasks = (
                    db.query(MidJourneyTask)
                    .filter(MidJourneyTask.user_id == user_id)
                    .order_by(MidJourneyTask.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return [MidJourneyTaskModel.model_validate(task) for task in tasks]
        except Exception as e:
            log.exception(f"Failed to get tasks for user {user_id}: {e}")
            return []

    def get_all_tasks(self, limit: int = 100) -> List[MidJourneyTaskModel]:
        """获取所有任务（管理员用）"""
        try:
            with get_db() as db:
                tasks = (
                    db.query(MidJourneyTask)
                    .order_by(MidJourneyTask.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return [MidJourneyTaskModel.model_validate(task) for task in tasks]
        except Exception as e:
            log.exception(f"Failed to get all tasks: {e}")
            return []

    def update_task_by_id(
        self, task_id: str, update_data: Dict[str, Any]
    ) -> Optional[MidJourneyTaskModel]:
        """更新任务"""
        try:
            with get_db() as db:
                # 添加更新时间戳
                update_data["updated_at"] = int(time.time())

                # 更新任务
                result = (
                    db.query(MidJourneyTask)
                    .filter(MidJourneyTask.task_id == task_id)
                    .update(update_data)
                )

                if result > 0:
                    db.commit()
                    # 获取更新后的任务
                    task = (
                        db.query(MidJourneyTask)
                        .filter(MidJourneyTask.task_id == task_id)
                        .first()
                    )
                    if task:
                        return MidJourneyTaskModel.model_validate(task)

                return None
        except Exception as e:
            log.exception(f"Failed to update task {task_id}: {e}")
            return None

    def delete_task_by_id(self, task_id: str) -> bool:
        """删除任务"""
        try:
            with get_db() as db:
                result = (
                    db.query(MidJourneyTask)
                    .filter(MidJourneyTask.task_id == task_id)
                    .delete()
                )
                db.commit()
                return result > 0
        except Exception as e:
            log.exception(f"Failed to delete task {task_id}: {e}")
            return False

    def delete_tasks_by_user_id(self, user_id: str) -> bool:
        """删除用户的所有任务"""
        try:
            with get_db() as db:
                result = (
                    db.query(MidJourneyTask)
                    .filter(MidJourneyTask.user_id == user_id)
                    .delete()
                )
                db.commit()
                return result >= 0  # 即使删除0条记录也算成功
        except Exception as e:
            log.exception(f"Failed to delete tasks for user {user_id}: {e}")
            return False

    def get_completed_tasks_by_user_id(
        self, user_id: str, limit: int = 50
    ) -> List[MidJourneyTaskModel]:
        """获取用户已完成的任务"""
        try:
            with get_db() as db:
                tasks = (
                    db.query(MidJourneyTask)
                    .filter(
                        MidJourneyTask.user_id == user_id,
                        MidJourneyTask.status == "completed",
                        MidJourneyTask.image_url.isnot(None),
                    )
                    .order_by(MidJourneyTask.completed_at.desc())
                    .limit(limit)
                    .all()
                )
                return [MidJourneyTaskModel.model_validate(task) for task in tasks]
        except Exception as e:
            log.exception(f"Failed to get completed tasks for user {user_id}: {e}")
            return []

    def convert_to_legacy_format(self, task: MidJourneyTaskModel) -> Dict[str, Any]:
        """将数据库模型转换为旧版内存存储格式，确保向后兼容"""
        return {
            "task_id": task.task_id,
            "user_id": task.user_id,
            "mj_task_id": task.mj_task_id,
            "parent_task_id": task.parent_task_id,
            "prompt": task.prompt,
            "final_prompt": task.final_prompt,
            "mode": task.mode,
            "aspect_ratio": task.aspect_ratio,
            "negative_prompt": task.negative_prompt,
            "status": task.status,
            "progress": task.progress,
            "message": task.message,
            "image_url": task.image_url,
            "credits_used": task.credits_used,
            "created_at": task.created_at,  # 保持Unix时间戳格式
            "completed_at": task.completed_at,  # 保持Unix时间戳格式
            "error_message": task.error_message,
            "actions": task.actions or [],
            "seed": task.seed,
            "reference_images": task.reference_images or [],
            "advanced_params": task.advanced_params,
            "action_type": task.action_type,
            "button_index": task.button_index,
            "custom_id": task.custom_id,
        }


# 创建全局实例
MidJourneyTasks = MidJourneyTasksTable()
