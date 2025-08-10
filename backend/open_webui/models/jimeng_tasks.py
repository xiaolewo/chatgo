"""
即梦视频生成任务数据模型
管理即梦视频生成任务的存储和查询
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


class JimengTask(Base):
    __tablename__ = "jimeng_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)

    # 请求参数
    prompt = Column(Text)
    image_url = Column(Text)  # 图生视频时的图片URL
    duration = Column(Integer, default=5)  # 视频时长（秒）
    aspect_ratio = Column(String, default="16:9")  # 画面纵横比
    cfg_scale = Column(Float, default=0.5)  # 生成视频的自由度

    # 任务状态
    status = Column(
        String, default="SUBMITTED"
    )  # NOT_START, SUBMITTED, QUEUED, IN_PROGRESS, SUCCESS, FAILURE
    message = Column(Text, default="")
    credits_used = Column(Integer, default=0)
    fail_reason = Column(Text)  # 失败原因

    # 结果数据
    video_url = Column(Text)  # 生成的视频URL
    video_id = Column(String)  # 视频ID
    finish_time = Column(String)  # API完成时间

    # API相关数据
    request_params = Column(Text)  # JSON字符串存储请求参数
    api_response = Column(Text)  # JSON字符串存储API响应

    # 时间戳
    created_at = Column(
        BigInteger, default=lambda: int(time.time() * 1000)
    )  # 使用毫秒时间戳保持兼容性
    completed_at = Column(BigInteger)
    updated_at = Column(
        BigInteger,
        default=lambda: int(time.time() * 1000),
        onupdate=lambda: int(time.time() * 1000),
    )


####################
# Pydantic模型
####################


class JimengTaskForm(BaseModel):
    task_id: str
    user_id: str
    prompt: str
    image_url: Optional[str] = None
    duration: int = 5
    aspect_ratio: str = "16:9"
    cfg_scale: float = 0.5
    status: str = "SUBMITTED"
    message: str = ""
    credits_used: int = 0
    fail_reason: Optional[str] = None
    video_url: Optional[str] = None
    video_id: Optional[str] = None
    finish_time: Optional[str] = None
    request_params: Optional[Dict[str, Any]] = None
    api_response: Optional[Dict[str, Any]] = None


class JimengTaskResponse(BaseModel):
    task_id: str
    user_id: str
    prompt: str
    image_url: Optional[str]
    duration: int
    aspect_ratio: str
    cfg_scale: float
    status: str
    message: str
    credits_used: int
    fail_reason: Optional[str]
    video_url: Optional[str]
    video_id: Optional[str]
    finish_time: Optional[str]
    request_params: Optional[Dict[str, Any]]
    api_response: Optional[Dict[str, Any]]
    created_at: int
    completed_at: Optional[int]
    updated_at: int


####################
# 数据库操作类
####################


class JimengTasks:

    @staticmethod
    def insert_new_task(task_form: JimengTaskForm) -> Optional[JimengTask]:
        """创建新的即梦视频任务"""
        try:
            with SessionLocal() as session:
                # 处理JSON数据
                request_params_str = None
                if task_form.request_params:
                    request_params_str = json.dumps(task_form.request_params)

                api_response_str = None
                if task_form.api_response:
                    api_response_str = json.dumps(task_form.api_response)

                task = JimengTask(
                    task_id=task_form.task_id,
                    user_id=task_form.user_id,
                    prompt=task_form.prompt,
                    image_url=task_form.image_url,
                    duration=task_form.duration,
                    aspect_ratio=task_form.aspect_ratio,
                    cfg_scale=task_form.cfg_scale,
                    status=task_form.status,
                    message=task_form.message,
                    credits_used=task_form.credits_used,
                    fail_reason=task_form.fail_reason,
                    video_url=task_form.video_url,
                    video_id=task_form.video_id,
                    finish_time=task_form.finish_time,
                    request_params=request_params_str,
                    api_response=api_response_str,
                )

                session.add(task)
                session.commit()
                session.refresh(task)

                log.info(f"即梦视频任务创建成功: {task_form.task_id}")
                return task

        except Exception as e:
            log.error(f"创建即梦视频任务失败: {str(e)}")
            return None

    @staticmethod
    def get_task_by_id(task_id: str) -> Optional[JimengTask]:
        """根据任务ID获取任务"""
        try:
            with SessionLocal() as session:
                task = (
                    session.query(JimengTask)
                    .filter(JimengTask.task_id == task_id)
                    .first()
                )
                return task
        except Exception as e:
            log.error(f"获取即梦视频任务失败: {str(e)}")
            return None

    @staticmethod
    def get_tasks_by_user_id(user_id: str, limit: int = 50) -> List[JimengTask]:
        """根据用户ID获取任务列表"""
        try:
            with SessionLocal() as session:
                tasks = (
                    session.query(JimengTask)
                    .filter(JimengTask.user_id == user_id)
                    .order_by(JimengTask.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return tasks
        except Exception as e:
            log.error(f"获取用户即梦视频任务列表失败: {str(e)}")
            return []

    @staticmethod
    def get_all_tasks(limit: int = 100) -> List[JimengTask]:
        """获取所有任务（管理员用）"""
        try:
            with SessionLocal() as session:
                tasks = (
                    session.query(JimengTask)
                    .order_by(JimengTask.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return tasks
        except Exception as e:
            log.error(f"获取所有即梦视频任务失败: {str(e)}")
            return []

    @staticmethod
    def update_task_by_id(
        task_id: str, update_data: Dict[str, Any]
    ) -> Optional[JimengTask]:
        """更新任务信息"""
        try:
            with SessionLocal() as session:
                task = (
                    session.query(JimengTask)
                    .filter(JimengTask.task_id == task_id)
                    .first()
                )

                if not task:
                    log.warning(f"要更新的即梦视频任务不存在: {task_id}")
                    return None

                # 更新字段
                for key, value in update_data.items():
                    if hasattr(task, key):
                        # 特殊处理JSON数据
                        if key in ["request_params", "api_response"] and isinstance(
                            value, dict
                        ):
                            setattr(task, key, json.dumps(value))
                        else:
                            setattr(task, key, value)

                # 更新时间戳
                task.updated_at = int(time.time() * 1000)

                # 如果任务完成或失败，设置完成时间
                if (
                    update_data.get("status") in ["SUCCESS", "FAILURE"]
                    and not task.completed_at
                ):
                    task.completed_at = int(time.time() * 1000)

                session.commit()
                session.refresh(task)

                log.info(f"即梦视频任务更新成功: {task_id}")
                return task

        except Exception as e:
            log.error(f"更新即梦视频任务失败: {str(e)}")
            return None

    @staticmethod
    def delete_task_by_id(task_id: str) -> bool:
        """删除任务"""
        try:
            with SessionLocal() as session:
                task = (
                    session.query(JimengTask)
                    .filter(JimengTask.task_id == task_id)
                    .first()
                )

                if task:
                    session.delete(task)
                    session.commit()
                    log.info(f"即梦视频任务删除成功: {task_id}")
                    return True
                else:
                    log.warning(f"要删除的即梦视频任务不存在: {task_id}")
                    return False

        except Exception as e:
            log.error(f"删除即梦视频任务失败: {str(e)}")
            return False

    @staticmethod
    def get_user_task_count(user_id: str) -> int:
        """获取用户任务总数"""
        try:
            with SessionLocal() as session:
                count = (
                    session.query(JimengTask)
                    .filter(JimengTask.user_id == user_id)
                    .count()
                )
                return count
        except Exception as e:
            log.error(f"获取用户即梦视频任务数量失败: {str(e)}")
            return 0

    @staticmethod
    def get_tasks_by_status(status: str, limit: int = 100) -> List[JimengTask]:
        """根据状态获取任务列表"""
        try:
            with SessionLocal() as session:
                tasks = (
                    session.query(JimengTask)
                    .filter(JimengTask.status == status)
                    .order_by(JimengTask.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return tasks
        except Exception as e:
            log.error(f"根据状态获取即梦视频任务失败: {str(e)}")
            return []

    @staticmethod
    def convert_to_response_format(task: JimengTask) -> Dict[str, Any]:
        """将数据库模型转换为响应格式"""
        try:
            # 解析JSON数据
            request_params = None
            if task.request_params:
                try:
                    request_params = json.loads(task.request_params)
                except json.JSONDecodeError:
                    log.warning(f"解析request_params失败: {task.task_id}")
                    request_params = None

            api_response = None
            if task.api_response:
                try:
                    api_response = json.loads(task.api_response)
                except json.JSONDecodeError:
                    log.warning(f"解析api_response失败: {task.task_id}")
                    api_response = None

            return {
                "task_id": task.task_id,
                "user_id": task.user_id,
                "prompt": task.prompt,
                "image_url": task.image_url,
                "duration": task.duration,
                "aspect_ratio": task.aspect_ratio,
                "cfg_scale": task.cfg_scale,
                "status": task.status,
                "message": task.message,
                "credits_used": task.credits_used,
                "fail_reason": task.fail_reason,
                "video_url": task.video_url,
                "video_id": task.video_id,
                "finish_time": task.finish_time,
                "request_params": request_params,
                "api_response": api_response,
                "created_at": task.created_at,
                "completed_at": task.completed_at,
                "updated_at": task.updated_at,
            }
        except Exception as e:
            log.error(f"转换即梦视频任务格式失败: {str(e)}")
            return {}

    @staticmethod
    def get_task_statistics() -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            with SessionLocal() as session:
                total_tasks = session.query(JimengTask).count()
                success_tasks = (
                    session.query(JimengTask)
                    .filter(JimengTask.status == "SUCCESS")
                    .count()
                )
                failed_tasks = (
                    session.query(JimengTask)
                    .filter(JimengTask.status == "FAILURE")
                    .count()
                )
                processing_tasks = (
                    session.query(JimengTask)
                    .filter(
                        JimengTask.status.in_(["SUBMITTED", "QUEUED", "IN_PROGRESS"])
                    )
                    .count()
                )

                return {
                    "total_tasks": total_tasks,
                    "success_tasks": success_tasks,
                    "failed_tasks": failed_tasks,
                    "processing_tasks": processing_tasks,
                    "success_rate": (
                        (success_tasks / total_tasks * 100) if total_tasks > 0 else 0
                    ),
                }
        except Exception as e:
            log.error(f"获取即梦视频任务统计失败: {str(e)}")
            return {
                "total_tasks": 0,
                "success_tasks": 0,
                "failed_tasks": 0,
                "processing_tasks": 0,
                "success_rate": 0,
            }
