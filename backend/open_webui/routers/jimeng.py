"""
即梦 (JiMeng) 视频生成 API Integration Router
提供即梦文生视频API的集成接口
"""

import uuid
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel, Field, validator
import httpx
import logging

from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail
from open_webui.models.jimeng_tasks import JimengTasks, JimengTaskForm
from open_webui.config import (
    JIMENG_ENABLED,
    JIMENG_API_URL,
    JIMENG_API_KEY,
    JIMENG_CREDITS_5S,
    JIMENG_CREDITS_10S,
)
from decimal import Decimal

log = logging.getLogger(__name__)

router = APIRouter()


# 任务状态常量
class TaskStatus:
    NOT_START = "NOT_START"
    SUBMITTED = "SUBMITTED"
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"


class JimengConfig(BaseModel):
    """即梦配置模型"""

    enabled: bool = False
    api_url: str = ""  # Base URL，例如: https://api.example.com
    api_key: str = ""  # Bearer token
    credits_5s: int = 5  # 5秒视频积分消耗
    credits_10s: int = 10  # 10秒视频积分消耗


class JimengGenerateRequest(BaseModel):
    """即梦视频生成请求模型"""

    prompt: str = Field(..., min_length=1, description="文本提示词")
    image_url: Optional[str] = Field(None, description="图生视频时的图片URL")
    duration: int = Field(5, description="视频时长（秒）")
    aspect_ratio: str = Field("16:9", description="画面纵横比")
    cfg_scale: float = Field(0.5, description="生成视频的自由度")

    @validator("duration")
    def validate_duration(cls, v):
        if v not in [5, 10]:
            raise ValueError("duration必须是5或10")
        return v

    @validator("aspect_ratio")
    def validate_aspect_ratio(cls, v):
        valid_ratios = ["1:1", "21:9", "16:9", "9:16", "4:3", "3:4"]
        if v not in valid_ratios:
            raise ValueError(f"aspect_ratio必须是{valid_ratios}之一")
        return v


####################
# 配置管理
####################


@router.get("/config")
async def get_jimeng_config(request: Request, user=Depends(get_admin_user)):
    """获取即梦配置"""
    try:
        return {
            "enabled": JIMENG_ENABLED.value,
            "api_url": JIMENG_API_URL.value,
            "api_key": JIMENG_API_KEY.value,
            "credits_5s": JIMENG_CREDITS_5S.value,
            "credits_10s": JIMENG_CREDITS_10S.value,
        }
    except Exception as e:
        log.error(f"获取即梦配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@router.post("/config")
async def update_jimeng_config(
    request: Request, config: JimengConfig, user=Depends(get_admin_user)
):
    """更新即梦配置"""
    try:
        # 更新配置值
        JIMENG_ENABLED.value = config.enabled
        JIMENG_API_URL.value = config.api_url
        JIMENG_API_KEY.value = config.api_key
        JIMENG_CREDITS_5S.value = config.credits_5s
        JIMENG_CREDITS_10S.value = config.credits_10s

        # 保存到数据库
        JIMENG_ENABLED.save()
        JIMENG_API_URL.save()
        JIMENG_API_KEY.save()
        JIMENG_CREDITS_5S.save()
        JIMENG_CREDITS_10S.save()

        return {"message": "即梦配置已更新"}
    except Exception as e:
        log.error(f"更新即梦配置失败: {e}")
        raise HTTPException(status_code=500, detail="更新配置失败")


@router.post("/verify")
async def verify_jimeng_connection(request: Request, user=Depends(get_admin_user)):
    """验证即梦API连接"""
    try:
        api_url = JIMENG_API_URL.value
        api_key = JIMENG_API_KEY.value

        if not api_url or not api_key:
            raise HTTPException(status_code=400, detail="API URL和API Key不能为空")

        # 构建测试请求URL
        test_url = f"{api_url}/jimeng/submit/videos"

        # 发送测试请求（使用最小参数来验证API连接和认证）
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                test_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": "test connection",
                    "duration": 5,
                    "aspect_ratio": "16:9",
                    "cfg_scale": 0.5,
                },
            )

            log.info(f"即梦API测试响应: HTTP {response.status_code}")

            # 检查响应状态
            if response.status_code == 200:
                try:
                    result = response.json()
                    log.info(f"即梦API测试响应内容: {result}")
                    if result.get("code") == "success":
                        return {"message": "连接成功，API正常", "status": "success"}
                    else:
                        return {
                            "message": f"API错误: {result.get('message', '未知错误')}",
                            "status": "error",
                        }
                except Exception as e:
                    log.error(f"解析API响应失败: {e}")
                    return {"message": "API响应解析失败", "status": "error"}
            elif response.status_code == 401 or response.status_code == 403:
                return {
                    "message": f"API Key无效或权限不足: HTTP {response.status_code}",
                    "status": "error",
                }
            elif response.status_code == 400:
                log.warning(f"API参数错误，但连接正常")
                return {"message": "连接成功，但参数格式有误", "status": "warning"}
            else:
                return {
                    "message": f"连接失败: HTTP {response.status_code}",
                    "status": "error",
                }

    except Exception as e:
        log.error(f"验证即梦连接失败: {e}")
        return {"message": f"连接失败: {str(e)}", "status": "error"}


####################
# 视频生成相关
####################


@router.post("/generate")
async def generate_video(
    request: Request,
    generate_request: JimengGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """生成视频"""
    try:
        log.info(f"收到即梦视频生成请求 - 用户: {user.id}")
        log.info(
            f"请求参数: prompt长度={len(generate_request.prompt)}, duration={generate_request.duration}, aspect_ratio={generate_request.aspect_ratio}"
        )

        # 检查服务是否启用
        jimeng_enabled = JIMENG_ENABLED.value
        log.info(f"即梦服务启用状态: {jimeng_enabled}")

        if not jimeng_enabled:
            log.warning("即梦服务未启用")
            raise HTTPException(
                status_code=400,
                detail="即梦服务未启用，请先在管理员设置中启用并配置即梦服务",
            )

        # 检查API配置
        api_url = JIMENG_API_URL.value
        api_key = JIMENG_API_KEY.value

        log.info(
            f"即梦API配置 - URL: {api_url[:50] if api_url else 'None'}..., Key: {'已配置' if api_key else 'None'}"
        )

        if not api_url or not api_key:
            log.warning("即梦API配置不完整")
            raise HTTPException(
                status_code=400,
                detail="API配置不完整，请在管理员设置中配置即梦API URL和API Key",
            )

        # 计算积分消耗
        if generate_request.duration == 5:
            credits_cost = JIMENG_CREDITS_5S.value
        else:
            credits_cost = JIMENG_CREDITS_10S.value

        # 检查用户积分
        try:
            user_credit = Credits.get_credit_by_user_id(user.id)
            if not user_credit or user_credit.credit < credits_cost:
                current_credits = user_credit.credit if user_credit else 0
                log.warning(
                    f"用户 {user.id} 积分不足: 当前{current_credits}, 需要{credits_cost}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"积分不足，当前{current_credits}v豆，需要{credits_cost}v豆",
                )
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"检查积分失败: {e}")
            raise HTTPException(status_code=400, detail="积分系统错误")

        # 构建即梦API请求
        jimeng_api_url = f"{api_url}/jimeng/submit/videos"

        # 构建请求参数
        api_params = {
            "prompt": generate_request.prompt,
            "duration": generate_request.duration,
            "aspect_ratio": generate_request.aspect_ratio,
            "cfg_scale": generate_request.cfg_scale,
        }

        # 添加可选参数
        if generate_request.image_url:
            api_params["image_url"] = generate_request.image_url

        # 调用即梦API
        log.info(f"用户 {user.id} 发起视频生成请求，调用即梦API: {jimeng_api_url}")
        log.info(f"请求参数: {json.dumps(api_params, ensure_ascii=False, indent=2)}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                jimeng_api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=api_params,
            )

            log.info(f"即梦API响应状态: HTTP {response.status_code}")

            if not response.is_success:
                error_detail = f"即梦API调用失败: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    log.error(f"即梦API错误响应: {error_data}")
                    if "message" in error_data:
                        error_detail = f"即梦API错误: {error_data['message']}"
                except:
                    error_detail = f"即梦API调用失败: HTTP {response.status_code}"

                log.error(f"即梦API调用失败: {error_detail}")
                raise HTTPException(status_code=400, detail=error_detail)

            # 解析API响应
            try:
                api_result = response.json()
                log.info(f"即梦API成功响应: {api_result}")
            except Exception as e:
                log.error(f"解析即梦API响应失败: {e}")
                raise HTTPException(status_code=500, detail="即梦API响应解析失败")

            # 检查API响应格式
            if api_result.get("code") != "success":
                error_msg = api_result.get("message", "未知错误")
                log.error(f"即梦API业务错误: {error_msg}")
                raise HTTPException(status_code=400, detail=f"即梦API错误: {error_msg}")

            # 提取任务ID
            task_id = api_result.get("data")
            if not task_id:
                log.error("即梦API响应缺少任务ID")
                raise HTTPException(status_code=500, detail="即梦API响应格式错误")

            log.info(f"即梦API成功创建任务: task_id={task_id}")

            # 扣除用户积分
            try:
                user_credit = Credits.get_credit_by_user_id(user.id)
                old_credits = user_credit.credit
                Credits.update_credit_by_user_id(
                    user.id, user_credit.credit - credits_cost
                )
                log.info(
                    f"用户 {user.id} 积分扣除成功: {old_credits} -> {old_credits - credits_cost} (扣除{credits_cost})"
                )
            except Exception as e:
                log.error(f"扣除积分失败: {e}")
                # 注意：这里不抛出异常，因为外部API已经调用成功

            # 保存任务到数据库
            task_form = JimengTaskForm(
                task_id=task_id,
                user_id=user.id,
                prompt=generate_request.prompt,
                image_url=generate_request.image_url,
                duration=generate_request.duration,
                aspect_ratio=generate_request.aspect_ratio,
                cfg_scale=generate_request.cfg_scale,
                status=TaskStatus.SUBMITTED,
                credits_used=credits_cost,
                request_params=api_params,
                api_response=api_result,
            )

            stored_task = JimengTasks.insert_new_task(task_form)
            if not stored_task:
                log.error(f"任务存储失败: {task_id}")
                # 不抛出异常，任务已经提交到即梦平台

            log.info(
                f"视频生成任务成功提交到即梦平台: user_id={user.id}, task_id={task_id}"
            )

            # 启动后台任务轮询状态
            background_tasks.add_task(
                poll_task_status, request.app, task_id, api_url, api_key
            )

            return {
                "task_id": task_id,
                "status": TaskStatus.SUBMITTED,
                "message": "视频生成任务已提交到即梦平台",
                "credits_used": credits_cost,
            }

    except HTTPException as he:
        log.error(f"HTTP异常: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        log.error(f"生成视频失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成视频失败: {str(e)}")


async def poll_task_status(app, task_id: str, api_url: str, api_key: str):
    """后台任务：轮询任务状态"""
    max_attempts = 60  # 最多尝试60次
    poll_interval = 5  # 每5秒查询一次

    for attempt in range(max_attempts):
        try:
            await asyncio.sleep(poll_interval)

            # 构建查询URL
            status_url = f"{api_url}/jimeng/fetch/{task_id}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    status_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )

                if response.is_success:
                    result = response.json()

                    if result.get("code") == "success" and "data" in result:
                        task_data = result["data"]
                        new_status = task_data.get("status")

                        # 更新任务状态到数据库
                        stored_task = JimengTasks.get_task_by_id(task_id)
                        if stored_task:
                            old_status = stored_task.status

                            # 详细记录API响应用于调试
                            log.info(f"即梦API响应详细数据 - task_id: {task_id}")
                            log.info(
                                f"API响应原始数据: {json.dumps(result, ensure_ascii=False, indent=2)}"
                            )
                            log.info(
                                f"task_data内容: {json.dumps(task_data, ensure_ascii=False, indent=2)}"
                            )

                            update_data = {"status": new_status}

                            # 如果任务失败，记录失败原因
                            if new_status == TaskStatus.FAILURE:
                                update_data["fail_reason"] = task_data.get(
                                    "fail_reason", "未知错误"
                                )

                            # 如果任务成功，提取视频信息（尝试多种可能的数据结构）
                            if new_status == TaskStatus.SUCCESS:
                                video_url = None
                                video_id = None

                                # 尝试不同的数据结构路径
                                if task_data.get("data") and task_data["data"].get(
                                    "data"
                                ):
                                    # 原来的路径：task_data.data.data.video
                                    video_info = task_data["data"]["data"]
                                    if video_info.get("video"):
                                        video_url = video_info["video"]
                                        video_id = task_data.get("task_id")
                                        log.info(
                                            f"从路径 data.data.video 提取到视频URL: {video_url}"
                                        )

                                # 尝试直接从task_data.data获取
                                elif task_data.get("data") and task_data["data"].get(
                                    "video"
                                ):
                                    video_url = task_data["data"]["video"]
                                    video_id = task_data.get("task_id")
                                    log.info(
                                        f"从路径 data.video 提取到视频URL: {video_url}"
                                    )

                                # 尝试直接从task_data获取
                                elif task_data.get("video"):
                                    video_url = task_data["video"]
                                    video_id = task_data.get("task_id")
                                    log.info(f"从路径 video 提取到视频URL: {video_url}")

                                # 尝试从video_url字段获取
                                elif task_data.get("video_url"):
                                    video_url = task_data["video_url"]
                                    video_id = task_data.get("task_id")
                                    log.info(
                                        f"从路径 video_url 提取到视频URL: {video_url}"
                                    )

                                if video_url:
                                    update_data.update(
                                        {
                                            "video_url": video_url,
                                            "video_id": video_id,
                                            "finish_time": task_data.get("finish_time"),
                                        }
                                    )
                                    log.info(
                                        f"成功提取视频信息 - URL: {video_url}, ID: {video_id}"
                                    )
                                else:
                                    log.warning(
                                        f"任务 {task_id} 已成功但无法提取视频URL，task_data结构: {list(task_data.keys())}"
                                    )

                            # 更新到数据库
                            JimengTasks.update_task_by_id(task_id, update_data)

                            log.info(
                                f"任务 {task_id} 状态更新: {old_status} -> {new_status}"
                            )

                            # 如果任务已完成或失败，停止轮询
                            if new_status in [TaskStatus.SUCCESS, TaskStatus.FAILURE]:
                                break

        except Exception as e:
            log.error(f"轮询任务 {task_id} 状态失败: {e}")

    log.info(f"任务 {task_id} 轮询结束")


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str, request: Request, user=Depends(get_verified_user)
):
    """获取任务状态"""
    try:
        # 从数据库查找任务
        stored_task = JimengTasks.get_task_by_id(task_id)
        if not stored_task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 检查用户权限
        if stored_task.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问此任务")

        # 如果任务还在处理中，查询即梦API获取最新状态
        if stored_task.status not in [TaskStatus.SUCCESS, TaskStatus.FAILURE]:
            api_url = JIMENG_API_URL.value
            api_key = JIMENG_API_KEY.value

            if api_url and api_key:
                try:
                    # 查询即梦API获取最新状态
                    status_url = f"{api_url}/jimeng/fetch/{task_id}"

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(
                            status_url,
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                            },
                        )

                        if response.is_success:
                            api_result = response.json()

                            if (
                                api_result.get("code") == "success"
                                and "data" in api_result
                            ):
                                task_data = api_result["data"]
                                new_status = task_data.get("status")

                                # 更新数据库中的任务状态
                                log.info(
                                    f"手动查询API响应详细数据 - task_id: {task_id}"
                                )
                                log.info(
                                    f"API响应原始数据: {json.dumps(api_result, ensure_ascii=False, indent=2)}"
                                )
                                log.info(
                                    f"task_data内容: {json.dumps(task_data, ensure_ascii=False, indent=2)}"
                                )

                                update_data = {"status": new_status}

                                # 如果任务失败，记录失败原因
                                if new_status == TaskStatus.FAILURE:
                                    update_data["fail_reason"] = task_data.get(
                                        "fail_reason", "未知错误"
                                    )

                                # 如果任务成功，提取视频信息（尝试多种可能的数据结构）
                                if new_status == TaskStatus.SUCCESS:
                                    video_url = None
                                    video_id = None

                                    # 尝试不同的数据结构路径
                                    if task_data.get("data") and task_data["data"].get(
                                        "data"
                                    ):
                                        # 原来的路径：task_data.data.data.video
                                        video_info = task_data["data"]["data"]
                                        if video_info.get("video"):
                                            video_url = video_info["video"]
                                            video_id = task_data.get("task_id")
                                            log.info(
                                                f"从路径 data.data.video 提取到视频URL: {video_url}"
                                            )

                                    # 尝试直接从task_data.data获取
                                    elif task_data.get("data") and task_data[
                                        "data"
                                    ].get("video"):
                                        video_url = task_data["data"]["video"]
                                        video_id = task_data.get("task_id")
                                        log.info(
                                            f"从路径 data.video 提取到视频URL: {video_url}"
                                        )

                                    # 尝试直接从task_data获取
                                    elif task_data.get("video"):
                                        video_url = task_data["video"]
                                        video_id = task_data.get("task_id")
                                        log.info(
                                            f"从路径 video 提取到视频URL: {video_url}"
                                        )

                                    # 尝试从video_url字段获取
                                    elif task_data.get("video_url"):
                                        video_url = task_data["video_url"]
                                        video_id = task_data.get("task_id")
                                        log.info(
                                            f"从路径 video_url 提取到视频URL: {video_url}"
                                        )

                                    if video_url:
                                        update_data.update(
                                            {
                                                "video_url": video_url,
                                                "video_id": video_id,
                                                "finish_time": task_data.get(
                                                    "finish_time"
                                                ),
                                            }
                                        )
                                        log.info(
                                            f"成功提取视频信息 - URL: {video_url}, ID: {video_id}"
                                        )
                                    else:
                                        log.warning(
                                            f"任务 {task_id} 已成功但无法提取视频URL，task_data结构: {list(task_data.keys())}"
                                        )

                                # 更新数据库
                                updated_task = JimengTasks.update_task_by_id(
                                    task_id, update_data
                                )
                                if updated_task:
                                    stored_task = updated_task

                except Exception as e:
                    log.error(f"查询即梦API状态异常: {e}")

        return {
            "task_id": task_id,
            "status": stored_task.status,
            "created_at": stored_task.created_at,
            "updated_at": stored_task.updated_at,
            "video_url": stored_task.video_url,
            "video_id": stored_task.video_id,
            "fail_reason": stored_task.fail_reason or "",
            "message": f"任务状态: {stored_task.status}",
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取任务状态失败")


@router.get("/tasks")
async def get_user_tasks(request: Request, user=Depends(get_verified_user)):
    """获取用户任务列表"""
    try:
        log.info(f"获取用户 {user.id} 的即梦任务列表")

        # 从数据库获取用户的任务
        tasks = JimengTasks.get_tasks_by_user_id(user.id)

        user_tasks = []
        for task in tasks:
            user_tasks.append(
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "prompt": task.prompt or "",
                    "image_url": task.image_url,
                    "duration": task.duration,
                    "aspect_ratio": task.aspect_ratio,
                    "cfg_scale": task.cfg_scale,
                    "credits_used": task.credits_used,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "video_url": task.video_url,
                    "video_id": task.video_id,
                    "fail_reason": task.fail_reason or "",
                }
            )

        return user_tasks

    except Exception as e:
        log.error(f"获取用户任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.delete("/task/{task_id}")
async def delete_task(task_id: str, request: Request, user=Depends(get_verified_user)):
    """删除任务"""
    try:
        # 从数据库查找任务
        stored_task = JimengTasks.get_task_by_id(task_id)
        if not stored_task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 检查用户权限
        if stored_task.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权删除此任务")

        # 从数据库删除任务
        success = JimengTasks.delete_task_by_id(task_id)
        if success:
            return {"message": "任务已删除", "task_id": task_id}
        else:
            raise HTTPException(status_code=500, detail="删除任务失败")

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail="删除任务失败")


@router.get("/credits")
async def get_user_credits(user=Depends(get_verified_user)):
    """获取用户积分"""
    try:
        user_credit = Credits.get_credit_by_user_id(user.id)
        if not user_credit:
            user_credit = Credits.init_credit_by_user_id(user.id)

        return {
            "user_id": user.id,
            "credits": float(user_credit.credit) if user_credit else 0,
        }
    except Exception as e:
        log.error(f"获取用户积分失败: {e}")
        raise HTTPException(status_code=500, detail="获取积分失败")
