"""
可灵 (Kling) 视频生成 API Integration Router
提供可灵文生视频API的集成接口
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
from open_webui.models.kling_tasks import (
    KlingTasks,
    KlingTaskForm,
    KlingTaskResponse,
    CameraControl,
)
from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail
from decimal import Decimal

log = logging.getLogger(__name__)

router = APIRouter()


# 任务状态常量
class TaskStatus:
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    SUCCEED = "succeed"
    FAILED = "failed"


class KlingConfig(BaseModel):
    """可灵配置模型"""

    enabled: bool = False
    api_url: str = ""  # Base URL，例如: https://api.example.com
    api_key: str = ""  # Bearer token
    std_credits: int = 5  # 标准模式积分消耗
    pro_credits: int = 10  # 专家模式积分消耗


class CameraControl(BaseModel):
    """摄像机控制"""

    type: Optional[str] = Field(None, description="运镜类型")
    config: Optional[dict] = Field(None, description="运镜配置")


class KlingGenerateRequest(BaseModel):
    """可灵视频生成请求模型"""

    model_name: Optional[str] = Field("kling-v1", description="模型名称")
    prompt: str = Field(
        ..., min_length=1, max_length=2500, description="正向文本提示词"
    )
    negative_prompt: Optional[str] = Field(
        None, max_length=2500, description="负向文本提示词"
    )
    cfg_scale: Optional[float] = Field(0.5, ge=0, le=1, description="生成视频的自由度")
    mode: Optional[str] = Field("std", description="生成模式：std或pro")
    camera_control: Optional[CameraControl] = Field(None, description="摄像机运动控制")
    aspect_ratio: Optional[str] = Field("16:9", description="画面纵横比")
    duration: Optional[str] = Field("5", description="视频时长")
    callback_url: Optional[str] = Field(None, description="回调地址")
    external_task_id: Optional[str] = Field(None, description="自定义任务ID")


####################
# 配置管理
####################


@router.get("/config")
async def get_kling_config(request: Request, user=Depends(get_admin_user)):
    """获取可灵配置"""
    try:
        return {
            "enabled": getattr(request.app.state.config, "KLING_ENABLED", False),
            "api_url": getattr(request.app.state.config, "KLING_API_URL", ""),
            "api_key": getattr(request.app.state.config, "KLING_API_KEY", ""),
            "std_credits": getattr(request.app.state.config, "KLING_STD_CREDITS", 5),
            "pro_credits": getattr(request.app.state.config, "KLING_PRO_CREDITS", 10),
        }
    except Exception as e:
        log.error(f"获取可灵配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@router.post("/config")
async def update_kling_config(
    request: Request, config: KlingConfig, user=Depends(get_admin_user)
):
    """更新可灵配置"""
    try:
        request.app.state.config.KLING_ENABLED = config.enabled
        request.app.state.config.KLING_API_URL = config.api_url
        request.app.state.config.KLING_API_KEY = config.api_key
        request.app.state.config.KLING_STD_CREDITS = config.std_credits
        request.app.state.config.KLING_PRO_CREDITS = config.pro_credits

        return {"message": "可灵配置已更新"}
    except Exception as e:
        log.error(f"更新可灵配置失败: {e}")
        raise HTTPException(status_code=500, detail="更新配置失败")


@router.post("/verify")
async def verify_kling_connection(request: Request, user=Depends(get_admin_user)):
    """验证可灵API连接"""
    try:
        api_url = getattr(request.app.state.config, "KLING_API_URL", "")
        api_key = getattr(request.app.state.config, "KLING_API_KEY", "")

        if not api_url or not api_key:
            raise HTTPException(status_code=400, detail="API URL和API Key不能为空")

        # 构建测试请求URL - 发送一个最小的POST请求来测试连接
        test_url = f"{api_url}/kling/v1/videos/text2video"

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
                    "model_name": "kling-v1",
                    "mode": "std",
                    "aspect_ratio": "16:9",
                    "duration": "5",
                },
            )

            log.info(f"可灵API测试响应: HTTP {response.status_code}")

            # 检查响应状态
            if response.status_code == 200:
                # 解析响应检查是否是有效的API响应
                try:
                    result = response.json()
                    log.info(f"可灵API测试响应内容: {result}")
                    if "code" in result and "data" in result:
                        if result["code"] == 0:
                            return {"message": "连接成功，API正常", "status": "success"}
                        else:
                            return {
                                "message": f"API错误: {result.get('message', '未知错误')}",
                                "status": "error",
                            }
                    else:
                        return {"message": "API响应格式异常", "status": "error"}
                except Exception as e:
                    log.error(f"解析API响应失败: {e}")
                    return {"message": "API响应解析失败", "status": "error"}
            elif response.status_code == 401 or response.status_code == 403:
                try:
                    error_detail = response.json()
                    error_msg = error_detail.get("message", "API Key无效或权限不足")
                except:
                    error_msg = "API Key无效或权限不足"
                return {
                    "message": f"{error_msg}: HTTP {response.status_code}",
                    "status": "error",
                }
            elif response.status_code == 400:
                try:
                    error_detail = response.json()
                    error_msg = error_detail.get("message", "请求参数错误")
                    log.warning(f"API参数错误，但连接正常: {error_msg}")
                    return {
                        "message": f"连接成功，但参数错误: {error_msg}",
                        "status": "warning",
                    }
                except:
                    return {"message": "连接成功，但请求格式有误", "status": "warning"}
            else:
                try:
                    error_detail = response.json()
                    error_msg = error_detail.get(
                        "message", f"HTTP {response.status_code}"
                    )
                except:
                    error_msg = f"HTTP {response.status_code}"
                return {"message": f"连接失败: {error_msg}", "status": "error"}

    except Exception as e:
        log.error(f"验证可灵连接失败: {e}")
        return {"message": f"连接失败: {str(e)}", "status": "error"}


####################
# 视频生成相关
####################


@router.post("/generate")
async def generate_video(
    request: Request,
    generate_request: KlingGenerateRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_verified_user),
):
    """生成视频"""
    try:
        log.info(f"收到视频生成请求 - 用户: {user.id}")
        log.info(
            f"请求参数: prompt长度={len(generate_request.prompt)}, negative_prompt长度={len(generate_request.negative_prompt) if generate_request.negative_prompt else 0}"
        )
        log.info(
            f"请求参数详情: model={generate_request.model_name}, mode={generate_request.mode}, aspect_ratio={generate_request.aspect_ratio}, duration={generate_request.duration}"
        )

        # 检查服务是否启用
        kling_enabled = getattr(request.app.state.config, "KLING_ENABLED", False)
        log.info(f"可灵服务启用状态: {kling_enabled}")

        if not kling_enabled:
            log.warning("可灵服务未启用")
            raise HTTPException(
                status_code=400,
                detail="可灵服务未启用，请先在管理员设置中启用并配置可灵服务",
            )

        # 检查API配置
        api_url = getattr(request.app.state.config, "KLING_API_URL", "")
        api_key = getattr(request.app.state.config, "KLING_API_KEY", "")

        log.info(
            f"可灵API配置 - URL: {api_url[:50] if api_url else 'None'}..., Key: {'已配置' if api_key else 'None'}"
        )

        if not api_url or not api_key:
            log.warning("可灵API配置不完整")
            raise HTTPException(
                status_code=400,
                detail="API配置不完整，请在管理员设置中配置可灵API URL和API Key",
            )

        # 计算积分消耗并提前检查
        credits_cost = (
            getattr(request.app.state.config, "KLING_PRO_CREDITS", 10)
            if generate_request.mode == "pro"
            else getattr(request.app.state.config, "KLING_STD_CREDITS", 5)
        )

        # 提前检查用户积分
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

        # 构建可灵API请求
        kling_api_url = f"{api_url}/kling/v1/videos/text2video"

        # 构建回调URL
        # 获取当前请求的host信息来构建回调URL
        host_url = str(request.base_url).rstrip("/")
        callback_url = f"{host_url}/api/v1/kling/callback"
        log.info(f"设置回调URL: {callback_url}")

        # 构建请求参数
        api_params = {
            "model_name": generate_request.model_name,
            "prompt": generate_request.prompt,
            "cfg_scale": generate_request.cfg_scale,
            "mode": generate_request.mode,
            "aspect_ratio": generate_request.aspect_ratio,
            "duration": generate_request.duration,
            "callback_url": callback_url,  # 添加回调URL
        }

        # 添加可选参数
        if generate_request.negative_prompt:
            api_params["negative_prompt"] = generate_request.negative_prompt
        if generate_request.camera_control:
            api_params["camera_control"] = generate_request.camera_control.dict(
                exclude_none=True
            )

        # 调用可灵API
        log.info(f"用户 {user.id} 发起视频生成请求，调用可灵API: {kling_api_url}")
        log.info(f"请求参数: {json.dumps(api_params, ensure_ascii=False, indent=2)}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                kling_api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=api_params,
            )

            log.info(f"可灵API响应状态: HTTP {response.status_code}")
            log.info(f"可灵API响应头: {dict(response.headers)}")

            if not response.is_success:
                error_detail = f"可灵API调用失败: HTTP {response.status_code}"
                try:
                    response_text = response.text
                    log.error(f"可灵API错误响应原文: {response_text}")
                    error_data = response.json()
                    log.error(f"可灵API错误响应解析: {error_data}")
                    if "message" in error_data:
                        error_detail = f"可灵API错误: {error_data['message']}"
                    elif "error" in error_data:
                        error_detail = f"可灵API错误: {error_data['error']}"
                except Exception as e:
                    log.error(f"解析错误响应失败: {e}")
                    error_detail = f"可灵API调用失败: HTTP {response.status_code} - {response.text[:200]}"

                log.error(f"可灵API调用失败: {error_detail}")
                raise HTTPException(status_code=400, detail=error_detail)

            # 解析API响应
            try:
                response_text = response.text
                log.info(f"可灵API响应原文: {response_text}")
                api_result = response.json()
                log.info(f"可灵API成功响应解析: {api_result}")
            except Exception as e:
                log.error(f"解析可灵API响应失败: {e}, 响应文本: {response.text[:500]}")
                raise HTTPException(status_code=500, detail="可灵API响应解析失败")

            # 检查API响应格式
            if "code" not in api_result or "data" not in api_result:
                log.error(f"可灵API响应格式错误: {api_result}")
                raise HTTPException(status_code=500, detail="可灵API响应格式错误")

            if api_result["code"] != 0:
                error_msg = api_result.get("message", "未知错误")
                log.error(
                    f"可灵API业务错误: code={api_result['code']}, message={error_msg}"
                )
                raise HTTPException(status_code=400, detail=f"可灵API错误: {error_msg}")

            # 提取任务信息
            task_data = api_result["data"]
            task_id = task_data["task_id"]
            task_status = task_data["task_status"]

            log.info(f"可灵API成功创建任务: task_id={task_id}, status={task_status}")

            # 扣除用户积分（积分已经在调用API前检查过了）
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
            task_form_data = {
                "prompt": generate_request.prompt,
                "negative_prompt": generate_request.negative_prompt,
                "model_name": generate_request.model_name,
                "mode": generate_request.mode,
                "aspect_ratio": generate_request.aspect_ratio,
                "duration": generate_request.duration,
                "cfg_scale": generate_request.cfg_scale,
                "camera_control": (
                    generate_request.camera_control.dict()
                    if generate_request.camera_control
                    else None
                ),
                "callback_url": generate_request.callback_url,
                "external_task_id": generate_request.external_task_id,
                "credits_used": credits_cost,
            }

            stored_task = KlingTasks.insert_new_task(task_form_data, user.id, task_id)
            if not stored_task:
                log.error(f"任务存储失败: {task_id}")
                # 不抛出异常，任务已经提交到可灵平台

            # 如果有视频数据，立即更新
            if task_data.get("videos") and len(task_data["videos"]) > 0:
                video = task_data["videos"][0]
                update_data = {
                    "status": task_status,
                    "video_id": video.get("id"),
                    "video_url": video.get("url"),
                    "video_duration": video.get("duration"),
                }
                KlingTasks.update_task_by_id(task_id, update_data)

            log.info(
                f"视频生成任务成功提交到可灵平台: user_id={user.id}, task_id={task_id}, status={task_status}"
            )

            return {
                "task_id": task_id,
                "status": task_status,
                "message": "视频生成任务已提交到可灵平台",
                "credits_used": credits_cost,
            }

    except HTTPException as he:
        log.error(f"HTTP异常: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        log.error(f"生成视频失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成视频失败: {str(e)}")


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str, request: Request, user=Depends(get_verified_user)
):
    """获取任务状态"""
    try:
        # 从数据库查找任务
        stored_task = KlingTasks.get_task_by_id(task_id)
        if not stored_task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 检查用户权限
        if stored_task.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问此任务")

        # 如果任务还在处理中，查询可灵API获取最新状态
        if stored_task.status in ["submitted", "processing"]:
            api_url = getattr(request.app.state.config, "KLING_API_URL", "")
            api_key = getattr(request.app.state.config, "KLING_API_KEY", "")

            log.info(f"检查任务 {task_id} 状态 - 当前状态: {stored_task.status}")
            log.info(
                f"API配置 - URL: {api_url[:50] if api_url else 'None'}..., Key: {'已配置' if api_key else 'None'}"
            )

            if api_url and api_key:
                try:
                    # 查询可灵API获取最新状态
                    status_url = f"{api_url}/kling/v1/videos/text2video/{task_id}"
                    log.info(f"查询外部API状态: {status_url}")

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(
                            status_url,
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                            },
                        )

                        log.info(f"外部API状态查询响应: HTTP {response.status_code}")
                        response_text = response.text
                        log.info(f"外部API状态响应原文: {response_text}")

                        if response.is_success:
                            api_result = response.json()
                            log.info(f"外部API状态响应解析: {api_result}")

                            if api_result.get("code") == 0 and "data" in api_result:
                                task_data = api_result["data"]
                                old_status = stored_task.status
                                new_status = task_data.get(
                                    "task_status", stored_task.status
                                )

                                log.info(f"任务状态更新: {old_status} -> {new_status}")

                                # 更新数据库中的任务状态
                                update_data = {
                                    "status": new_status,
                                    "task_status_msg": task_data.get(
                                        "task_status_msg", ""
                                    ),
                                }

                                # 如果任务完成，提取视频信息
                                if task_data.get("task_result"):
                                    task_result = task_data["task_result"]
                                    if (
                                        task_result.get("videos")
                                        and len(task_result["videos"]) > 0
                                    ):
                                        video = task_result["videos"][0]
                                        update_data.update(
                                            {
                                                "video_url": video.get("url"),
                                                "video_id": video.get("id"),
                                                "video_duration": video.get("duration"),
                                            }
                                        )

                                log.info(f"准备更新任务数据: {update_data}")

                                # 更新数据库
                                updated_task = KlingTasks.update_task_by_id(
                                    task_id, update_data
                                )
                                if updated_task:
                                    stored_task = updated_task

                                log.info(f"任务状态已更新: {stored_task.status}")
                            else:
                                log.warning(
                                    f"外部API响应格式异常: code={api_result.get('code')}, data存在={('data' in api_result)}"
                                )
                        else:
                            log.error(
                                f"外部API状态查询失败: HTTP {response.status_code} - {response_text}"
                            )

                except Exception as e:
                    log.error(f"查询可灵API状态异常: {e}")
                    import traceback

                    log.error(f"异常堆栈: {traceback.format_exc()}")
            else:
                log.warning("API配置不完整，无法查询外部状态")

        log.info(
            f"返回任务状态: task_id={task_id}, status={stored_task.status}, video_url={stored_task.video_url}"
        )

        return {
            "task_id": task_id,
            "status": stored_task.status,
            "created_at": stored_task.created_at,
            "updated_at": stored_task.updated_at,
            "video_url": stored_task.video_url,
            "video_id": stored_task.video_id,
            "video_duration": stored_task.video_duration,
            "task_status_msg": stored_task.task_status_msg or "",
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
        log.info(f"获取用户 {user.id} 的可灵任务列表")

        # 从数据库获取用户的任务
        tasks = KlingTasks.get_tasks_by_user_id(user.id)

        user_tasks = []
        for task in tasks:
            user_tasks.append(
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "prompt": task.prompt or "",
                    "negative_prompt": task.negative_prompt,
                    "model_name": task.model_name,
                    "mode": task.mode,
                    "aspect_ratio": task.aspect_ratio,
                    "duration": task.duration,
                    "cfg_scale": task.cfg_scale,
                    "credits_used": task.credits_used,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "video_url": task.video_url,
                    "video_id": task.video_id,
                    "video_duration": task.video_duration,
                    "task_status_msg": task.task_status_msg or "",
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
        stored_task = KlingTasks.get_task_by_id(task_id)
        if not stored_task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 检查用户权限
        if stored_task.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权删除此任务")

        # 从数据库删除任务
        success = KlingTasks.delete_task_by_id(task_id)
        if success:
            return {"message": "任务已删除", "task_id": task_id}
        else:
            raise HTTPException(status_code=500, detail="删除任务失败")

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail="删除任务失败")


@router.post("/callback")
async def kling_callback(request: Request):
    """可灵API任务完成回调通知接口"""
    try:
        # 获取回调数据
        callback_data = await request.json()
        log.info(
            f"收到可灵API回调通知: {json.dumps(callback_data, ensure_ascii=False, indent=2)}"
        )

        # 解析回调数据
        task_id = callback_data.get("task_id")
        task_status = callback_data.get("task_status")

        if not task_id:
            log.error("回调数据缺少task_id")
            return {"code": 1, "message": "缺少task_id"}

        # 查找对应的任务
        stored_task = KlingTasks.get_task_by_id(task_id)
        if stored_task:
            old_status = stored_task.status

            log.info(f"任务 {task_id} 状态更新: {old_status} -> {task_status}")

            # 更新任务状态
            update_data = {
                "status": task_status,
                "task_status_msg": callback_data.get("task_status_msg", ""),
            }

            # 如果任务完成，提取视频信息
            if task_status == "succeed" and callback_data.get("task_result"):
                task_result = callback_data["task_result"]
                if task_result.get("videos") and len(task_result["videos"]) > 0:
                    video = task_result["videos"][0]
                    update_data.update(
                        {
                            "video_url": video.get("url"),
                            "video_id": video.get("id"),
                            "video_duration": video.get("duration"),
                        }
                    )
                    log.info(f"任务 {task_id} 完成，视频URL: {video.get('url')}")

            # 更新数据库中的任务
            updated_task = KlingTasks.update_task_by_id(task_id, update_data)
            if updated_task:
                log.info(f"任务 {task_id} 状态已通过回调更新: {updated_task.status}")
            else:
                log.error(f"任务 {task_id} 状态更新失败")

            return {"code": 0, "message": "回调处理成功"}
        else:
            log.warning(f"回调通知的任务ID {task_id} 不存在")
            return {"code": 1, "message": f"任务 {task_id} 不存在"}

    except Exception as e:
        log.error(f"处理可灵API回调通知失败: {e}")
        import traceback

        log.error(f"回调处理异常堆栈: {traceback.format_exc()}")
        return {"code": 1, "message": f"处理回调失败: {str(e)}"}


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


# 后台任务处理功能暂时禁用
