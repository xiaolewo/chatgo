import base64
import math
from decimal import Decimal
from io import BytesIO
from typing import Optional, Union

import httpx
from PIL import Image
from fastapi import HTTPException
from pydantic import BaseModel

from open_webui.config import (
    USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE,
    USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE,
    USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE,
    USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE,
    USAGE_CALCULATE_DEFAULT_TOKEN_PRICE,
    USAGE_CALCULATE_DEFAULT_REQUEST_PRICE,
    CREDIT_NO_CREDIT_MSG,
)
from open_webui.models.chats import Chats
from open_webui.models.credits import Credits
from open_webui.models.models import Models, ModelModel


def get_model_price(
    model: Optional[ModelModel] = None,
) -> (Decimal, Decimal, Decimal, Decimal):
    # no model provide
    if not model or not isinstance(model, ModelModel):
        return (
            Decimal(USAGE_CALCULATE_DEFAULT_TOKEN_PRICE.value),
            Decimal(USAGE_CALCULATE_DEFAULT_TOKEN_PRICE.value),
            Decimal(USAGE_CALCULATE_DEFAULT_REQUEST_PRICE.value),
            Decimal(0),
        )
    # base model
    if model.base_model_id:
        base_model = Models.get_model_by_id(model.base_model_id)
        if base_model:
            return get_model_price(base_model)
    # model price
    model_price = model.price or {}
    return (
        Decimal(
            model_price.get("prompt_price", USAGE_CALCULATE_DEFAULT_TOKEN_PRICE.value)
        ),
        Decimal(
            model_price.get(
                "completion_price", USAGE_CALCULATE_DEFAULT_TOKEN_PRICE.value
            )
        ),
        Decimal(
            model_price.get(
                "request_price", USAGE_CALCULATE_DEFAULT_REQUEST_PRICE.value
            )
        ),
        Decimal(model_price.get("minimum_credit", 0)),
    )


def get_feature_price(features: Union[set, list]) -> Decimal:
    if not features:
        return Decimal(0)
    price = Decimal(0)
    for feature in features:
        match feature:
            case "image_generation":
                price += (
                    Decimal(USAGE_CALCULATE_FEATURE_IMAGE_GEN_PRICE.value) / 1000 / 1000
                )
            case "code_interpreter":
                price += (
                    Decimal(USAGE_CALCULATE_FEATURE_CODE_EXECUTE_PRICE.value)
                    / 1000
                    / 1000
                )
            case "web_search":
                price += (
                    Decimal(USAGE_CALCULATE_FEATURE_WEB_SEARCH_PRICE.value)
                    / 1000
                    / 1000
                )
            case "direct_tool_servers":
                price += (
                    Decimal(USAGE_CALCULATE_FEATURE_TOOL_SERVER_PRICE.value)
                    / 1000
                    / 1000
                )
    return price


def is_free_request(model_price: list, form_data: dict) -> bool:
    is_free_model = sum(float(price) for price in model_price) <= 0

    features = (
        form_data.get("features")
        or (form_data.get("metadata") or {}).get("features")
        or {}
    )
    is_feature_free = get_feature_price({k for k, v in features.items() if v}) <= 0

    return is_free_model and is_feature_free


def check_credit_by_user_id(user_id: str, form_data: dict) -> None:
    """
    检查用户是否有足够的积分执行请求
    1. 首先检查用户所在权限组中所有管理员的积分是否充足
    2. 如果所有管理员积分都不充足，才扣除用户自己的积分
    Args:
        user_id (str): 用户唯一标识符
        form_data (dict): 请求表单数据，包含模型ID等信息

    Returns:
        None: 若积分足够则返回None，否则抛出HTTPException

    Raises:
        HTTPException: 当用户积分不足时，抛出403异常
    """
    from open_webui.models.groups import Groups
    from open_webui.models.subscription import SubscriptionCredits

    # 加载模型信息，获取模型的价格信息
    model_id = form_data.get("model") or form_data.get("model_id") or ""
    model = Models.get_model_by_id(model_id)
    model_price = get_model_price(model)
    minimum_credit = model_price[-1]  # 获取模型所需的最低积分

    # 检查请求是否免费，若免费则直接返回，无需检查积分
    if is_free_request(model_price=model_price, form_data=form_data):
        return

    # 加载元数据，用于后续错误处理
    metadata = form_data.get("metadata") or form_data

    # 获取用户所在的所有权限组（按加入时间排序）
    group_list = Groups.get_user_groups_ordered(user_id)

    # 1. 首先检查所有权限组管理员的积分是否充足
    admin_has_sufficient_credit = False
    user_id_to_check = None

    # 遍历所有权限组，检查每个管理员的积分
    for group in group_list or []:
        # 跳过无效的组或没有管理员的组
        if not group or not group.admin_id:
            continue

        # 跳过用户自己是管理员的组
        if group.admin_id == user_id:
            continue
        # print("当前存着的权限组:",group.name) 习惯测试
        # 获取管理员的积分信息
        admin_credit = Credits.get_credit_by_user_id(group.admin_id)
        if not admin_credit:
            continue

        # 获取管理员的套餐积分
        admin_subscription_credits = SubscriptionCredits.get_total_active_credits(
            group.admin_id
        )

        # 计算管理员的总可用积分（普通积分 + 套餐积分）
        admin_total_credits = (
            float(admin_credit.credit if admin_credit else 0)
            + admin_subscription_credits
        )

        # 如果找到任何一个管理员积分足够（总积分>0且满足最低积分要求），标记为有足够积分
        if admin_total_credits > 0 and admin_total_credits >= minimum_credit:
            admin_has_sufficient_credit = True
            user_id_to_check = group.admin_id  # 记录这个管理员ID
            break  # 找到后退出循环

    # 2. 如果所有管理员积分都不充足，检查用户自己的积分
    if not admin_has_sufficient_credit:
        user_id_to_check = user_id  # 使用用户自己的ID进行检查

    # 获取要检查用户的积分信息
    credit = Credits.get_credit_by_user_id(user_id_to_check)
    if not credit:
        # 积分记录不存在，抛出异常
        if isinstance(metadata, dict) and metadata:
            chat_id = metadata.get("chat_id")
            message_id = metadata.get("message_id") or metadata.get("id")
            if chat_id and message_id:
                Chats.upsert_message_to_chat_by_id_and_message_id(
                    chat_id,
                    message_id,
                    {"error": {"content": CREDIT_NO_CREDIT_MSG.value}},
                )
        raise HTTPException(status_code=403, detail=CREDIT_NO_CREDIT_MSG.value)

    # 获取要检查用户的套餐积分
    subscription_credits = SubscriptionCredits.get_total_active_credits(
        user_id_to_check
    )

    # 计算总可用积分（普通积分 + 套餐积分）
    total_credits = float(credit.credit if credit else 0) + subscription_credits

    # 检查积分是否足够执行请求
    if total_credits <= 0 or total_credits < minimum_credit:
        # 如果积分不足，尝试更新聊天消息，添加错误信息
        if isinstance(metadata, dict) and metadata:
            chat_id = metadata.get("chat_id")  # 获取聊天ID
            message_id = metadata.get("message_id") or metadata.get("id")  # 获取消息ID
            if chat_id and message_id:  # 如果聊天ID和消息ID都存在
                # 更新消息，添加错误信息
                Chats.upsert_message_to_chat_by_id_and_message_id(
                    chat_id,
                    message_id,
                    {"error": {"content": CREDIT_NO_CREDIT_MSG.value}},
                )

        # 抛出积分不足的异常
        raise HTTPException(status_code=403, detail=CREDIT_NO_CREDIT_MSG.value)


class ImageURL(BaseModel):
    url: str
    detail: str


def calculate_image_token(model_id: str, image: ImageURL) -> int:
    if not image or not image.url:
        return 0

    base_tokens = 85

    if image.detail == "low":
        return 85

    if image.detail == "auto" or not image.detail:
        image.detail = "high"

    tile_tokens = 170

    if model_id.find("gpt-4o-mini") != -1:
        tile_tokens = 5667
        base_tokens = 2833

    if model_id.find("gemini") != -1 or model_id.find("claude") != -1:
        return 3 * base_tokens

    if image.url.startswith("http"):
        with httpx.Client(trust_env=True, timeout=60) as client:
            response = client.get(image.url)
        response.raise_for_status()
        image_data = base64.b64encode(response.content).decode("utf-8")
    else:
        if "," in image.url:
            image_data = image.url.split(",", 1)[1]
        else:
            image_data = image.url

    image_data = base64.b64decode(image_data.encode("utf-8"))
    image = Image.open(BytesIO(image_data))
    width, height = image.size

    short_side = width
    other_side = height

    scale = 1.0

    if height < short_side:
        short_side = height
        other_side = width

    if short_side > 768:
        scale = short_side / 768
        short_side = 768

    other_side = math.ceil(other_side / scale)

    tiles = (short_side + 511) / 512 * ((other_side + 511) / 512)

    return math.ceil(tiles * tile_tokens + base_tokens)
