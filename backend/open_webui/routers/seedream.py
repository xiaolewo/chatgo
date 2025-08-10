"""
即梦3.0 (Seedream 3.0) API Integration Router
提供即梦3.0图像生成API的集成接口
"""

import uuid
import time
from datetime import datetime
from typing import Dict, Optional, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
import httpx
import logging

from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.seedream_tasks import SeedreamTasks, SeedreamTaskForm
from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail
from decimal import Decimal

log = logging.getLogger(__name__)

router = APIRouter()


class SeedreamConfig(BaseModel):
    """即梦3.0配置模型"""

    enabled: bool = False
    api_url: str = ""  # 平台Base_URL，例如: https://api.example.com
    api_key: str = ""  # Bearer token
    credits_per_generation: int = 1  # 每次生成消耗的积分，默认1积分=0.2元


class LogoInfo(BaseModel):
    """水印信息模型"""

    add_logo: Optional[bool] = Field(False, description="是否添加水印")
    position: Optional[int] = Field(
        0, ge=0, le=3, description="水印位置：0-右下角,1-左下角,2-左上角,3-右上角"
    )
    language: Optional[int] = Field(
        0, ge=0, le=1, description="水印语言：0-中文,1-英文"
    )
    opacity: Optional[float] = Field(0.3, ge=0.0, le=1.0, description="水印不透明度")
    logo_text_content: Optional[str] = Field(None, description="明水印自定义内容")


class SeedreamGenerateRequest(BaseModel):
    """即梦3.0图像生成请求模型"""

    prompt: str = Field(
        ..., min_length=3, max_length=2000, description="图像描述提示词"
    )
    use_pre_llm: Optional[bool] = Field(False, description="开启文本扩写")
    seed: Optional[int] = Field(-1, description="随机种子，-1为随机")
    scale: Optional[float] = Field(
        2.5, ge=1.0, le=10.0, description="影响文本描述的程度"
    )
    width: Optional[int] = Field(1328, ge=512, le=2048, description="生成图像的宽度")
    height: Optional[int] = Field(1328, ge=512, le=2048, description="生成图像的高度")
    return_url: Optional[bool] = Field(True, description="返回图片链接")
    logo_info: Optional[LogoInfo] = Field(None, description="水印信息")

    @validator("prompt")
    def validate_prompt(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError("图像描述至少需要3个字符")
        if len(v) > 2000:
            raise ValueError("图像描述不能超过2000个字符")
        return v.strip()

    @validator("width", "height")
    def validate_dimensions(cls, v):
        if v < 512 or v > 2048:
            raise ValueError("图像尺寸必须在512-2048之间")
        return v


class SeedreamResponse(BaseModel):
    """即梦3.0响应模型"""

    task_id: str
    status: str
    message: str
    credits_used: int
    image_url: Optional[str] = None
    image_data: Optional[str] = None  # Base64图像数据


@router.get("/config")
async def get_seedream_config(request: Request, user=Depends(get_admin_user)):
    """获取即梦3.0配置"""
    return {
        "enabled": getattr(request.app.state.config, "SEEDREAM_ENABLED", False),
        "api_url": getattr(request.app.state.config, "SEEDREAM_API_URL", ""),
        "api_key": getattr(request.app.state.config, "SEEDREAM_API_KEY", ""),
        "credits_per_generation": getattr(
            request.app.state.config, "SEEDREAM_CREDITS", 1
        ),
    }


@router.post("/config")
async def update_seedream_config(
    request: Request, config: SeedreamConfig, user=Depends(get_admin_user)
):
    """更新即梦3.0配置"""
    # 保存到持久化配置
    request.app.state.config.SEEDREAM_ENABLED = config.enabled
    request.app.state.config.SEEDREAM_API_URL = config.api_url
    request.app.state.config.SEEDREAM_API_KEY = config.api_key
    request.app.state.config.SEEDREAM_CREDITS = config.credits_per_generation

    log.info(f"即梦3.0配置已更新并持久化: enabled={config.enabled}")
    return {"message": "配置更新成功", "config": config}


@router.post("/verify")
async def verify_seedream_connection(request: Request, user=Depends(get_admin_user)):
    """验证即梦3.0连接"""
    try:
        # 获取配置
        config_api_url = getattr(request.app.state.config, "SEEDREAM_API_URL", "")
        config_api_key = getattr(request.app.state.config, "SEEDREAM_API_KEY", "")

        if not config_api_url or not config_api_key:
            raise HTTPException(status_code=400, detail="请先配置API URL和API Key")

        # 测试连接（使用简单的测试prompt）
        test_response = await call_seedream_api(
            config_api_url,
            config_api_key,
            {
                "prompt": "test connection",
                "width": 512,
                "height": 512,
                "return_url": True,
            },
        )

        if test_response["success"]:
            return {"message": "连接验证成功", "status": "success"}
        else:
            return {
                "message": f"连接验证失败: {test_response['error']}",
                "status": "failed",
            }

    except Exception as e:
        log.error(f"连接验证失败: {str(e)}")
        return {"message": f"连接验证失败: {str(e)}", "status": "failed"}


@router.get("/credits")
async def get_user_credits(user=Depends(get_verified_user)):
    """获取用户v豆余额"""
    try:
        user_credit = Credits.get_credit_by_user_id(user.id)
        if not user_credit:
            user_credit = Credits.init_credit_by_user_id(user.id)

        return {
            "user_id": user.id,
            "credits": float(user_credit.credit),
            "credit_display": f"{user_credit.credit:.2f}",
        }
    except Exception as e:
        log.error(f"获取用户积分失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户积分失败")


@router.post("/generate", response_model=SeedreamResponse)
async def generate_image(
    req: Request, request: SeedreamGenerateRequest, user=Depends(get_verified_user)
):
    """生成图像（同步接口）"""
    try:
        # 获取配置
        config_enabled = getattr(req.app.state.config, "SEEDREAM_ENABLED", False)
        config_api_url = getattr(req.app.state.config, "SEEDREAM_API_URL", "")
        config_api_key = getattr(req.app.state.config, "SEEDREAM_API_KEY", "")
        config_credits = getattr(req.app.state.config, "SEEDREAM_CREDITS", 1)

        # 验证服务状态
        if not config_enabled:
            raise HTTPException(
                status_code=503, detail="即梦3.0服务未启用，请联系管理员开启服务"
            )

        if not config_api_url or not config_api_key:
            raise HTTPException(
                status_code=503, detail="即梦3.0服务配置不完整，请联系管理员配置API信息"
            )

        # 检查用户积分
        try:
            user_credit = Credits.get_credit_by_user_id(user.id)
            if not user_credit:
                user_credit = Credits.init_credit_by_user_id(user.id)
        except Exception as e:
            log.error(f"获取用户积分失败: {str(e)}")
            raise HTTPException(status_code=400, detail="获取用户积分失败，请稍后重试")

        current_balance = float(user_credit.credit)
        if current_balance < config_credits:
            raise HTTPException(
                status_code=400,
                detail=f"v豆余额不足，需要{config_credits}v豆，当前余额：{current_balance:.2f}v豆",
            )

        # 扣除积分
        try:
            deduct_form = AddCreditForm(
                user_id=user.id,
                amount=Decimal(-config_credits),
                detail=SetCreditFormDetail(
                    desc="即梦3.0图像生成",
                    api_path="/seedream/generate",
                    api_params={"prompt": request.prompt[:50] + "..."},
                    usage={"credits_used": config_credits, "service": "seedream"},
                ),
            )
            Credits.add_credit_by_user_id(deduct_form)
            log.info(f"用户 {user.id} 消耗了 {config_credits} v豆用于即梦3.0任务")
        except Exception as e:
            log.error(f"扣除用户积分失败: {str(e)}")
            raise HTTPException(status_code=500, detail="扣除积分失败，请稍后重试")

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 创建任务记录
        task_form = SeedreamTaskForm(
            task_id=task_id,
            user_id=user.id,
            prompt=request.prompt,
            use_pre_llm=request.use_pre_llm,
            seed=request.seed,
            scale=request.scale,
            width=request.width,
            height=request.height,
            return_url=request.return_url,
            logo_info=request.logo_info.dict() if request.logo_info else None,
            status="processing",
            message="正在生成图像",
            credits_used=config_credits,
        )

        # 保存到数据库
        saved_task = SeedreamTasks.insert_new_task(task_form)
        if not saved_task:
            # 如果任务创建失败，退还积分
            try:
                refund_form = AddCreditForm(
                    user_id=user.id,
                    amount=Decimal(config_credits),
                    detail=SetCreditFormDetail(
                        desc="即梦3.0任务创建失败退款",
                        api_path="/seedream/generate",
                        api_params={"task_id": task_id},
                        usage={
                            "credits_refunded": config_credits,
                            "reason": "task_creation_failed",
                        },
                    ),
                )
                Credits.add_credit_by_user_id(refund_form)
            except Exception as refund_error:
                log.error(f"退还积分失败: {str(refund_error)}")

            raise HTTPException(status_code=500, detail="任务创建失败，请稍后重试")

        log.info(f"新的即梦3.0任务已创建: {task_id}, 用户: {user.id}")

        # 调用即梦3.0 API（同步调用）
        try:
            api_response = await call_seedream_api(
                config_api_url, config_api_key, request.dict()
            )

            if api_response["success"]:
                # 更新任务为成功状态
                update_data = {
                    "status": "completed",
                    "message": "图像生成完成",
                    "image_url": api_response.get("image_url"),
                    "image_data": api_response.get("image_data"),
                    "completed_at": int(time.time()),
                }
                SeedreamTasks.update_task_by_id(task_id, update_data)

                log.info(f"即梦3.0任务成功完成: {task_id}")

                return SeedreamResponse(
                    task_id=task_id,
                    status="completed",
                    message="图像生成完成",
                    credits_used=config_credits,
                    image_url=api_response.get("image_url"),
                    image_data=api_response.get("image_data"),
                )
            else:
                # API调用失败，退还积分
                try:
                    refund_form = AddCreditForm(
                        user_id=user.id,
                        amount=Decimal(config_credits),
                        detail=SetCreditFormDetail(
                            desc="即梦3.0生成失败退款",
                            api_path="/seedream/generate",
                            api_params={"task_id": task_id},
                            usage={
                                "credits_refunded": config_credits,
                                "reason": "generation_failed",
                            },
                        ),
                    )
                    Credits.add_credit_by_user_id(refund_form)
                    log.info(f"生成失败，已退还 {config_credits} v豆给用户 {user.id}")
                except Exception as refund_error:
                    log.error(f"退还积分失败: {str(refund_error)}")

                # 更新任务为失败状态
                update_data = {
                    "status": "failed",
                    "message": f"生成失败: {api_response['error']}",
                    "completed_at": int(time.time()),
                }
                SeedreamTasks.update_task_by_id(task_id, update_data)

                raise HTTPException(
                    status_code=500, detail=f"图像生成失败: {api_response['error']}"
                )

        except Exception as e:
            # 异常处理，退还积分
            try:
                refund_form = AddCreditForm(
                    user_id=user.id,
                    amount=Decimal(config_credits),
                    detail=SetCreditFormDetail(
                        desc="即梦3.0异常退款",
                        api_path="/seedream/generate",
                        api_params={"task_id": task_id},
                        usage={
                            "credits_refunded": config_credits,
                            "reason": "exception",
                        },
                    ),
                )
                Credits.add_credit_by_user_id(refund_form)
                log.info(f"生成异常，已退还 {config_credits} v豆给用户 {user.id}")
            except Exception as refund_error:
                log.error(f"退还积分失败: {str(refund_error)}")

            # 更新任务为失败状态
            update_data = {
                "status": "failed",
                "message": f"生成异常: {str(e)}",
                "completed_at": int(time.time()),
            }
            SeedreamTasks.update_task_by_id(task_id, update_data)

            raise HTTPException(status_code=500, detail=f"图像生成异常: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"即梦3.0图像生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/task/{task_id}")
async def get_task_status(task_id: str, user=Depends(get_verified_user)):
    """获取任务状态"""
    task = SeedreamTasks.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证用户权限
    if task.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此任务")

    # 转换为响应格式
    task_info = SeedreamTasks.convert_to_response_format(task)
    return task_info


@router.get("/tasks")
async def list_user_tasks(user=Depends(get_verified_user)):
    """获取用户的任务列表"""
    if user.role == "admin":
        tasks = SeedreamTasks.get_all_tasks(limit=100)
    else:
        tasks = SeedreamTasks.get_tasks_by_user_id(user.id, limit=50)

    user_tasks = [SeedreamTasks.convert_to_response_format(task) for task in tasks]
    return {"tasks": user_tasks}


@router.delete("/task/{task_id}")
async def delete_task(task_id: str, user=Depends(get_verified_user)):
    """删除任务记录"""
    task = SeedreamTasks.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证用户权限
    if task.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问此任务")

    # 删除任务
    deleted = SeedreamTasks.delete_task_by_id(task_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="删除任务失败")

    log.info(f"任务已删除: {task_id}")
    return {"message": "任务已删除"}


async def call_seedream_api(
    api_url: str, api_key: str, request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """调用即梦3.0 API"""

    async with httpx.AsyncClient() as client:
        try:
            # 构建请求头
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # 构建API URL（按照文档要求替换）
            full_url = f"{api_url}/volcv/v1?Action=CVProcess&Version=2022-08-31"

            # 构建请求负载
            payload = {
                "req_key": "high_aes_general_v30l_zt2i",  # 固定值
                "prompt": request_data.get("prompt", ""),
                "use_pre_llm": request_data.get("use_pre_llm", False),
                "seed": request_data.get("seed", -1),
                "scale": request_data.get("scale", 2.5),
                "width": request_data.get("width", 1328),
                "height": request_data.get("height", 1328),
                "return_url": request_data.get("return_url", True),
            }

            # 添加水印信息（如果存在）
            if request_data.get("logo_info"):
                payload["logo_info"] = request_data["logo_info"]

            log.info(f"调用即梦3.0 API: {full_url}")
            log.info(
                f"请求负载: prompt长度={len(payload['prompt'])}, 尺寸={payload['width']}x{payload['height']}"
            )

            # 发送请求
            response = await client.post(
                full_url,
                json=payload,
                headers=headers,
                timeout=60.0,  # 即梦3.0是同步接口，可能需要较长时间
            )

            if response.status_code != 200:
                raise Exception(
                    f"API调用失败: {response.status_code} - {response.text}"
                )

            result = response.json()

            # 检查响应状态
            if result.get("code") != 10000:
                error_msg = result.get("message", "未知错误")
                log.error(f"即梦3.0 API返回错误: {error_msg}")
                raise Exception(f"API返回错误: {error_msg}")

            # 解析响应数据
            data = result.get("data", {})
            image_urls = data.get("image_urls", [])
            binary_data_base64 = data.get("binary_data_base64", [])

            response_data = {
                "success": True,
                "message": "生成成功",
                "request_id": result.get("request_id"),
                "time_elapsed": result.get("time_elapsed"),
            }

            # 优先使用图片URL
            if image_urls:
                response_data["image_url"] = image_urls[0]

            # 如果有Base64数据也返回
            if binary_data_base64:
                response_data["image_data"] = binary_data_base64[0]

            return response_data

        except Exception as e:
            log.error(f"即梦3.0 API调用失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"API调用失败: {str(e)}",
            }
