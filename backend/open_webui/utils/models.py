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


import asyncio


async def get_all_base_models(request: Request, user: UserModel = None):
    function_models = []
    openai_models = []
    ollama_models = []

    # 并行执行所有模型加载任务
    tasks = []
    task_names = []

    if request.app.state.config.ENABLE_OPENAI_API:
        tasks.append(openai.get_all_models(request, user=user))
        task_names.append("openai")

    if request.app.state.config.ENABLE_OLLAMA_API:
        tasks.append(ollama.get_all_models(request, user=user))
        task_names.append("ollama")

    tasks.append(get_function_models(request))
    task_names.append("function")

    # 并行执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    for i, result in enumerate(results):
        task_name = task_names[i]
        try:
            if task_name == "openai" and not isinstance(result, Exception):
                openai_models = result["data"]
                logger.debug(f"Loaded {len(openai_models)} OpenAI models")
            elif task_name == "ollama" and not isinstance(result, Exception):
                ollama_data = result
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
                    for model in ollama_data["models"]
                ]
                logger.debug(f"Loaded {len(ollama_models)} Ollama models")
            elif task_name == "function" and not isinstance(result, Exception):
                function_models = result
                logger.debug(f"Loaded {len(function_models)} function models")
            elif isinstance(result, Exception):
                logger.error(f"Error in {task_name} models: {result}")
        except Exception as e:
            logger.error(f"Error processing {task_name} results: {e}")

    models = function_models + openai_models + ollama_models
    logger.debug(f"get_all_base_models() returned {len(models)} models")
    return models


# 移除缓存装饰器，直接实现缓存逻辑
from aiocache import Cache

# 创建全局缓存实例，确保所有操作共享同一个缓存
from aiocache.backends.memory import SimpleMemoryCache

# 使用SimpleMemoryCache确保缓存操作可靠
MODEL_CACHE = SimpleMemoryCache()


async def get_all_models(request, user: UserModel = None):
    # 使用固定缓存键，确保缓存稳定
    cache_key = "all_models"
    logger.debug(f"get_all_models() using cache key: {cache_key}")

    # 尝试从缓存获取
    try:
        cached_models = await MODEL_CACHE.get(cache_key)
        logger.debug(f"get_all_models() cache get result: {cached_models is not None}")
        if cached_models:
            logger.debug(
                f"get_all_models() returned {len(cached_models)} models from cache"
            )
            request.app.state.MODELS = {model["id"]: model for model in cached_models}
            return cached_models
    except Exception as e:
        logger.error(f"Error getting from cache: {e}")

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

    # 4. 处理自定义模型（使用字典映射优化性能）
    OLLAMA_OWNED_BY = "ollama"
    OPENAI_DEFAULT_OWNED_BY = "openai"
    UNKNOWN_OWNED_BY = "unknown owner"
    custom_models = Models.get_all_models()
    models_to_remove = []  # 标记待删除模型，避免遍历中修改列表

    # 构建模型ID映射，优化查找性能
    model_id_map = {}
    ollama_model_map = {}
    for idx, model in enumerate(models):
        model_id_map[model["id"]] = idx
        if model.get("owned_by") == OLLAMA_OWNED_BY:
            ollama_model_map[model["id"].split(":", 1)[0]] = idx

    # 构建现有模型ID集合，用于快速判断
    existing_model_ids = {m["id"] for m in models}

    for custom_model in custom_models:
        if custom_model.base_model_id is None:
            # 使用字典映射快速查找匹配模型
            match_idx = model_id_map.get(custom_model.id)
            if not match_idx:
                match_idx = ollama_model_map.get(custom_model.id)

            if match_idx is not None:
                if custom_model.is_active:
                    model = models[match_idx]
                    model["name"] = custom_model.name
                    model["info"] = custom_model.model_dump()
                    # 安全提取actionIds，避免空值报错
                    model["action_ids"] = (
                        model["info"].get("meta", {}).get("actionIds", [])
                    )
                else:
                    models_to_remove.append(match_idx)

            # 倒序删除标记模型，防止索引偏移
            for idx in reversed(sorted(models_to_remove)):
                if idx < len(models):
                    models.pop(idx)
            models_to_remove.clear()  # 清空标记列表

        # 追加激活的新自定义模型（未存在于现有列表时）
        elif custom_model.is_active and custom_model.id not in existing_model_ids:
            owned_by = OPENAI_DEFAULT_OWNED_BY
            pipe = None
            # 使用映射快速查找基础模型
            base_match = None
            if custom_model.base_model_id in model_id_map:
                base_match = models[model_id_map[custom_model.base_model_id]]
            elif custom_model.base_model_id in ollama_model_map:
                base_match = models[ollama_model_map[custom_model.base_model_id]]

            if base_match:
                owned_by = base_match.get("owned_by", UNKNOWN_OWNED_BY)
                pipe = base_match.get("pipe")

            # 安全提取元数据中的actionIds
            action_ids = []
            if custom_model.meta:
                action_ids = custom_model.meta.model_dump().get("actionIds", [])
            # 构建自定义模型
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
            existing_model_ids.add(custom_model.id)

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

    # 缓存到aiocache
    cache_key = "all_models"
    try:
        await MODEL_CACHE.set(cache_key, models, ttl=3600)
        logger.debug(
            f"get_all_models() cached {len(models)} models with key: {cache_key}"
        )
        # 验证缓存是否设置成功
        verify_cache = await MODEL_CACHE.get(cache_key)
        logger.debug(f"get_all_models() cache verify: {verify_cache is not None}")
        if verify_cache:
            logger.debug(f"get_all_models() cache verify count: {len(verify_cache)}")
    except Exception as e:
        logger.error(f"Error setting cache: {e}")

    logger.debug(f"get_all_models() returned {len(models)} models and cached")
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
