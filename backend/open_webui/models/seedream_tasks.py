"""
即梦3.0任务数据模型
管理即梦3.0图像生成任务的存储和查询
"""

import time
import json
from sqlalchemy import Column, String, Integer, Text, Boolean, Float, BigInteger
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from open_webui.internal.db import Base, SessionLocal
from open_webui.models.users import UserModel

import logging

log = logging.getLogger(__name__)

####################
# 数据库模型
####################


class SeedreamTask(Base):
    __tablename__ = "seedream_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)

    # 请求参数
    prompt = Column(Text)
    use_pre_llm = Column(Boolean, default=False)
    seed = Column(Integer, default=-1)
    scale = Column(Float, default=2.5)
    width = Column(Integer, default=1328)
    height = Column(Integer, default=1328)
    return_url = Column(Boolean, default=True)
    logo_info = Column(Text)  # JSON字符串存储水印信息

    # 任务状态
    status = Column(
        String, default="submitted"
    )  # submitted, processing, completed, failed
    message = Column(Text, default="")
    credits_used = Column(Integer, default=0)

    # 结果数据
    image_url = Column(Text)
    image_data = Column(Text)  # Base64图像数据
    request_id = Column(String)  # 即梦3.0的请求ID
    time_elapsed = Column(String)  # API处理时间

    # 时间戳
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    completed_at = Column(BigInteger)
    updated_at = Column(
        BigInteger, default=lambda: int(time.time()), onupdate=lambda: int(time.time())
    )


####################
# Pydantic模型
####################


class SeedreamTaskForm(BaseModel):
    task_id: str
    user_id: str
    prompt: str
    use_pre_llm: Optional[bool] = False
    seed: Optional[int] = -1
    scale: Optional[float] = 2.5
    width: Optional[int] = 1328
    height: Optional[int] = 1328
    return_url: Optional[bool] = True
    logo_info: Optional[Dict[str, Any]] = None
    status: str = "submitted"
    message: str = ""
    credits_used: int = 0
    image_url: Optional[str] = None
    image_data: Optional[str] = None
    request_id: Optional[str] = None
    time_elapsed: Optional[str] = None


class SeedreamTaskResponse(BaseModel):
    task_id: str
    user_id: str
    prompt: str
    use_pre_llm: bool
    seed: int
    scale: float
    width: int
    height: int
    return_url: bool
    logo_info: Optional[Dict[str, Any]]
    status: str
    message: str
    credits_used: int
    image_url: Optional[str]
    image_data: Optional[str]
    request_id: Optional[str]
    time_elapsed: Optional[str]
    created_at: int
    completed_at: Optional[int]
    updated_at: int


####################
# 数据库操作类
####################


class SeedreamTasks:

    @staticmethod
    def insert_new_task(task_form: SeedreamTaskForm) -> Optional[SeedreamTask]:
        """创建新的即梦3.0任务"""
        try:
            with SessionLocal() as session:
                # 处理logo_info
                logo_info_str = None
                if task_form.logo_info:
                    logo_info_str = json.dumps(task_form.logo_info)

                task = SeedreamTask(
                    task_id=task_form.task_id,
                    user_id=task_form.user_id,
                    prompt=task_form.prompt,
                    use_pre_llm=task_form.use_pre_llm,
                    seed=task_form.seed,
                    scale=task_form.scale,
                    width=task_form.width,
                    height=task_form.height,
                    return_url=task_form.return_url,
                    logo_info=logo_info_str,
                    status=task_form.status,
                    message=task_form.message,
                    credits_used=task_form.credits_used,
                    image_url=task_form.image_url,
                    image_data=task_form.image_data,
                    request_id=task_form.request_id,
                    time_elapsed=task_form.time_elapsed,
                )

                session.add(task)
                session.commit()
                session.refresh(task)

                log.info(f"即梦3.0任务创建成功: {task_form.task_id}")
                return task

        except Exception as e:
            log.error(f"创建即梦3.0任务失败: {str(e)}")
            return None

    @staticmethod
    def get_task_by_id(task_id: str) -> Optional[SeedreamTask]:
        """根据任务ID获取任务"""
        try:
            with SessionLocal() as session:
                task = (
                    session.query(SeedreamTask)
                    .filter(SeedreamTask.task_id == task_id)
                    .first()
                )
                return task
        except Exception as e:
            log.error(f"获取即梦3.0任务失败: {str(e)}")
            return None

    @staticmethod
    def get_tasks_by_user_id(user_id: str, limit: int = 50) -> List[SeedreamTask]:
        """根据用户ID获取任务列表"""
        try:
            with SessionLocal() as session:
                tasks = (
                    session.query(SeedreamTask)
                    .filter(SeedreamTask.user_id == user_id)
                    .order_by(SeedreamTask.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return tasks
        except Exception as e:
            log.error(f"获取用户即梦3.0任务列表失败: {str(e)}")
            return []

    @staticmethod
    def get_all_tasks(limit: int = 100) -> List[SeedreamTask]:
        """获取所有任务（管理员用）"""
        try:
            with SessionLocal() as session:
                tasks = (
                    session.query(SeedreamTask)
                    .order_by(SeedreamTask.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return tasks
        except Exception as e:
            log.error(f"获取所有即梦3.0任务失败: {str(e)}")
            return []

    @staticmethod
    def update_task_by_id(
        task_id: str, update_data: Dict[str, Any]
    ) -> Optional[SeedreamTask]:
        """更新任务信息"""
        try:
            with SessionLocal() as session:
                task = (
                    session.query(SeedreamTask)
                    .filter(SeedreamTask.task_id == task_id)
                    .first()
                )

                if not task:
                    log.warning(f"要更新的即梦3.0任务不存在: {task_id}")
                    return None

                # 更新字段
                for key, value in update_data.items():
                    if hasattr(task, key):
                        # 特殊处理logo_info
                        if key == "logo_info" and isinstance(value, dict):
                            setattr(task, key, json.dumps(value))
                        else:
                            setattr(task, key, value)

                # 更新时间戳
                task.updated_at = int(time.time())

                session.commit()
                session.refresh(task)

                log.info(f"即梦3.0任务更新成功: {task_id}")
                return task

        except Exception as e:
            log.error(f"更新即梦3.0任务失败: {str(e)}")
            return None

    @staticmethod
    def delete_task_by_id(task_id: str) -> bool:
        """删除任务"""
        try:
            with SessionLocal() as session:
                task = (
                    session.query(SeedreamTask)
                    .filter(SeedreamTask.task_id == task_id)
                    .first()
                )

                if task:
                    session.delete(task)
                    session.commit()
                    log.info(f"即梦3.0任务删除成功: {task_id}")
                    return True
                else:
                    log.warning(f"要删除的即梦3.0任务不存在: {task_id}")
                    return False

        except Exception as e:
            log.error(f"删除即梦3.0任务失败: {str(e)}")
            return False

    @staticmethod
    def get_user_task_count(user_id: str) -> int:
        """获取用户任务总数"""
        try:
            with SessionLocal() as session:
                count = (
                    session.query(SeedreamTask)
                    .filter(SeedreamTask.user_id == user_id)
                    .count()
                )
                return count
        except Exception as e:
            log.error(f"获取用户即梦3.0任务数量失败: {str(e)}")
            return 0

    @staticmethod
    def get_tasks_by_status(status: str, limit: int = 100) -> List[SeedreamTask]:
        """根据状态获取任务列表"""
        try:
            with SessionLocal() as session:
                tasks = (
                    session.query(SeedreamTask)
                    .filter(SeedreamTask.status == status)
                    .order_by(SeedreamTask.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return tasks
        except Exception as e:
            log.error(f"根据状态获取即梦3.0任务失败: {str(e)}")
            return []

    @staticmethod
    def convert_to_response_format(task: SeedreamTask) -> Dict[str, Any]:
        """将数据库模型转换为响应格式"""
        try:
            # 解析logo_info
            logo_info = None
            if task.logo_info:
                try:
                    logo_info = json.loads(task.logo_info)
                except json.JSONDecodeError:
                    log.warning(f"解析logo_info失败: {task.task_id}")
                    logo_info = None

            return {
                "task_id": task.task_id,
                "user_id": task.user_id,
                "prompt": task.prompt,
                "use_pre_llm": task.use_pre_llm,
                "seed": task.seed,
                "scale": task.scale,
                "width": task.width,
                "height": task.height,
                "return_url": task.return_url,
                "logo_info": logo_info,
                "status": task.status,
                "message": task.message,
                "credits_used": task.credits_used,
                "image_url": task.image_url,
                "image_data": task.image_data,
                "request_id": task.request_id,
                "time_elapsed": task.time_elapsed,
                "created_at": task.created_at,
                "completed_at": task.completed_at,
                "updated_at": task.updated_at,
            }
        except Exception as e:
            log.error(f"转换即梦3.0任务格式失败: {str(e)}")
            return {}

    @staticmethod
    def get_task_statistics() -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            with SessionLocal() as session:
                total_tasks = session.query(SeedreamTask).count()
                completed_tasks = (
                    session.query(SeedreamTask)
                    .filter(SeedreamTask.status == "completed")
                    .count()
                )
                failed_tasks = (
                    session.query(SeedreamTask)
                    .filter(SeedreamTask.status == "failed")
                    .count()
                )
                processing_tasks = (
                    session.query(SeedreamTask)
                    .filter(SeedreamTask.status.in_(["submitted", "processing"]))
                    .count()
                )

                return {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "processing_tasks": processing_tasks,
                    "success_rate": (
                        (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                    ),
                }
        except Exception as e:
            log.error(f"获取即梦3.0任务统计失败: {str(e)}")
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "processing_tasks": 0,
                "success_rate": 0,
            }
