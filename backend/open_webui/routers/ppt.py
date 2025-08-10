"""
PPT 生成 API Integration Router
提供PPT生成API的集成接口，基于即梦PPT开放API
"""

import uuid
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any, List
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Request,
    BackgroundTasks,
    File,
    UploadFile,
    Form,
)
from fastapi.responses import Response
from pydantic import BaseModel, Field, validator, ValidationError
import httpx
import logging

from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.models.credits import Credits, AddCreditForm, SetCreditFormDetail
from open_webui.models.ppt_config import PptConfigs, PptConfigModel
from decimal import Decimal

log = logging.getLogger(__name__)

router = APIRouter()

# 配置默认值
DEFAULT_PPT_API_URL = "https://open.docmee.cn"
DEFAULT_PPT_CREDITS = 10


def get_current_ppt_config() -> PptConfigModel:
    """获取当前PPT配置"""
    return PptConfigs.get_or_create_config()


class PptTaskRequest(BaseModel):
    """PPT生成任务请求模型"""

    type: int = Field(
        ...,
        description="生成类型：1-智能生成，2-文件生成，3-思维导图，4-Word转换，5-网页生成，6-文本生成，7-Markdown",
    )
    content: Optional[str] = Field(None, description="内容：根据type不同有不同含义")
    template_id: str = Field(..., description="模板ID")
    language: str = Field("zh", description="语言")
    scene: Optional[str] = Field(None, description="演示场景")
    audience: Optional[str] = Field(None, description="目标受众")
    length: str = Field("medium", description="篇幅长度：short/medium/long")


class TemplateFilter(BaseModel):
    """模板筛选条件"""

    type: int = Field(1, description="模板类型：1-系统模板，4-用户模板")
    category: Optional[str] = Field(None, description="类目筛选")
    style: Optional[str] = Field(None, description="风格筛选")
    theme_color: Optional[str] = Field(None, description="主题颜色筛选")


class PptResponse(BaseModel):
    """PPT响应模型"""

    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/config")
async def get_ppt_config(user=Depends(get_admin_user)):
    """获取PPT配置 (仅管理员)"""
    try:
        config = PptConfigs.get_or_create_config()
        return config.model_dump()
    except Exception as e:
        log.error(f"获取PPT配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/config")
async def update_ppt_config(config: PptConfigModel, user=Depends(get_admin_user)):
    """更新PPT配置 (仅管理员)"""
    try:
        updated_config = PptConfigs.update_config(
            config.model_dump(exclude={"id", "created_at", "updated_at"})
        )
        if updated_config:
            log.info(f"PPT配置已更新: enabled={updated_config.enabled}")
            return {"success": True, "message": "配置已更新"}
        else:
            raise HTTPException(status_code=500, detail="配置更新失败")
    except Exception as e:
        log.error(f"更新PPT配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get("/template/options")
async def get_template_options(user=Depends(get_verified_user)):
    """获取模板筛选选项"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.api_url}/api/ppt/template/options",
                headers={"Api-Key": config.api_key},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code, detail="获取模板选项失败"
                )

    except httpx.RequestError as e:
        log.error(f"获取模板选项网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except Exception as e:
        log.error(f"获取模板选项失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板选项失败: {str(e)}")


class TemplateRequest(BaseModel):
    """模板查询请求模型"""

    page: int = Field(1, description="页码")
    size: int = Field(10, description="页大小")
    filters: TemplateFilter = Field(default_factory=TemplateFilter)


@router.post("/templates")
async def get_templates(request: TemplateRequest, user=Depends(get_verified_user)):
    """分页查询PPT模板"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        request_data = {
            "page": request.page,
            "size": request.size,
            "filters": request.filters.dict(),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.api_url}/api/ppt/templates",
                json=request_data,
                headers={"Content-Type": "application/json", "Api-Key": config.api_key},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code, detail="获取模板失败"
                )

    except httpx.RequestError as e:
        log.error(f"获取模板网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except Exception as e:
        log.error(f"获取模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")


@router.post("/v2/createTask")
async def create_ppt_task(
    type: int = Form(...),
    content: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    user=Depends(get_verified_user),
):
    """创建PPT生成任务"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        # 检查用户积分
        user_credits = Credits.get_credit_by_user_id(user.id)
        if user_credits is None:
            user_credits = Credits.init_credit_by_user_id(user.id)

        # 检查余额是否充足
        current_balance = float(user_credits.credit)
        credits_needed = config.credits_per_ppt
        if current_balance < credits_needed:
            raise HTTPException(
                status_code=402,
                detail=f"v豆余额不足，生成PPT需要{credits_needed}v豆，当前余额：{current_balance:.2f}v豆",
            )

        # 扣除v豆 (使用系统标准扣费逻辑)
        try:
            deduct_form = AddCreditForm(
                user_id=user.id,
                amount=Decimal(-credits_needed),
                detail=SetCreditFormDetail(
                    desc="PPT生成",
                    api_path="/api/v1/ppt/v2/createTask",
                    api_params={"type": type, "content": content or ""},
                    usage={"credits_per_ppt": credits_needed},
                ),
            )
            Credits.add_credit_by_user_id(deduct_form)
            log.info(f"用户 {user.email} 创建PPT任务，扣除 {credits_needed} v豆")
        except Exception as e:
            log.error(f"扣除用户积分失败: {str(e)}")
            raise HTTPException(status_code=500, detail="扣除积分失败，请稍后重试")

        # 准备请求数据
        form_data = {"type": type}

        if content:
            form_data["content"] = content

        # 处理文件上传
        files_data = []
        for file in files:
            files_data.append(
                ("file", (file.filename, await file.read(), file.content_type))
            )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{config.api_url}/api/ppt/v2/createTask",
                    data=form_data,
                    files=files_data,
                    headers={"Api-Key": config.api_key},
                )

                if response.status_code == 200:
                    result = response.json()
                    return result
                else:
                    # PPT API调用失败，需要退费
                    refund_form = AddCreditForm(
                        user_id=user.id,
                        amount=Decimal(credits_needed),
                        detail=SetCreditFormDetail(
                            desc="PPT生成失败退费",
                            api_path="/api/v1/ppt/v2/createTask",
                            api_params={"type": type, "content": content or ""},
                            usage={"refund_credits": credits_needed},
                        ),
                    )
                    Credits.add_credit_by_user_id(refund_form)
                    log.info(
                        f"PPT生成失败，为用户 {user.email} 退费 {credits_needed} v豆"
                    )
                    raise HTTPException(
                        status_code=response.status_code, detail="创建任务失败"
                    )

        except httpx.RequestError as e:
            # 网络错误，退费
            refund_form = AddCreditForm(
                user_id=user.id,
                amount=Decimal(credits_needed),
                detail=SetCreditFormDetail(
                    desc="PPT生成网络错误退费",
                    api_path="/api/v1/ppt/v2/createTask",
                    api_params={"type": type, "content": content or ""},
                    usage={"refund_credits": credits_needed},
                ),
            )
            Credits.add_credit_by_user_id(refund_form)
            log.info(f"PPT生成网络错误，为用户 {user.email} 退费 {credits_needed} v豆")
            raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")

        except Exception as e:
            # 其他错误，退费
            refund_form = AddCreditForm(
                user_id=user.id,
                amount=Decimal(credits_needed),
                detail=SetCreditFormDetail(
                    desc="PPT生成异常退费",
                    api_path="/api/v1/ppt/v2/createTask",
                    api_params={"type": type, "content": content or ""},
                    usage={"refund_credits": credits_needed},
                ),
            )
            Credits.add_credit_by_user_id(refund_form)
            log.info(f"PPT生成异常，为用户 {user.email} 退费 {credits_needed} v豆")
            raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"创建PPT任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/v2/options")
async def get_generation_options(user=Depends(get_verified_user)):
    """获取生成选项"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.api_url}/api/ppt/v2/options",
                headers={"Api-Key": config.api_key},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code, detail="获取生成选项失败"
                )

    except httpx.RequestError as e:
        log.error(f"获取生成选项网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except Exception as e:
        log.error(f"获取生成选项失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取生成选项失败: {str(e)}")


class GenerateContentRequest(BaseModel):
    """生成内容请求模型"""

    id: str = Field(..., description="任务ID")
    stream: bool = Field(True, description="是否流式")
    length: str = Field("medium", description="篇幅长度")
    scene: Optional[str] = Field(None, description="演示场景")
    audience: Optional[str] = Field(None, description="目标受众")
    lang: Optional[str] = Field(None, description="语言")
    prompt: Optional[str] = Field(None, description="用户要求")


@router.post("/v2/generateContent")
async def generate_content(
    request: GenerateContentRequest, user=Depends(get_verified_user)
):
    """生成PPT大纲内容"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        request_data = request.dict()
        log.info(f"生成PPT内容请求: {request_data}")

        if not config.api_key:
            log.error("PPT API密钥未配置")
            raise HTTPException(status_code=500, detail="PPT API密钥未配置")

        api_url = f"{config.api_url}/api/ppt/v2/generateContent"
        log.info(f"请求API URL: {api_url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                api_url,
                json=request_data,
                headers={"Content-Type": "application/json", "Api-Key": config.api_key},
            )

            log.info(f"PPT API响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                log.info(f"PPT API响应成功: {result}")
                return result
            else:
                error_text = await response.atext()
                log.error(f"PPT API响应失败: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"生成内容失败: {error_text}",
                )

    except httpx.RequestError as e:
        log.error(f"生成PPT内容网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except Exception as e:
        log.error(f"生成PPT内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成内容失败: {str(e)}")


class UpdateContentRequest(BaseModel):
    """修改大纲内容请求模型"""

    id: str = Field(..., description="任务ID")
    stream: bool = Field(True, description="是否流式")
    markdown: str = Field(..., description="大纲内容markdown")
    question: Optional[str] = Field(None, description="用户修改建议")


@router.post("/v2/updateContent")
async def update_content(
    request: UpdateContentRequest, user=Depends(get_verified_user)
):
    """修改PPT大纲内容"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        request_data = request.dict()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.api_url}/api/ppt/v2/updateContent",
                json=request_data,
                headers={"Content-Type": "application/json", "Api-Key": config.api_key},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code, detail="修改内容失败"
                )

    except httpx.RequestError as e:
        log.error(f"修改PPT内容网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except Exception as e:
        log.error(f"修改PPT内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"修改内容失败: {str(e)}")


class GeneratePptRequest(BaseModel):
    """生成PPT请求模型"""

    id: str = Field(..., description="任务ID")
    templateId: str = Field(..., description="模板ID")
    markdown: str = Field(..., description="Markdown内容")


@router.post("/v2/generatePptx")
async def generate_ppt(request: GeneratePptRequest, user=Depends(get_verified_user)):
    """生成PPT"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        request_data = request.dict()
        log.info(f"生成PPT请求: {request_data}")

        if not config.api_key:
            log.error("PPT API密钥未配置")
            raise HTTPException(status_code=500, detail="PPT API密钥未配置")

        api_url = f"{config.api_url}/api/ppt/v2/generatePptx"
        log.info(f"请求API URL: {api_url}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                api_url,
                json=request_data,
                headers={"Content-Type": "application/json", "Api-Key": config.api_key},
            )

            log.info(f"PPT生成API响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                log.info(f"PPT生成API响应成功: {result}")
                return result
            else:
                error_text = await response.atext()
                log.error(f"PPT生成API响应失败: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"生成PPT失败: {error_text}",
                )

    except ValidationError as e:
        log.error(f"生成PPT请求数据验证失败: {str(e)}")
        raise HTTPException(status_code=422, detail=f"请求数据格式错误: {str(e)}")
    except httpx.RequestError as e:
        log.error(f"生成PPT网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"生成PPT失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成PPT失败: {str(e)}")


class PptListRequest(BaseModel):
    """PPT列表请求模型"""

    page: int = Field(1, description="页码")
    size: int = Field(10, description="页大小")


@router.post("/listPptx")
async def get_user_ppts(request: PptListRequest, user=Depends(get_verified_user)):
    """获取用户PPT列表"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        request_data = request.dict()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.api_url}/api/ppt/listPptx",
                json=request_data,
                headers={"Content-Type": "application/json", "Api-Key": config.api_key},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code, detail="获取PPT列表失败"
                )

    except httpx.RequestError as e:
        log.error(f"获取PPT列表网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except Exception as e:
        log.error(f"获取PPT列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取PPT列表失败: {str(e)}")


@router.get("/loadPptx")
async def load_ppt(id: str, user=Depends(get_verified_user)):
    """加载PPT数据"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.api_url}/api/ppt/loadPptx",
                params={"id": id},
                headers={"Api-Key": config.api_key},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code, detail="加载PPT数据失败"
                )

    except httpx.RequestError as e:
        log.error(f"加载PPT数据网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except Exception as e:
        log.error(f"加载PPT数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加载PPT数据失败: {str(e)}")


class LoadPptMarkdownRequest(BaseModel):
    """加载PPT大纲请求模型"""

    id: str = Field(..., description="PPT ID")
    format: str = Field("tree", description="输出格式: text|tree")


@router.post("/loadPptxMarkdown")
async def load_ppt_markdown(
    request: LoadPptMarkdownRequest, user=Depends(get_verified_user)
):
    """加载PPT大纲内容"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        request_data = request.dict()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.api_url}/api/ppt/loadPptxMarkdown",
                json=request_data,
                headers={"Content-Type": "application/json", "Api-Key": config.api_key},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code, detail="加载PPT大纲失败"
                )

    except httpx.RequestError as e:
        log.error(f"加载PPT大纲网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except Exception as e:
        log.error(f"加载PPT大纲失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加载PPT大纲失败: {str(e)}")


class DownloadPptRequest(BaseModel):
    """下载PPT请求模型"""

    id: str = Field(..., description="PPT ID")
    refresh: bool = Field(False, description="是否刷新")


@router.post("/downloadPptx")
async def download_ppt(request: DownloadPptRequest, user=Depends(get_verified_user)):
    """下载PPT"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    try:
        request_data = request.dict()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.api_url}/api/ppt/downloadPptx",
                json=request_data,
                headers={"Content-Type": "application/json", "Api-Key": config.api_key},
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code, detail="下载PPT失败"
                )

    except httpx.RequestError as e:
        log.error(f"下载PPT网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except Exception as e:
        log.error(f"下载PPT失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载PPT失败: {str(e)}")


@router.get("/downloadWithAnimation")
async def download_ppt_with_animation(
    type: int = 1, id: str = None, user=Depends(get_verified_user)
):
    """下载智能动画PPT"""
    config = get_current_ppt_config()
    if not config.enabled:
        raise HTTPException(status_code=503, detail="PPT功能未启用")

    if not id:
        raise HTTPException(status_code=400, detail="PPT ID不能为空")

    try:
        params = {"type": type, "id": id}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.api_url}/api/ppt/downloadWithAnimation",
                params=params,
                headers={"Api-Key": config.api_key},
            )

            if response.status_code == 200:
                # 返回文件流
                return Response(
                    content=response.content,
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": f"attachment; filename=ppt_with_animation_{id}.pptx"
                    },
                )
            else:
                raise HTTPException(
                    status_code=response.status_code, detail="下载动画PPT失败"
                )

    except httpx.RequestError as e:
        log.error(f"下载动画PPT网络错误: {str(e)}")
        raise HTTPException(status_code=503, detail=f"网络请求失败: {str(e)}")
    except Exception as e:
        log.error(f"下载动画PPT失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载动画PPT失败: {str(e)}")


@router.get("/status")
async def get_ppt_status(user=Depends(get_verified_user)):
    """获取PPT服务状态"""
    try:
        config = get_current_ppt_config()
        if not config.enabled:
            return {"enabled": False, "message": "PPT功能未启用"}

        # 测试连接
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.api_url}/api/ppt/v2/options",
                headers={"Api-Key": config.api_key},
                timeout=5.0,
            )

            if response.status_code == 200:
                return {
                    "enabled": True,
                    "status": "online",
                    "message": "PPT服务正常",
                    "api_key": config.api_key,  # 添加api_key供前端使用
                }
            else:
                return {
                    "enabled": True,
                    "status": "error",
                    "message": f"PPT服务异常: {response.status_code}",
                    "api_key": config.api_key,  # 即使服务异常也返回api_key
                }

    except httpx.RequestError as e:
        return {
            "enabled": True,
            "status": "offline",
            "message": f"PPT服务连接失败: {str(e)}",
            "api_key": config.api_key,  # 网络错误时也返回api_key
        }
    except Exception as e:
        return {
            "enabled": False,
            "status": "error",
            "message": f"PPT服务状态检查失败: {str(e)}",
        }
