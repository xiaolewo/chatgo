import time
import logging
import sys

from aiocache import cached
from fastapi import Request

from open_webui.routers import openai, ollama
from open_webui.functions import get_function_models


from open_webui.models.functions import Functions
from open_webui.models.models import Models


from open_webui.utils.plugin import load_function_module_by_id
from open_webui.utils.access_control import has_access


from open_webui.config import (
    DEFAULT_ARENA_MODEL,
)

from open_webui.env import SRC_LOG_LEVELS, GLOBAL_LOG_LEVEL
from open_webui.models.users import UserModel


logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL)
log = logging.getLogger(__name__)
logger = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])


async def get_all_base_models(request: Request, user: UserModel = None):
    function_models = []
    openai_models = []
    ollama_models = []

    if request.app.state.config.ENABLE_OPENAI_API:
        openai_models = await openai.get_all_models(request, user=user)
        openai_models = openai_models["data"]

    if request.app.state.config.ENABLE_OLLAMA_API:
        ollama_models = await ollama.get_all_models(request, user=user)
        ollama_models = [
            {
                "id": model["model"],
                "name": model["name"],
                "object": "model",
                "created": int(time.time()),
                "owned_by": "ollama",
                "ollama": model,
                "tags": model.get("tags", []),
            }
            for model in ollama_models["models"]
        ]

    function_models = await get_function_models(request)
    models = function_models + openai_models + ollama_models

    return models


@cached(ttl=3600)  # 缓存 1 小时
async def get_all_models(request, user: UserModel = None):
    # 1. 获取基础模型，无数据直接返回空列表
    models = await get_all_base_models(request, user=user)
    if len(models) == 0:
        request.app.state.MODELS = {}
        logger.debug("get_all_models() returned 0 models (no base models)")
        return []

    # 2. 追加竞技场模型（配置开启时）
    ARENA_OWNED_BY = "arena"
    MODEL_OBJECT_TYPE = "model"
    if request.app.state.config.ENABLE_EVALUATION_ARENA_MODELS:
        arena_models = []
        if len(request.app.state.config.EVALUATION_ARENA_MODELS) > 0:
            arena_models = [
                {
                    "id": model["id"],
                    "name": model["name"],
                    "info": {"meta": model["meta"]},
                    "object": MODEL_OBJECT_TYPE,
                    "created": int(time.time()),
                    "owned_by": ARENA_OWNED_BY,
                    "arena": True,
                }
                for model in request.app.state.config.EVALUATION_ARENA_MODELS
            ]
        else:
            # 添加默认竞技场模型
            arena_models = [
                {
                    "id": DEFAULT_ARENA_MODEL["id"],
                    "name": DEFAULT_ARENA_MODEL["name"],
                    "info": {"meta": DEFAULT_ARENA_MODEL["meta"]},
                    "object": MODEL_OBJECT_TYPE,
                    "created": int(time.time()),
                    "owned_by": ARENA_OWNED_BY,
                    "arena": True,
                }
            ]
        models = models + arena_models

    # 3. 预处理动作ID，转换集合提升查询性能
    global_action_ids = [
        function.id for function in Functions.get_global_action_functions()
    ]
    enabled_action_ids = [
        function.id
        for function in Functions.get_functions_by_type("action", active_only=True)
    ]
    enabled_action_set = set(enabled_action_ids)  # O(1) 查寻替代 O(n)

    # 4. 处理自定义模型（修复遍历删除索引异常，优化匹配逻辑）
    OLLAMA_OWNED_BY = "ollama"
    OPENAI_DEFAULT_OWNED_BY = "openai"
    UNKNOWN_OWNED_BY = "unknown owner"
    custom_models = Models.get_all_models()
    models_to_remove = []  # 标记待删除模型，避免遍历中修改列表

    for custom_model in custom_models:
        if custom_model.base_model_id is None:
            # 匹配现有模型并更新/标记删除
            for idx, model in enumerate(models):
                model_id = model["id"]
                custom_id = custom_model.id
                # 优化Ollama匹配，split仅分割1次，匹配到即处理
                is_match = custom_id == model_id or (
                    model.get("owned_by") == OLLAMA_OWNED_BY
                    and custom_id == model_id.split(":", 1)[0]
                )
                if is_match:
                    if custom_model.is_active:
                        model["name"] = custom_model.name
                        model["info"] = custom_model.model_dump()
                        # 安全提取actionIds，避免空值报错
                        model["action_ids"] = (
                            model["info"].get("meta", {}).get("actionIds", [])
                        )
                    else:
                        models_to_remove.append(idx)
            # 倒序删除标记模型，防止索引偏移
            for idx in reversed(models_to_remove):
                models.pop(idx)
            models_to_remove.clear()  # 清空标记列表

        # 追加激活的新自定义模型（未存在于现有列表时）
        elif custom_model.is_active and custom_model.id not in {
            m["id"] for m in models
        }:
            owned_by = OPENAI_DEFAULT_OWNED_BY
            pipe = None
            # 匹配基础模型，找到后立即终止循环
            for model in models:
                if (
                    custom_model.base_model_id == model["id"]
                    or custom_model.base_model_id == model["id"].split(":", 1)[0]
                ):
                    owned_by = model.get("owned_by", UNKNOWN_OWNED_BY)
                    pipe = model.get("pipe")
                    break
            # 安全提取元数据中的actionIds
            action_ids = []
            if custom_model.meta:
                action_ids = custom_model.meta.model_dump().get("actionIds", [])
            # 构建自定义模型1
            custom_model_dict = {
                "id": f"{custom_model.id}",
                "name": custom_model.name,
                "object": MODEL_OBJECT_TYPE,
                "created": custom_model.created_at,
                "owned_by": owned_by,
                "info": custom_model.model_dump(),
                "preset": True,
                "action_ids": action_ids,
            }
            if pipe is not None:
                custom_model_dict["pipe"] = pipe
            models.append(custom_model_dict)

    # 5. 处理模型动作（优化异常提示，缓存函数模块）
    def get_action_items_from_module(function, module):
        if hasattr(module, "actions"):
            return [
                {
                    "id": f"{function.id}.{action['id']}",
                    "name": action.get("name", f"{function.name} ({action['id']})"),
                    "description": function.meta.description,
                    "icon_url": action.get(
                        "icon_url", function.meta.manifest.get("icon_url", None)
                    ),
                }
                for action in module.actions
            ]
        else:
            return [
                {
                    "id": function.id,
                    "name": function.name,
                    "description": function.meta.description,
                    "icon_url": function.meta.manifest.get("icon_url", None),
                }
            ]

    def get_function_module_by_id(function_id):
        if function_id in request.app.state.FUNCTIONS:
            return request.app.state.FUNCTIONS[function_id]
        else:
            function_module, _, _ = load_function_module_by_id(function_id)
            request.app.state.FUNCTIONS[function_id] = function_module
            return function_module

    # 遍历处理所有模型动作
    for model in models:
        # 合并去重动作ID，过滤未启用的ID（集合操作优化）
        action_ids = [
            action_id
            for action_id in list(set(model.pop("action_ids", []) + global_action_ids))
            if action_id in enabled_action_set
        ]
        model["actions"] = []
        for action_id in action_ids:
            action_function = Functions.get_function_by_id(action_id)
            if action_function is None:
                raise ValueError(f"Action not found: {action_id}")  # 精准异常类型
            function_module = get_function_module_by_id(action_id)
            model["actions"].extend(
                get_action_items_from_module(action_function, function_module)
            )

    # 6. 缓存模型到应用状态，记录日志
    request.app.state.MODELS = {model["id"]: model for model in models}
    logger.debug(f"get_all_models() returned {len(models)} models")
    return models


def check_model_access(user, model):
    if model.get("arena"):
        if not has_access(
            user.id,
            type="read",
            access_control=model.get("info", {})
            .get("meta", {})
            .get("access_control", {}),
        ):
            raise Exception("Model not found")
    else:
        model_info = Models.get_model_by_id(model.get("id"))
        if not model_info:
            raise Exception("Model not found")
        elif not (
            user.id == model_info.user_id
            or has_access(
                user.id, type="read", access_control=model_info.access_control
            )
        ):
            raise Exception("Model not found")
