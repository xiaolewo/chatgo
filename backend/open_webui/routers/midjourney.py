"""
MidJourney API Integration Router
提供MidJourney图像生成API的集成接口
"""

import asyncio
import uuid
import random
import time
from datetime import datetime
from typing import Dict, Optional, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
import httpx
import logging

from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.midjourney_tasks import MidJourneyTasks, MidJourneyTaskForm
from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail
from decimal import Decimal

log = logging.getLogger(__name__)

router = APIRouter()

# 任务状态管理已迁移到数据库 (models/midjourney_tasks.py)


class MidJourneyConfig(BaseModel):
    """MidJourney配置模型"""

    enabled: bool = False
    api_url: str = ""  # 基础URL，例如: https://api.example.com
    api_key: str = ""
    fast_credits: int = 10
    relax_credits: int = 5


class ReferenceImage(BaseModel):
    """参考图片模型"""

    base64: str = Field(..., description="Base64编码的图片数据")
    weight: Optional[float] = Field(
        1.0, ge=0.1, le=3.0, description="图片权重 (0.1-3.0)"
    )
    type: str = Field(
        "reference", description="图片类型: reference(普通参考图) 或 style(风格参考图)"
    )


class AdvancedParameters(BaseModel):
    """高级参数模型"""

    chaos: Optional[int] = Field(None, ge=0, le=100, description="混乱程度 (0-100)")
    stylize: Optional[int] = Field(
        None, ge=0, le=1000, description="风格化程度 (0-1000)"
    )
    seed: Optional[int] = Field(
        None, ge=0, le=4294967295, description="种子值 (0-4294967295)"
    )
    version: Optional[str] = Field(
        None, description="MidJourney版本 (v5.2, v6, v6.1, v7)"
    )
    tile: Optional[bool] = Field(False, description="平铺模式")
    quality: Optional[float] = Field(
        1.0, ge=0.25, le=2.0, description="图像质量 (0.25-2.0)"
    )
    weird: Optional[int] = Field(None, ge=0, le=3000, description="奇异程度 (0-3000)")

    @validator("version")
    def validate_version(cls, v):
        if v is not None:
            valid_versions = ["5.2", "6", "6.1", "7", "niji 5", "niji 6"]
            if v not in valid_versions:
                raise ValueError(f'版本必须是以下之一: {", ".join(valid_versions)}')
        return v


class ImageGenerateRequest(BaseModel):
    """图像生成请求模型"""

    prompt: str = Field(..., min_length=3, max_length=2000, description="图像描述")
    mode: str = Field("fast", description="生成模式: fast 或 relax")
    aspect_ratio: Optional[str] = Field("1:1", description="宽高比")
    negative_prompt: Optional[str] = Field(
        None, max_length=1000, description="负面提示词"
    )
    reference_images: Optional[List[ReferenceImage]] = Field(
        [], description="参考图片列表"
    )
    advanced_params: Optional[AdvancedParameters] = Field(None, description="高级参数")

    @validator("mode")
    def validate_mode(cls, v):
        if v not in ["fast", "relax", "turbo"]:
            raise ValueError("生成模式必须是 fast, relax 或 turbo")
        return v

    @validator("reference_images")
    def validate_reference_images(cls, v):
        if v and len(v) > 5:
            raise ValueError("最多只能上传5张参考图片")
        return v


class TaskResponse(BaseModel):
    """任务响应模型"""

    task_id: str
    status: str
    message: str
    credits_used: int


class ActionButton(BaseModel):
    """任务操作按钮模型"""

    label: str = Field(..., description="按钮标签 (如 U1, U2, V1, V2)")
    custom_id: str = Field(..., description="按钮自定义ID")
    type: str = Field(..., description="按钮类型: upscale, variation, reroll")
    emoji: Optional[str] = Field(None, description="按钮表情符号")


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""

    task_id: str
    status: str
    progress: Optional[int] = None
    image_url: Optional[str] = None
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    actions: Optional[List[ActionButton]] = Field([], description="可用操作按钮")
    seed: Optional[int] = Field(None, description="生成使用的种子值")
    final_prompt: Optional[str] = Field(None, description="最终使用的提示词")


@router.get("/config")
async def get_midjourney_config(request: Request, user=Depends(get_admin_user)):
    """获取MidJourney配置"""
    return {
        "enabled": getattr(request.app.state.config, "MIDJOURNEY_ENABLED", False),
        "api_url": getattr(request.app.state.config, "MIDJOURNEY_API_URL", ""),
        "api_key": getattr(request.app.state.config, "MIDJOURNEY_API_KEY", ""),
        "fast_credits": getattr(
            request.app.state.config, "MIDJOURNEY_FAST_CREDITS", 10
        ),
        "relax_credits": getattr(
            request.app.state.config, "MIDJOURNEY_RELAX_CREDITS", 5
        ),
        "turbo_credits": getattr(
            request.app.state.config, "MIDJOURNEY_TURBO_CREDITS", 15
        ),
    }


@router.get("/credits")
async def get_user_credits(user=Depends(get_verified_user)):
    """获取用户v豆余额"""
    try:
        user_credit = Credits.get_credit_by_user_id(user.id)
        if not user_credit:
            # 如果用户没有积分记录，初始化一个
            user_credit = Credits.init_credit_by_user_id(user.id)

        return {
            "user_id": user.id,
            "credits": float(user_credit.credit),
            "credit_display": f"{user_credit.credit:.2f}",
        }
    except Exception as e:
        log.error(f"获取用户积分失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户积分失败")


@router.post("/config")
async def update_midjourney_config(
    request: Request, config: MidJourneyConfig, user=Depends(get_admin_user)
):
    """更新MidJourney配置"""
    # 保存到持久化配置
    request.app.state.config.MIDJOURNEY_ENABLED = config.enabled
    request.app.state.config.MIDJOURNEY_API_URL = config.api_url
    request.app.state.config.MIDJOURNEY_API_KEY = config.api_key
    request.app.state.config.MIDJOURNEY_FAST_CREDITS = config.fast_credits
    request.app.state.config.MIDJOURNEY_RELAX_CREDITS = config.relax_credits
    request.app.state.config.MIDJOURNEY_TURBO_CREDITS = getattr(
        config, "turbo_credits", 15
    )

    log.info(f"MidJourney配置已更新并持久化: enabled={config.enabled}")
    return {"message": "配置更新成功", "config": config}


@router.post("/generate", response_model=TaskResponse)
async def generate_image(
    req: Request, request: ImageGenerateRequest, user=Depends(get_verified_user)
):
    """提交图像生成任务"""
    try:
        # 从持久化配置获取MidJourney配置
        config_enabled = getattr(req.app.state.config, "MIDJOURNEY_ENABLED", False)
        config_api_url = getattr(req.app.state.config, "MIDJOURNEY_API_URL", "")
        config_api_key = getattr(req.app.state.config, "MIDJOURNEY_API_KEY", "")
        config_fast_credits = getattr(
            req.app.state.config, "MIDJOURNEY_FAST_CREDITS", 10
        )
        config_relax_credits = getattr(
            req.app.state.config, "MIDJOURNEY_RELAX_CREDITS", 5
        )
        config_turbo_credits = getattr(
            req.app.state.config, "MIDJOURNEY_TURBO_CREDITS", 15
        )

        # 验证服务状态
        if not config_enabled:
            raise HTTPException(
                status_code=503, detail="MidJourney服务未启用，请联系管理员开启服务"
            )

        if not config_api_url or not config_api_key:
            raise HTTPException(
                status_code=503,
                detail="MidJourney服务配置不完整，请联系管理员配置API信息",
            )

        # 验证请求参数
        if not request.prompt or len(request.prompt.strip()) < 3:
            raise HTTPException(status_code=400, detail="图像描述至少需要3个字符")

        if len(request.prompt) > 2000:
            raise HTTPException(status_code=400, detail="图像描述不能超过2000个字符")

        if request.mode not in ["fast", "relax", "turbo"]:
            raise HTTPException(
                status_code=400, detail="生成模式必须是 'fast'、'relax' 或 'turbo'"
            )

        # 计算所需积分
        if request.mode == "fast":
            credits_needed = config_fast_credits
        elif request.mode == "relax":
            credits_needed = config_relax_credits
        elif request.mode == "turbo":
            credits_needed = config_turbo_credits
        else:
            credits_needed = config_fast_credits  # 默认

        if credits_needed <= 0:
            raise HTTPException(status_code=500, detail="积分配置错误，请联系管理员")

        # 检查用户真实v豆余额
        try:
            user_credit = Credits.get_credit_by_user_id(user.id)
            if not user_credit:
                # 如果用户没有积分记录，初始化一个
                user_credit = Credits.init_credit_by_user_id(user.id)
        except Exception as e:
            log.error(f"获取用户积分失败: {str(e)}")
            raise HTTPException(status_code=400, detail="获取用户积分失败，请稍后重试")

        current_balance = float(user_credit.credit)
        if current_balance < credits_needed:
            raise HTTPException(
                status_code=400,
                detail=f"v豆余额不足，需要{credits_needed}v豆，当前余额：{current_balance:.2f}v豆",
            )

        # 扣除v豆
        try:
            deduct_form = AddCreditForm(
                user_id=user.id,
                amount=Decimal(-credits_needed),
                detail=SetCreditFormDetail(
                    desc=f"MidJourney图像生成-{request.mode}模式",
                    api_path="/midjourney/generate",
                    api_params={
                        "mode": request.mode,
                        "prompt": request.prompt[:50] + "...",
                    },
                    usage={"credits_used": credits_needed, "mode": request.mode},
                ),
            )
            Credits.add_credit_by_user_id(deduct_form)
            log.info(f"用户 {user.id} 消耗了 {credits_needed} v豆用于MidJourney任务")
        except Exception as e:
            log.error(f"扣除用户积分失败: {str(e)}")
            raise HTTPException(status_code=500, detail="扣除积分失败，请稍后重试")

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 构建完整的提示词 - 安全地处理参数
        final_prompt = request.prompt.strip()

        # 添加高级参数到提示词
        if request.advanced_params:
            params = request.advanced_params
            if params.chaos is not None and params.chaos != "":
                try:
                    chaos_val = int(params.chaos)
                    if 0 <= chaos_val <= 100:
                        final_prompt += f" --chaos {chaos_val}"
                except (ValueError, TypeError):
                    log.warning(f"无效的chaos值: {params.chaos}")

            if params.stylize is not None and params.stylize != "":
                try:
                    stylize_val = int(params.stylize)
                    if 0 <= stylize_val <= 1000:
                        final_prompt += f" --stylize {stylize_val}"
                except (ValueError, TypeError):
                    log.warning(f"无效的stylize值: {params.stylize}")

            if params.seed is not None and params.seed != "":
                try:
                    seed_val = int(params.seed)
                    if 0 <= seed_val <= 4294967295:
                        final_prompt += f" --seed {seed_val}"
                except (ValueError, TypeError):
                    log.warning(f"无效的seed值: {params.seed}")

            if params.version and params.version.strip():
                version_str = params.version.strip()
                if version_str.startswith("niji"):
                    # Niji版本格式: --niji 5 或 --niji 6
                    final_prompt += f" --{version_str}"
                else:
                    # MidJourney版本格式: --v 6.1
                    final_prompt += f" --v {version_str}"

            if params.tile:
                final_prompt += " --tile"

            if params.quality is not None:
                try:
                    quality_val = float(params.quality)
                    if 0.25 <= quality_val <= 2.0:
                        # 总是添加质量参数，包括默认的1.0
                        final_prompt += f" --q {quality_val}"
                except (ValueError, TypeError):
                    log.warning(f"无效的quality值: {params.quality}")

            if params.weird is not None and params.weird != "":
                try:
                    weird_val = int(params.weird)
                    if 0 <= weird_val <= 3000:
                        final_prompt += f" --weird {weird_val}"
                except (ValueError, TypeError):
                    log.warning(f"无效的weird值: {params.weird}")

        # 添加宽高比 - 总是添加，包括默认的1:1
        if request.aspect_ratio:
            final_prompt += f" --ar {request.aspect_ratio}"

        # 处理参考图片权重参数
        if request.reference_images:
            reference_weights = []
            style_refs = []

            for ref_img in request.reference_images:
                if isinstance(ref_img, dict):
                    ref_type = ref_img.get("type", "reference")
                    weight = ref_img.get("weight", 1.0)

                    if ref_type == "style":
                        style_refs.append(str(weight))
                    else:
                        reference_weights.append(str(weight))

            # 添加普通参考图权重 --iw
            if reference_weights:
                avg_weight = sum(float(w) for w in reference_weights) / len(
                    reference_weights
                )
                if avg_weight != 1.0:
                    final_prompt += f" --iw {avg_weight:.1f}"

            # 添加风格参考图权重 --sref (注意：风格参考图的URL会在base64Array中传递)
            if style_refs:
                avg_style_weight = sum(float(w) for w in style_refs) / len(style_refs)
                if avg_style_weight != 1.0:
                    final_prompt += f" --sw {avg_style_weight:.1f}"

        # 创建任务记录并保存到数据库
        task_form = MidJourneyTaskForm(
            task_id=task_id,
            user_id=user.id,
            prompt=request.prompt.strip(),
            final_prompt=final_prompt,
            mode=request.mode,
            aspect_ratio=request.aspect_ratio or "1:1",
            negative_prompt=(
                request.negative_prompt.strip() if request.negative_prompt else None
            ),
            reference_images=[img.dict() for img in (request.reference_images or [])],
            advanced_params=(
                request.advanced_params.dict() if request.advanced_params else None
            ),
            status="submitted",
            progress=0,
            message="任务已提交，等待处理",
            credits_used=credits_needed,
            seed=request.advanced_params.seed if request.advanced_params else None,
        )

        # 保存到数据库
        saved_task = MidJourneyTasks.insert_new_task(task_form)
        if not saved_task:
            raise HTTPException(status_code=500, detail="任务创建失败，请稍后重试")

        log.info(
            f"新的MidJourney任务已创建: {task_id}, 用户: {user.id}, 模式: {request.mode}"
        )

        # 启动异步任务处理，传递当前配置
        asyncio.create_task(
            process_midjourney_task(task_id, config_api_url, config_api_key)
        )

        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message="任务已提交成功",
            credits_used=credits_needed,
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        log.error(f"提交MidJourney任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, user=Depends(get_verified_user)):
    """获取任务状态"""
    task = MidJourneyTasks.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证用户权限
    if task.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此任务")

    # 转换为旧版格式确保兼容性
    task_info = MidJourneyTasks.convert_to_legacy_format(task)
    return TaskStatusResponse(**task_info)


@router.get("/tasks")
async def list_user_tasks(user=Depends(get_verified_user)):
    """获取用户的任务列表"""
    if user.role == "admin":
        # 管理员可以看到所有任务
        tasks = MidJourneyTasks.get_all_tasks(limit=100)
    else:
        # 普通用户只能看到自己的任务
        tasks = MidJourneyTasks.get_tasks_by_user_id(user.id, limit=50)

    # 转换为旧版格式确保兼容性
    user_tasks = [MidJourneyTasks.convert_to_legacy_format(task) for task in tasks]

    return {"tasks": user_tasks}


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str, user=Depends(get_verified_user)):
    """取消任务"""
    task = MidJourneyTasks.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证用户权限
    if task.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此任务")

    # 只能取消未完成的任务
    if task.status in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="任务已完成，无法取消")

    # 取消任务，退还v豆（仅当任务未完成时）
    if task.status not in ["completed"] and task.credits_used > 0:
        try:
            refund_form = AddCreditForm(
                user_id=user.id,
                amount=Decimal(task.credits_used),
                detail=SetCreditFormDetail(
                    desc=f"MidJourney任务取消退款-{task.mode}模式",
                    api_path="/midjourney/task/cancel",
                    api_params={"task_id": task_id},
                    usage={
                        "credits_refunded": task.credits_used,
                        "reason": "task_cancelled",
                    },
                ),
            )
            Credits.add_credit_by_user_id(refund_form)
            log.info(f"任务取消，已退还 {task.credits_used} v豆给用户 {user.id}")
        except Exception as refund_error:
            log.error(f"退还v豆失败: {str(refund_error)}")

    # 更新任务状态
    update_data = {
        "status": "cancelled",
        "message": "任务已取消",
        "completed_at": int(time.time()),
    }

    updated_task = MidJourneyTasks.update_task_by_id(task_id, update_data)
    if not updated_task:
        raise HTTPException(status_code=500, detail="任务取消失败")

    log.info(f"任务已取消: {task_id}")

    return {"message": "任务已取消"}


@router.get("/debug/task/{task_id}")
async def debug_task(task_id: str, user=Depends(get_verified_user)):
    """调试：获取任务的详细信息"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    task = MidJourneyTasks.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取一些统计信息（仅供调试）
    all_tasks = MidJourneyTasks.get_all_tasks(limit=10)
    task_ids = [t.task_id for t in all_tasks]

    return {
        "task_info": MidJourneyTasks.convert_to_legacy_format(task),
        "config": "debug_config_unavailable",
        "recent_task_ids": task_ids,
        "storage_type": "database_persistent",
    }


async def process_midjourney_task(
    task_id: str, config_api_url: str = None, config_api_key: str = None
):
    """处理MidJourney任务的异步函数"""
    task = MidJourneyTasks.get_task_by_id(task_id)

    if not task:
        log.error(f"任务不存在: {task_id}")
        return

    # 为了保持代码兼容性，将数据库任务转换为字典格式
    task_info = MidJourneyTasks.convert_to_legacy_format(task)

    # 定义更新任务状态的辅助函数
    def update_task_status(**updates):
        try:
            MidJourneyTasks.update_task_by_id(task_id, updates)
            # 同时更新本地task_info以保持兼容性
            task_info.update(updates)
        except Exception as e:
            log.error(f"更新任务状态失败 {task_id}: {e}")

    try:
        log.info(f"开始处理MidJourney任务: {task_id}")

        # 验证任务状态
        if task_info["status"] != "submitted":
            log.warning(f"任务状态异常: {task_id}, 当前状态: {task_info['status']}")
            return

        # 阶段1: 提交到MidJourney API
        update_task_status(
            status="processing", message="正在提交到MidJourney服务", progress=10
        )

        log.info(f"开始处理任务: {task_id}, prompt: {task_info['prompt'][:50]}...")

        # 构建API请求
        request_data = {
            "prompt": task_info["final_prompt"],
            "mode": task_info["mode"],
            "reference_images": task_info.get("reference_images", []),
            "advanced_params": task_info.get("advanced_params"),
        }

        # 调用真实的MidJourney API
        api_response = await call_midjourney_api(
            config_api_url, config_api_key, request_data
        )

        if not api_response["success"]:
            raise Exception(f"API调用失败: {api_response.get('error', '未知错误')}")

        # 获取MidJourney任务ID
        mj_task_id = api_response["task_id"]

        update_task_status(
            mj_task_id=mj_task_id, message="任务已提交，正在生成图像", progress=20
        )

        log.info(f"MidJourney任务已提交: {mj_task_id}")

        # 阶段2: 轮询任务状态
        max_polls = 60  # 最多轮询60次 (5分钟)
        poll_interval = 5  # 5秒间隔
        poll_count = 0

        while poll_count < max_polls:
            await asyncio.sleep(poll_interval)
            poll_count += 1

            # 查询任务状态 - 使用传递的配置参数
            status_response = await fetch_midjourney_task(
                config_api_url, config_api_key, mj_task_id, task_info["mode"]
            )

            if status_response.get("status") == "FAILURE":
                error_msg = status_response.get("failReason", "任务执行失败")
                raise Exception(f"MidJourney任务失败: {error_msg}")

            # 更新进度
            progress_str = status_response.get("progress", "0%")
            try:
                progress_num = int(progress_str.replace("%", ""))
                # 映射MidJourney进度到我们的进度 (20-95)
                mapped_progress = 20 + int(progress_num * 0.75)
                current_progress = min(mapped_progress, 95)
            except:
                # 如果无法解析进度，使用默认进度更新
                current_progress = min(20 + poll_count * 2, 90)

            update_task_status(
                progress=current_progress,
                message=f"MidJourney正在生成图像 ({progress_str})",
            )

            log.info(
                f"任务进度更新: {task_id} - {task_info['progress']}% - {task_info['message']}"
            )

            # 处理不同的任务状态
            mj_status = status_response.get("status")

            if mj_status == "SUCCESS":
                # 解析动作按钮
                buttons = status_response.get("buttons", [])
                actions = []
                for button in buttons:
                    button_label = button.get("label", "")
                    button_emoji = button.get("emoji", "")

                    # 确定动作类型
                    if button_label and button_label.startswith("U"):
                        action_type = "upscale"
                        display_label = button_label
                    elif button_label and button_label.startswith("V"):
                        action_type = "variation"
                        display_label = button_label
                    elif button_emoji == "🔄":
                        action_type = "reroll"
                        display_label = "重新生成"
                    else:
                        action_type = "unknown"
                        display_label = button_label or button_emoji or "未知"

                    actions.append(
                        {
                            "label": display_label,
                            "custom_id": button.get("customId", ""),
                            "type": action_type,
                            "emoji": button_emoji,
                        }
                    )

                # 提取种子值（如果存在）
                properties = status_response.get("properties", {})
                final_prompt = properties.get("finalPrompt", "")
                seed_value = task_info.get("seed")  # 获取原有的种子值

                if "--seed" in final_prompt:
                    try:
                        seed_match = final_prompt.split("--seed")[1].split()[0]
                        seed_value = int(seed_match)
                    except:
                        if not seed_value:
                            seed_value = random.randint(0, 4294967295)
                elif not seed_value:
                    seed_value = random.randint(0, 4294967295)

                # 更新任务为完成状态
                update_task_status(
                    status="completed",
                    message="图像生成完成",
                    progress=100,
                    image_url=status_response.get("imageUrl"),
                    completed_at=int(time.time()),
                    actions=actions,
                    seed=seed_value,
                    final_prompt=(
                        final_prompt if final_prompt else task_info.get("final_prompt")
                    ),
                )

                log.info(f"MidJourney任务成功完成: {task_id}")
                break

            elif mj_status in ["NOT_START", "SUBMITTED"]:
                # 任务等待中
                current_progress = max(task_info.get("progress", 0), 5)
                update_task_status(
                    message="任务已提交，等待处理", progress=current_progress
                )

            elif mj_status == "IN_PROGRESS":
                # 任务处理中，继续轮询
                pass  # 进度已在上面更新

            elif mj_status == "MODAL":
                # 需要用户确认（一般不会出现在imagine任务中）
                update_task_status(message="等待确认")

            elif mj_status == "CANCEL":
                # 任务被取消
                update_task_status(
                    status="cancelled",
                    message="任务已取消",
                    completed_at=int(time.time()),
                )
                break

        else:
            # 轮询超时
            raise Exception("任务处理超时，请稍后重试")

    except asyncio.CancelledError:
        # 任务被取消，退还v豆
        try:
            refund_form = AddCreditForm(
                user_id=task_info["user_id"],
                amount=Decimal(task_info.get("credits_used", 0)),
                detail=SetCreditFormDetail(
                    desc=f"MidJourney任务取消退款-{task_info.get('mode', 'unknown')}模式",
                    api_path="/midjourney/process",
                    api_params={"task_id": task_id, "cancel_reason": "task_cancelled"},
                    usage={
                        "credits_refunded": task_info.get("credits_used", 0),
                        "reason": "task_cancelled",
                    },
                ),
            )
            Credits.add_credit_by_user_id(refund_form)
            log.info(
                f"任务取消，已退还 {task_info.get('credits_used', 0)} v豆给用户 {task_info['user_id']}"
            )
        except Exception as refund_error:
            log.error(f"退还v豆失败: {str(refund_error)}")

        log.info(f"MidJourney任务被取消: {task_id}")
        update_task_status(
            status="cancelled", message="任务已取消", completed_at=int(time.time())
        )

    except Exception as e:
        log.error(f"MidJourney任务处理失败: {task_id}")
        log.error(f"错误详情: {str(e)}")

        # 根据错误类型设置不同的错误消息
        error_str = str(e).lower()
        if "验证失败" in error_str or "validation" in error_str:
            error_message = f"参数验证失败: {str(e)}"
        elif "network" in error_str or "connection" in error_str:
            error_message = "网络连接失败，请稍后重试"
        elif "timeout" in error_str:
            error_message = "请求超时，请稍后重试"
        elif "配置" in error_str:
            error_message = "服务配置错误，请联系管理员"
        else:
            # 显示详细错误信息用于调试
            error_message = f"生成失败: {str(e)}"

        # 任务失败，退还v豆
        try:
            refund_form = AddCreditForm(
                user_id=task_info["user_id"],
                amount=Decimal(task_info.get("credits_used", 0)),
                detail=SetCreditFormDetail(
                    desc=f"MidJourney任务失败退款-{task_info.get('mode', 'unknown')}模式",
                    api_path="/midjourney/generate",
                    api_params={"task_id": task_id, "refund_reason": "task_failed"},
                    usage={
                        "credits_refunded": task_info.get("credits_used", 0),
                        "reason": "task_failed",
                    },
                ),
            )
            Credits.add_credit_by_user_id(refund_form)
            log.info(
                f"任务失败，已退还 {task_info.get('credits_used', 0)} v豆给用户 {task_info['user_id']}"
            )
        except Exception as refund_error:
            log.error(f"退还v豆失败: {str(refund_error)}")

        # 设置失败状态
        update_task_status(
            status="failed",
            error_message=str(e),
            message=error_message,
            completed_at=int(time.time()),
        )


# 新增：执行MidJourney动作的路由
class ActionRequest(BaseModel):
    """动作执行请求模型"""

    action_type: str = Field(..., description="动作类型: upscale, variation, reroll")
    button_index: Optional[int] = Field(
        None, description="按钮索引 (0-3 for U1-U4/V1-V4)"
    )
    custom_id: str = Field(..., description="按钮自定义ID")


@router.post("/action/{task_id}", response_model=TaskResponse)
async def execute_action(
    req: Request, task_id: str, request: ActionRequest, user=Depends(get_verified_user)
):
    """执行MidJourney动作 (U1-U4, V1-V4, Reroll)"""
    original_task_model = MidJourneyTasks.get_task_by_id(task_id)
    if not original_task_model:
        raise HTTPException(status_code=404, detail="原始任务不存在")

    # 转换为字典格式保持兼容性
    original_task = MidJourneyTasks.convert_to_legacy_format(original_task_model)

    # 验证用户权限
    if original_task["user_id"] != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此任务")

    # 验证原始任务状态
    if original_task["status"] != "completed":
        raise HTTPException(status_code=400, detail="只能对已完成的任务执行动作")

    # 检查用户v豆余额并扣除动作操作所需积分
    action_credits_needed = 5  # 动作操作通常消耗较少积分

    try:
        user_credit = Credits.get_credit_by_user_id(user.id)
        if not user_credit:
            user_credit = Credits.init_credit_by_user_id(user.id)
    except Exception as e:
        log.error(f"获取用户积分失败: {str(e)}")
        raise HTTPException(status_code=400, detail="获取用户积分失败，请稍后重试")

    current_balance = float(user_credit.credit)
    if current_balance < action_credits_needed:
        raise HTTPException(
            status_code=400,
            detail=f"v豆余额不足，执行{request.action_type}操作需要{action_credits_needed}v豆，当前余额：{current_balance:.2f}v豆",
        )

    # 扣除v豆
    try:
        deduct_form = AddCreditForm(
            user_id=user.id,
            amount=Decimal(-action_credits_needed),
            detail=SetCreditFormDetail(
                desc=f"MidJourney动作操作-{request.action_type}",
                api_path="/midjourney/action",
                api_params={
                    "action_type": request.action_type,
                    "parent_task_id": task_id,
                },
                usage={
                    "credits_used": action_credits_needed,
                    "action_type": request.action_type,
                },
            ),
        )
        Credits.add_credit_by_user_id(deduct_form)
        log.info(
            f"用户 {user.id} 消耗了 {action_credits_needed} v豆用于MidJourney动作操作"
        )
    except Exception as e:
        log.error(f"扣除用户积分失败: {str(e)}")
        raise HTTPException(status_code=500, detail="扣除积分失败，请稍后重试")

    # 生成新任务ID
    new_task_id = str(uuid.uuid4())

    # 创建新动作任务记录
    action_task_form = MidJourneyTaskForm(
        task_id=new_task_id,
        user_id=user.id,
        parent_task_id=task_id,
        action_type=request.action_type,
        button_index=request.button_index,
        custom_id=request.custom_id,
        prompt=original_task["prompt"],
        final_prompt=original_task["final_prompt"],
        mode=original_task["mode"],
        status="submitted",
        progress=0,
        message=f"正在执行{request.action_type}操作",
        credits_used=action_credits_needed,
        seed=original_task.get("seed"),
    )

    # 保存到数据库
    saved_action_task = MidJourneyTasks.insert_new_task(action_task_form)
    if not saved_action_task:
        raise HTTPException(status_code=500, detail="动作任务创建失败，请稍后重试")

    # 获取当前MidJourney配置
    config_api_url = getattr(req.app.state.config, "MIDJOURNEY_API_URL", "")
    config_api_key = getattr(req.app.state.config, "MIDJOURNEY_API_KEY", "")

    # 启动异步处理，传递当前配置
    asyncio.create_task(
        process_action_task(new_task_id, config_api_url, config_api_key)
    )

    log.info(
        f"新的MidJourney动作任务已创建: {new_task_id}, 类型: {request.action_type}"
    )

    return TaskResponse(
        task_id=new_task_id,
        status="submitted",
        message=f"{request.action_type}操作已提交",
        credits_used=5,
    )


async def process_action_task(
    task_id: str, config_api_url: str = None, config_api_key: str = None
):
    """处理MidJourney动作任务"""
    task = MidJourneyTasks.get_task_by_id(task_id)

    if not task:
        log.error(f"动作任务不存在: {task_id}")
        return

    # 转换为字典格式保持兼容性
    task_info = MidJourneyTasks.convert_to_legacy_format(task)

    # 定义更新任务状态的辅助函数
    def update_action_task_status(**updates):
        try:
            MidJourneyTasks.update_task_by_id(task_id, updates)
            # 同时更新本地task_info以保持兼容性
            task_info.update(updates)
        except Exception as e:
            log.error(f"更新动作任务状态失败 {task_id}: {e}")

    try:
        log.info(f"开始处理MidJourney动作任务: {task_id}")

        update_action_task_status(
            status="processing", progress=10, message="正在提交动作请求"
        )

        # 获取原始任务的MidJourney任务ID
        parent_task_id = task_info.get("parent_task_id")
        parent_task_model = (
            MidJourneyTasks.get_task_by_id(parent_task_id) if parent_task_id else None
        )
        parent_task = (
            MidJourneyTasks.convert_to_legacy_format(parent_task_model)
            if parent_task_model
            else None
        )

        if not parent_task or not parent_task.get("mj_task_id"):
            raise Exception("找不到原始任务的MidJourney ID")

        original_mj_task_id = parent_task["mj_task_id"]
        custom_id = task_info.get("custom_id")

        # 使用传递的API配置
        current_api_url = config_api_url
        current_api_key = config_api_key

        action_response = await call_midjourney_action_api(
            current_api_url,
            current_api_key,
            custom_id,
            original_mj_task_id,
            parent_task.get("mode", "fast"),
        )

        if not action_response["success"]:
            raise Exception(
                f"动作API调用失败: {action_response.get('error', '未知错误')}"
            )

        # 获取新的MidJourney任务ID
        new_mj_task_id = action_response["task_id"]

        update_action_task_status(
            mj_task_id=new_mj_task_id, message="动作已提交，正在处理", progress=20
        )

        log.info(f"MidJourney动作任务已提交: {new_mj_task_id}")

        # 轮询动作任务状态
        max_polls = 60  # 最多轮询60次 (5分钟)
        poll_interval = 5  # 5秒间隔
        poll_count = 0

        while poll_count < max_polls:
            await asyncio.sleep(poll_interval)
            poll_count += 1

            # 使用传递的API配置
            current_api_url = config_api_url
            current_api_key = config_api_key

            status_response = await fetch_midjourney_task(
                current_api_url,
                current_api_key,
                new_mj_task_id,
                parent_task.get("mode", "fast"),
            )

            if status_response.get("status") == "FAILURE":
                error_msg = status_response.get("failReason", "动作执行失败")
                raise Exception(f"MidJourney动作失败: {error_msg}")

            # 更新进度
            progress_str = status_response.get("progress", "0%")
            try:
                progress_num = int(progress_str.replace("%", ""))
                mapped_progress = 20 + int(progress_num * 0.75)
                current_progress = min(mapped_progress, 95)
            except:
                current_progress = min(20 + poll_count * 2, 90)

            update_action_task_status(
                progress=current_progress, message=f"动作执行中 ({progress_str})"
            )

            log.info(f"动作任务进度更新: {task_id} - {task_info['progress']}%")

            # 检查是否完成
            if status_response.get("status") == "SUCCESS":
                # 解析动作按钮
                buttons = status_response.get("buttons", [])
                actions = []
                for button in buttons:
                    button_label = button.get("label", "")
                    button_emoji = button.get("emoji", "")

                    # 确定动作类型
                    if button_label and button_label.startswith("U"):
                        action_type = "upscale"
                        display_label = button_label
                    elif button_label and button_label.startswith("V"):
                        action_type = "variation"
                        display_label = button_label
                    elif button_emoji == "🔄":
                        action_type = "reroll"
                        display_label = "重新生成"
                    else:
                        action_type = "unknown"
                        display_label = button_label or button_emoji or "未知"

                    actions.append(
                        {
                            "label": display_label,
                            "custom_id": button.get("customId", ""),
                            "type": action_type,
                            "emoji": button_emoji,
                        }
                    )

                # 动作完成，更新任务状态
                update_action_task_status(
                    status="completed",
                    progress=100,
                    message="动作执行完成",
                    image_url=status_response.get("imageUrl"),
                    completed_at=int(time.time()),
                    actions=actions,
                )

                log.info(f"MidJourney动作任务完成: {task_id}")
                break

        else:
            # 轮询超时
            raise Exception("动作处理超时，请稍后重试")

    except Exception as e:
        log.error(f"MidJourney动作任务失败: {task_id}, 错误: {str(e)}")

        # 动作任务失败，退还v豆
        try:
            refund_form = AddCreditForm(
                user_id=task_info["user_id"],
                amount=Decimal(task_info.get("credits_used", 0)),
                detail=SetCreditFormDetail(
                    desc=f"MidJourney动作失败退款-{task_info.get('action_type', 'unknown')}",
                    api_path="/midjourney/action",
                    api_params={"task_id": task_id, "refund_reason": "action_failed"},
                    usage={
                        "credits_refunded": task_info.get("credits_used", 0),
                        "reason": "action_failed",
                    },
                ),
            )
            Credits.add_credit_by_user_id(refund_form)
            log.info(
                f"动作任务失败，已退还 {task_info.get('credits_used', 0)} v豆给用户 {task_info['user_id']}"
            )
        except Exception as refund_error:
            log.error(f"退还v豆失败: {str(refund_error)}")

        update_action_task_status(
            status="failed",
            message=f"动作执行失败: {str(e)}",
            completed_at=int(time.time()),
        )


async def call_midjourney_api(
    api_url: str, api_key: str, request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """调用真实的MidJourney API"""

    async with httpx.AsyncClient() as client:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # 构建API请求负载 (按照文档格式)
            prompt = request_data.get("prompt", "")
            mode = request_data.get("mode", "fast")

            # 根据模式使用正确的API端点路径 - 按照文档格式
            mode_path_map = {
                "fast": "fast",
                "relax": "relax",
                "turbo": "fast",  # turbo模式使用fast端点
            }
            mode_path = mode_path_map.get(mode, "fast")
            submit_url = f"{api_url}/{mode_path}/mj/submit/imagine"

            # 使用LinkAPI文档指定的标准参数格式
            # Turbo模式的处理：
            # 1. 使用fast端点（因为大多数API没有独立的turbo端点）
            # 2. 在prompt中添加--turbo参数（在MidJourney中这是启用turbo模式的标准方式）
            final_prompt = prompt
            if mode == "turbo":
                # 检查prompt中是否已经包含--turbo参数
                if "--turbo" not in final_prompt.lower():
                    final_prompt += " --turbo"
                log.info(f"Turbo模式检测，已在prompt中添加--turbo参数")

            payload = {"prompt": final_prompt, "base64Array": []}

            # 添加参考图片 (按照文档的base64Array格式)
            reference_images = request_data.get("reference_images", [])
            if reference_images:
                for ref_img in reference_images:
                    # 前端发送的是字典对象，包含base64字段
                    if isinstance(ref_img, dict):
                        base64_data = ref_img.get("base64", "")
                        if base64_data:
                            # 确保有正确的data URL前缀
                            if not base64_data.startswith("data:"):
                                base64_data = f"data:image/jpeg;base64,{base64_data}"
                            payload["base64Array"].append(base64_data)
                            log.info(
                                f"添加参考图片: {ref_img.get('filename', '未知文件名')}, 类型: {ref_img.get('type', 'unknown')}"
                            )
                    else:
                        log.warning(f"参考图片格式不正确: {type(ref_img)}")

            log.info(f"调用MidJourney API: {submit_url} (模式: {mode})")
            log.info(
                f"请求负载: prompt长度={len(payload['prompt'])}, 参考图数量={len(payload['base64Array'])}"
            )
            if mode == "turbo":
                log.info(f"Turbo模式 - 最终prompt片段: {payload['prompt'][-50:]}")

            # 实际API调用
            response = await client.post(
                submit_url, json=payload, headers=headers, timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(
                    f"API调用失败: {response.status_code} - {response.text}"
                )

            result = response.json()
            if result.get("code") != 1:
                error_desc = result.get("description", "未知错误")
                # 优化特定错误信息的显示
                if error_desc == "quota_not_enough":
                    raise Exception("API配额不足，请检查账户余额并充值")
                elif error_desc == "parameter error":
                    raise Exception("API参数错误，请检查配置")
                else:
                    raise Exception(f"任务提交失败: {error_desc}")

            return {
                "success": True,
                "task_id": result["result"],
                "status": "submitted",
                "code": result.get("code"),
                "description": result.get("description", "提交成功"),
                "result": result["result"],
            }

        except Exception as e:
            log.error(f"MidJourney API调用失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "code": -1,
                "description": str(e),
            }


async def call_midjourney_action_api(
    api_url: str, api_key: str, custom_id: str, task_id: str, mode: str = "fast"
) -> Dict[str, Any]:
    """调用MidJourney动作API"""

    async with httpx.AsyncClient() as client:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # 根据模式使用正确的动作API端点路径 - 按照文档格式
            mode_path_map = {
                "fast": "fast",
                "relax": "relax",
                "turbo": "fast",  # turbo模式使用fast端点 + --turbo参数
            }
            mode_path = mode_path_map.get(mode, "fast")
            action_url = f"{api_url}/{mode_path}/mj/submit/action"

            # 按照文档格式构建请求
            payload = {"customId": custom_id, "taskId": task_id}

            log.info(f"调用MidJourney动作API: {action_url}")
            log.info(f"动作请求: customId={custom_id}, taskId={task_id}")

            # 实际API调用
            response = await client.post(
                action_url, json=payload, headers=headers, timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(
                    f"动作API调用失败: {response.status_code} - {response.text}"
                )

            result = response.json()
            if result.get("code") != 1:
                raise Exception(
                    f"动作提交失败: {result.get('description', '未知错误')}"
                )

            return {
                "success": True,
                "task_id": result["result"],
                "status": "submitted",
                "code": result.get("code"),
                "description": result.get("description", "动作提交成功"),
                "result": result["result"],
            }

        except Exception as e:
            log.error(f"MidJourney动作API调用失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "code": -1,
                "description": str(e),
            }


async def fetch_midjourney_task(
    api_url: str, api_key: str, task_id: str, mode: str = "fast"
) -> Dict[str, Any]:
    """查询MidJourney任务状态"""

    async with httpx.AsyncClient() as client:
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # 任务查询使用fast端点路径（根据文档规范）
            fetch_url = f"{api_url}/fast/mj/task/{task_id}/fetch"

            log.info(f"查询MidJourney任务: {fetch_url}")

            # 实际API调用
            response = await client.get(fetch_url, headers=headers, timeout=30.0)

            if response.status_code != 200:
                raise Exception(
                    f"任务查询失败: {response.status_code} - {response.text}"
                )

            return response.json()

        except Exception as e:
            log.error(f"MidJourney任务查询失败: {str(e)}")
            return {"status": "FAILURE", "failReason": str(e)}
