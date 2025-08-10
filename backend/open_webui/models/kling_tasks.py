"""
可灵视频生成任务数据模型
管理可灵文生视频任务的存储和查询
"""

import time
import json
import uuid
from sqlalchemy import Column, String, Integer, Text, Boolean, Float, BigInteger
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from open_webui.internal.db import Base, SessionLocal
from open_webui.models.users import UserModel

import logging

log = logging.getLogger(__name__)

####################
# 数据库模型
####################


class KlingTask(Base):
    __tablename__ = "kling_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    external_task_id = Column(String, nullable=True)  # 自定义任务ID

    # 请求参数
    model_name = Column(String, default="kling-v1")
    prompt = Column(Text)
    negative_prompt = Column(Text, nullable=True)
    cfg_scale = Column(Float, default=0.5)
    mode = Column(String, default="std")  # std, pro
    camera_control = Column(Text)  # JSON字符串存储摄像机控制信息
    aspect_ratio = Column(String, default="16:9")  # 16:9, 9:16, 1:1
    duration = Column(String, default="5")  # 5, 10
    callback_url = Column(String, nullable=True)

    # 任务状态
    status = Column(
        String, default="submitted"
    )  # submitted, processing, succeed, failed
    task_status_msg = Column(Text, default="")
    credits_used = Column(Integer, default=0)

    # 结果数据
    video_id = Column(String, nullable=True)  # 生成视频的ID
    video_url = Column(Text, nullable=True)  # 视频URL
    video_duration = Column(String, nullable=True)  # 视频时长
    request_id = Column(String, nullable=True)  # 可灵的请求ID

    # 时间戳
    created_at = Column(BigInteger, default=lambda: int(time.time() * 1000))
    updated_at = Column(BigInteger, default=lambda: int(time.time() * 1000))


####################
# Pydantic模型
####################


class CameraControlConfig(BaseModel):
    """摄像机控制配置"""

    horizontal: Optional[float] = Field(0, ge=-10, le=10, description="水平运镜")
    vertical: Optional[float] = Field(0, ge=-10, le=10, description="垂直运镜")
    pan: Optional[float] = Field(0, ge=-10, le=10, description="水平摇镜")
    tilt: Optional[float] = Field(0, ge=-10, le=10, description="垂直摇镜")
    roll: Optional[float] = Field(0, ge=-10, le=10, description="旋转运镜")
    zoom: Optional[float] = Field(0, ge=-10, le=10, description="变焦")


class CameraControl(BaseModel):
    """摄像机控制"""

    type: Optional[str] = Field(None, description="运镜类型")
    config: Optional[CameraControlConfig] = Field(None, description="运镜配置")


class KlingTaskForm(BaseModel):
    """可灵任务创建表单"""

    model_name: Optional[str] = Field("kling-v1", description="模型名称")
    prompt: str = Field(..., min_length=1, max_length=500, description="正向文本提示词")
    negative_prompt: Optional[str] = Field(
        None, max_length=200, description="负向文本提示词"
    )
    cfg_scale: Optional[float] = Field(0.5, ge=0, le=1, description="生成视频的自由度")
    mode: Optional[str] = Field("std", description="生成模式：std或pro")
    camera_control: Optional[CameraControl] = Field(None, description="摄像机运动控制")
    aspect_ratio: Optional[str] = Field("16:9", description="画面纵横比")
    duration: Optional[str] = Field("5", description="视频时长")
    callback_url: Optional[str] = Field(None, description="回调地址")
    external_task_id: Optional[str] = Field(None, description="自定义任务ID")

    @validator("model_name")
    def validate_model_name(cls, v):
        valid_models = [
            "kling-v1",
            "kling-v1-6",
            "kling-v2-master",
            "kling-v2-1-master",
        ]
        if v not in valid_models:
            raise ValueError(f'模型名称必须是以下之一: {", ".join(valid_models)}')
        return v

    @validator("mode")
    def validate_mode(cls, v):
        if v not in ["std", "pro"]:
            raise ValueError("模式必须是std或pro")
        return v

    @validator("aspect_ratio")
    def validate_aspect_ratio(cls, v):
        if v not in ["16:9", "9:16", "1:1"]:
            raise ValueError("画面比例必须是16:9、9:16或1:1")
        return v

    @validator("duration")
    def validate_duration(cls, v):
        if v not in ["5", "10"]:
            raise ValueError("视频时长必须是5秒或10秒")
        return v


class KlingTaskResponse(BaseModel):
    """可灵任务响应模型"""

    id: int
    task_id: str
    user_id: str
    external_task_id: Optional[str] = None
    model_name: str
    prompt: str
    negative_prompt: Optional[str] = None
    cfg_scale: float
    mode: str
    camera_control: Optional[Dict[str, Any]] = None
    aspect_ratio: str
    duration: str
    status: str
    task_status_msg: str
    credits_used: int
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    video_duration: Optional[str] = None
    request_id: Optional[str] = None
    created_at: int
    updated_at: int


####################
# 数据库操作类
####################


class KlingTasks:

    @staticmethod
    def insert_new_task(
        task_form_data: Dict[str, Any], user_id: str, task_id: str
    ) -> Optional[KlingTask]:
        """创建新的可灵任务"""
        try:
            with SessionLocal() as session:
                camera_control_json = None
                if task_form_data.get("camera_control"):
                    camera_control_json = json.dumps(task_form_data["camera_control"])

                task = KlingTask(
                    task_id=task_id,
                    user_id=user_id,
                    external_task_id=task_form_data.get("external_task_id"),
                    model_name=task_form_data.get("model_name", "kling-v1"),
                    prompt=task_form_data["prompt"],
                    negative_prompt=task_form_data.get("negative_prompt"),
                    cfg_scale=task_form_data.get("cfg_scale", 0.5),
                    mode=task_form_data.get("mode", "std"),
                    camera_control=camera_control_json,
                    aspect_ratio=task_form_data.get("aspect_ratio", "16:9"),
                    duration=task_form_data.get("duration", "5"),
                    callback_url=task_form_data.get("callback_url"),
                    status="submitted",
                    task_status_msg="任务已提交",
                    credits_used=task_form_data.get("credits_used", 0),
                )

                session.add(task)
                session.commit()
                session.refresh(task)

                log.info(f"可灵任务创建成功: {task_id}")
                return task
        except Exception as e:
            log.error(f"创建可灵任务失败: {e}")
            return None

    @staticmethod
    def get_task_by_id(task_id: str) -> Optional[KlingTask]:
        """根据任务ID获取任务"""
        try:
            with SessionLocal() as session:
                task = (
                    session.query(KlingTask)
                    .filter(KlingTask.task_id == task_id)
                    .first()
                )
                return task
        except Exception as e:
            log.error(f"获取可灵任务失败: {e}")
            return None

    @staticmethod
    def get_task_by_external_id(
        external_task_id: str, user_id: str
    ) -> Optional[KlingTask]:
        """根据自定义任务ID获取任务"""
        try:
            with SessionLocal() as session:
                task = (
                    session.query(KlingTask)
                    .filter(
                        KlingTask.external_task_id == external_task_id,
                        KlingTask.user_id == user_id,
                    )
                    .first()
                )
                return task
        except Exception as e:
            log.error(f"获取可灵任务失败: {e}")
            return None

    @staticmethod
    def get_tasks_by_user_id(user_id: str, limit: int = 50) -> List[KlingTask]:
        """根据用户ID获取任务列表"""
        try:
            with SessionLocal() as session:
                tasks = (
                    session.query(KlingTask)
                    .filter(KlingTask.user_id == user_id)
                    .order_by(KlingTask.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return tasks
        except Exception as e:
            log.error(f"获取用户可灵任务列表失败: {e}")
            return []

    @staticmethod
    def update_task_by_id(
        task_id: str, update_data: Dict[str, Any]
    ) -> Optional[KlingTask]:
        """更新任务信息"""
        try:
            with SessionLocal() as session:
                task = (
                    session.query(KlingTask)
                    .filter(KlingTask.task_id == task_id)
                    .first()
                )

                if not task:
                    log.warning(f"要更新的可灵任务不存在: {task_id}")
                    return None

                # 更新字段
                for key, value in update_data.items():
                    if hasattr(task, key):
                        # 特殊处理camera_control
                        if key == "camera_control" and isinstance(value, dict):
                            setattr(task, key, json.dumps(value))
                        else:
                            setattr(task, key, value)

                # 更新时间戳
                task.updated_at = int(time.time() * 1000)

                session.commit()
                session.refresh(task)

                log.info(f"可灵任务更新成功: {task_id}")
                return task

        except Exception as e:
            log.error(f"更新可灵任务失败: {e}")
            return None

    @staticmethod
    def delete_task_by_id(task_id: str) -> bool:
        """删除任务"""
        try:
            with SessionLocal() as session:
                task = (
                    session.query(KlingTask)
                    .filter(KlingTask.task_id == task_id)
                    .first()
                )

                if task:
                    session.delete(task)
                    session.commit()
                    log.info(f"可灵任务删除成功: {task_id}")
                    return True
                else:
                    log.warning(f"要删除的可灵任务不存在: {task_id}")
                    return False

        except Exception as e:
            log.error(f"删除可灵任务失败: {e}")
            return False

    @staticmethod
    def get_user_task_count(user_id: str) -> int:
        """获取用户任务总数"""
        try:
            with SessionLocal() as session:
                count = (
                    session.query(KlingTask)
                    .filter(KlingTask.user_id == user_id)
                    .count()
                )
                return count
        except Exception as e:
            log.error(f"获取用户可灵任务数量失败: {e}")
            return 0

    @staticmethod
    def get_tasks_by_status(status: str, limit: int = 100) -> List[KlingTask]:
        """根据状态获取任务列表"""
        try:
            with SessionLocal() as session:
                tasks = (
                    session.query(KlingTask)
                    .filter(KlingTask.status == status)
                    .order_by(KlingTask.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return tasks
        except Exception as e:
            log.error(f"根据状态获取可灵任务失败: {e}")
            return []

    @staticmethod
    def convert_to_response_format(task: KlingTask) -> Dict[str, Any]:
        """将数据库模型转换为响应格式"""
        try:
            # 解析camera_control
            camera_control = None
            if task.camera_control:
                try:
                    camera_control = json.loads(task.camera_control)
                except json.JSONDecodeError:
                    log.warning(f"解析camera_control失败: {task.task_id}")
                    camera_control = None

            return {
                "task_id": task.task_id,
                "user_id": task.user_id,
                "external_task_id": task.external_task_id,
                "model_name": task.model_name,
                "prompt": task.prompt,
                "negative_prompt": task.negative_prompt,
                "cfg_scale": task.cfg_scale,
                "mode": task.mode,
                "camera_control": camera_control,
                "aspect_ratio": task.aspect_ratio,
                "duration": task.duration,
                "status": task.status,
                "task_status_msg": task.task_status_msg,
                "credits_used": task.credits_used,
                "video_id": task.video_id,
                "video_url": task.video_url,
                "video_duration": task.video_duration,
                "request_id": task.request_id,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }
        except Exception as e:
            log.error(f"转换可灵任务格式失败: {e}")
            return {}

    @staticmethod
    def get_task_statistics() -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            with SessionLocal() as session:
                total_tasks = session.query(KlingTask).count()
                succeed_tasks = (
                    session.query(KlingTask)
                    .filter(KlingTask.status == "succeed")
                    .count()
                )
                failed_tasks = (
                    session.query(KlingTask)
                    .filter(KlingTask.status == "failed")
                    .count()
                )
                processing_tasks = (
                    session.query(KlingTask)
                    .filter(KlingTask.status.in_(["submitted", "processing"]))
                    .count()
                )

                return {
                    "total_tasks": total_tasks,
                    "succeed_tasks": succeed_tasks,
                    "failed_tasks": failed_tasks,
                    "processing_tasks": processing_tasks,
                    "success_rate": (
                        (succeed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                    ),
                }
        except Exception as e:
            log.error(f"获取可灵任务统计失败: {e}")
            return {
                "total_tasks": 0,
                "succeed_tasks": 0,
                "failed_tasks": 0,
                "processing_tasks": 0,
                "success_rate": 0,
            }
