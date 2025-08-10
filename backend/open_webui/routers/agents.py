"""
Agent Marketplace API Routes
智能体广场API路由
"""

import json
import time
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from open_webui.models.agents import (
    AgentApps,
    AgentAppSubmissions,
    AgentAppFavorites,
    AgentAppStats,
    AgentApp,
    AgentAppSubmission,
    AgentAppFavorite,
)
from open_webui.models.users import Users
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.utils.utils import get_current_user

log = logging.getLogger(__name__)

router = APIRouter()


# ========== 数据模型 ==========


class AgentAppCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field(default="general")
    icon: Optional[str] = None
    app_type: str = Field(default="form")
    form_config: Dict[str, Any] = Field(default_factory=dict)
    ai_config: Dict[str, Any] = Field(default_factory=dict)
    access_control: Dict[str, Any] = Field(default_factory=dict)
    cost_per_use: int = Field(default=100, ge=0)
    usage_limit: int = Field(default=0, ge=0)


class AgentAppUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[str] = None
    form_config: Optional[Dict[str, Any]] = None
    ai_config: Optional[Dict[str, Any]] = None
    access_control: Optional[Dict[str, Any]] = None
    cost_per_use: Optional[int] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, ge=0)


class AgentAppResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str]
    category: str
    icon: Optional[str]
    app_type: str
    status: str
    form_config: Dict[str, Any]
    ai_config: Dict[str, Any]
    access_control: Dict[str, Any]
    usage_limit: int
    cost_per_use: int
    usage_count: int
    favorite_count: int
    rating: int
    created_by: str
    created_at: int
    updated_at: int


class FormSubmissionRequest(BaseModel):
    form_data: Dict[str, Any]
    files: Optional[List[str]] = None


class AppListResponse(BaseModel):
    apps: List[AgentAppResponse]
    total: int
    page: int
    limit: int
    user_favorites: Optional[List[str]] = None


# ========== 应用管理API ==========


@router.get("/", response_model=AppListResponse)
async def get_agent_apps(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    status: str = Query("active"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_verified_user),
):
    """获取智能体应用列表"""
    try:
        offset = (page - 1) * limit

        apps = AgentApps.get_apps(
            category=category,
            search=search,
            status=status,
            limit=limit,
            offset=offset,
            user_id=user.id if user.role != "admin" else None,
        )

        # 获取用户收藏列表
        user_favorites = AgentAppFavorites.get_user_favorites(user.id) if user else []

        # 获取总数（简化实现，实际应该有专门的count方法）
        total_apps = AgentApps.get_apps(
            category=category, search=search, status=status, limit=1000, offset=0
        )
        total = len(total_apps)

        return AppListResponse(
            apps=apps,
            total=total,
            page=page,
            limit=limit,
            user_favorites=user_favorites,
        )

    except Exception as e:
        log.error(f"Error getting agent apps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{app_id}")
async def get_agent_app_by_id(app_id: str, user=Depends(get_verified_user)):
    """根据ID获取智能体应用详情"""
    try:
        app = AgentApps.get_app_by_id(app_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        # 检查访问权限
        if (
            app.status != "active"
            and user.role != "admin"
            and app.created_by != user.id
        ):
            raise HTTPException(status_code=403, detail="Access denied")

        # 检查是否收藏
        is_favorited = AgentAppFavorites.is_favorited(app_id, user.id)

        return {"app": app, "is_favorited": is_favorited}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting agent app: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=AgentAppResponse)
async def create_agent_app(form_data: AgentAppCreate, user=Depends(get_admin_user)):
    """创建智能体应用（管理员）"""
    try:
        app = AgentApps.create_app(
            name=form_data.name,
            display_name=form_data.display_name,
            description=form_data.description,
            category=form_data.category,
            icon=form_data.icon,
            form_config=form_data.form_config,
            ai_config=form_data.ai_config,
            cost_per_use=form_data.cost_per_use,
            access_control=form_data.access_control,
            created_by=user.id,
        )

        if not app:
            raise HTTPException(status_code=400, detail="Failed to create application")

        return app

    except Exception as e:
        log.error(f"Error creating agent app: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{app_id}")
async def update_agent_app(
    app_id: str, form_data: AgentAppUpdate, user=Depends(get_admin_user)
):
    """更新智能体应用（管理员）"""
    try:
        app = AgentApps.get_app_by_id(app_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        # 构建更新数据
        update_data = {}
        for field, value in form_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        success = AgentApps.update_app(app_id, **update_data)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update application")

        return {"message": "Application updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating agent app: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{app_id}")
async def delete_agent_app(app_id: str, user=Depends(get_admin_user)):
    """删除智能体应用（管理员）"""
    try:
        success = AgentApps.delete_app(app_id)
        if not success:
            raise HTTPException(status_code=404, detail="Application not found")

        return {"message": "Application deleted successfully"}

    except Exception as e:
        log.error(f"Error deleting agent app: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 表单提交API ==========


@router.post("/{app_id}/submit")
async def submit_agent_form(
    app_id: str,
    form_data: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    user=Depends(get_verified_user),
):
    """提交智能体应用表单"""
    try:
        # 获取应用配置
        app = AgentApps.get_app_by_id(app_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        if app.status != "active":
            raise HTTPException(status_code=403, detail="Application is not active")

        # 解析表单数据
        try:
            parsed_form_data = json.loads(form_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid form data format")

        # 验证表单数据
        validation_result = validate_form_data(app.form_config, parsed_form_data)
        if not validation_result["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Form validation failed",
                    "errors": validation_result["errors"],
                },
            )

        # 处理文件上传
        file_urls = []
        if files:
            file_urls = await process_uploaded_files(files, user.id)

        # 创建提交记录
        submission = AgentAppSubmissions.create_submission(
            app_id=app_id, user_id=user.id, form_data=parsed_form_data, files=file_urls
        )

        if not submission:
            raise HTTPException(status_code=500, detail="Failed to create submission")

        # 增加应用使用次数
        AgentApps.increment_usage_count(app_id)

        # 异步处理AI响应（这里简化处理）
        try:
            ai_response = await process_ai_response(app, parsed_form_data, file_urls)
            AgentAppSubmissions.update_submission_response(
                submission.id,
                ai_response=ai_response,
                status="completed",
                processing_time=1000,  # 简化的处理时间
            )
        except Exception as ai_error:
            log.error(f"AI processing failed: {ai_error}")
            AgentAppSubmissions.update_submission_response(
                submission.id,
                ai_response="",
                status="failed",
                error_message=str(ai_error),
            )

        return {
            "submission_id": submission.id,
            "status": "completed",
            "ai_response": ai_response if "ai_response" in locals() else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error submitting form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{app_id}/favorite")
async def toggle_favorite_app(app_id: str, user=Depends(get_verified_user)):
    """切换应用收藏状态"""
    try:
        app = AgentApps.get_app_by_id(app_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        is_favorited = AgentAppFavorites.is_favorited(app_id, user.id)

        if is_favorited:
            AgentAppFavorites.remove_favorite(app_id, user.id)
            return {"favorited": False}
        else:
            AgentAppFavorites.add_favorite(app_id, user.id)
            return {"favorited": True}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error toggling favorite: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{app_id}/stats")
async def get_agent_app_stats(app_id: str, user=Depends(get_verified_user)):
    """获取应用统计信息"""
    try:
        app = AgentApps.get_app_by_id(app_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        # 这里应该从统计表获取详细数据，简化实现
        return {
            "app_id": app_id,
            "usage_count": app.usage_count,
            "favorite_count": app.favorite_count,
            "rating": app.rating,
            "created_at": app.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting app stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 提交记录API ==========


@router.get("/submissions")
async def get_submissions(
    app_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_verified_user),
):
    """获取用户提交历史"""
    try:
        offset = (page - 1) * limit

        submissions = AgentAppSubmissions.get_user_submissions(
            user_id=user.id, app_id=app_id, limit=limit, offset=offset
        )

        return {"submissions": submissions, "page": page, "limit": limit}

    except Exception as e:
        log.error(f"Error getting submissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/submissions/{submission_id}")
async def get_submission_by_id(submission_id: str, user=Depends(get_verified_user)):
    """根据ID获取提交记录详情"""
    try:
        submission = AgentAppSubmissions.get_submission_by_id(submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # 检查权限
        if submission.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        return submission

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting submission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 分类管理API ==========


@router.get("/categories")
async def get_app_categories(user=Depends(get_verified_user)):
    """获取应用分类列表"""
    try:
        categories = AgentApps.get_categories()
        return {"categories": categories}

    except Exception as e:
        log.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 工具函数 ==========


def validate_form_data(
    form_config: Dict[str, Any], form_data: Dict[str, Any]
) -> Dict[str, Any]:
    """验证表单数据"""
    errors = {}
    is_valid = True

    if not form_config or "fields" not in form_config:
        return {"is_valid": True, "errors": {}}

    for field in form_config["fields"]:
        field_id = field.get("id")
        field_type = field.get("type")
        required = field.get("required", False)
        value = form_data.get(field_id)

        # 检查必填字段
        if required and (
            value is None
            or value == ""
            or (isinstance(value, list) and len(value) == 0)
        ):
            errors[field_id] = "此字段为必填项"
            is_valid = False
            continue

        # 如果值为空且非必填，跳过验证
        if value is None or value == "":
            continue

        # 根据字段类型进行验证
        field_errors = validate_field_value(field, value)
        if field_errors:
            errors[field_id] = field_errors
            is_valid = False

    return {"is_valid": is_valid, "errors": errors}


def validate_field_value(field: Dict[str, Any], value: Any) -> Optional[str]:
    """验证单个字段值"""
    field_type = field.get("type")
    validation = field.get("validation", {})

    if field_type == "text":
        if not isinstance(value, str):
            return "必须是文本类型"

        min_length = validation.get("minLength")
        max_length = validation.get("maxLength")

        if min_length and len(value) < min_length:
            return f"最少需要{min_length}个字符"
        if max_length and len(value) > max_length:
            return f"最多允许{max_length}个字符"

    elif field_type == "select":
        options = field.get("options", [])
        valid_values = [opt["value"] for opt in options]

        if value not in valid_values:
            return "请选择有效的选项"

    elif field_type == "file":
        if not isinstance(value, list):
            return "文件字段必须是数组类型"

        max_files = validation.get("maxFiles", 1)
        if len(value) > max_files:
            return f"最多只能上传{max_files}个文件"

    return None


async def process_uploaded_files(
    files: List[UploadFile], user_id: str
) -> List[Dict[str, Any]]:
    """处理上传的文件"""
    file_info_list = []

    for file in files:
        if file.filename:
            # 这里应该实现实际的文件上传逻辑
            # 简化实现，返回文件信息
            file_info = {
                "name": file.filename,
                "size": 0,  # 实际应该获取文件大小
                "type": file.content_type,
                "url": f"/files/{user_id}/{file.filename}",  # 简化的URL
                "upload_time": int(time.time()),
            }
            file_info_list.append(file_info)

    return file_info_list


async def process_ai_response(
    app: AgentApp, form_data: Dict[str, Any], files: List[Dict[str, Any]]
) -> str:
    """处理AI响应（简化实现）"""
    try:
        ai_config = app.ai_config
        system_prompt = ai_config.get("system_prompt", "")

        # 构建用户输入
        user_input = []
        for key, value in form_data.items():
            user_input.append(f"{key}: {value}")

        if files:
            file_names = [f["name"] for f in files]
            user_input.append(f"附件: {', '.join(file_names)}")

        prompt = f"{system_prompt}\n\n用户输入:\n" + "\n".join(user_input)

        # 这里应该调用实际的AI接口
        # 简化实现，返回固定响应
        return f"基于您提供的信息，我为您生成了以下回答：\n\n这是一个示例AI响应，基于表单数据：{json.dumps(form_data, ensure_ascii=False)}"

    except Exception as e:
        log.error(f"AI processing error: {e}")
        raise e


# ========== 管理员API ==========


@router.get("/admin/stats")
async def get_admin_stats(user=Depends(get_admin_user)):
    """获取管理员统计信息"""
    try:
        # 这里应该实现实际的统计逻辑
        stats = {
            "total_apps": len(AgentApps.get_apps(limit=1000)),
            "active_apps": len(AgentApps.get_apps(status="active", limit=1000)),
            "total_submissions": 0,  # 应该从提交记录表统计
            "total_users": len(Users.get_users()),
        }

        return stats

    except Exception as e:
        log.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/apps")
async def get_admin_app_list(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_admin_user),
):
    """获取管理员应用列表"""
    try:
        offset = (page - 1) * limit

        apps = AgentApps.get_apps(
            category=category, search=search, status=status, limit=limit, offset=offset
        )

        return {"apps": apps, "page": page, "limit": limit}

    except Exception as e:
        log.error(f"Error getting admin app list: {e}")
        raise HTTPException(status_code=500, detail=str(e))
