#!/usr/bin/env python3
"""
简化的可灵API测试服务器
用于快速测试可灵视频生成功能
"""
import uuid
import time
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import uvicorn

app = FastAPI(title="Kling Test Server")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存存储
tasks = {}

# 配置（测试用）
CONFIG = {
    "KLING_ENABLED": True,
    "KLING_API_URL": "https://api.qingque.cn",  # 示例URL
    "KLING_API_KEY": "your-api-key-here",  # 需要真实的API Key
    "KLING_STD_CREDITS": 5,
    "KLING_PRO_CREDITS": 10,
}


class KlingGenerateRequest(BaseModel):
    model_name: str = "kling-v1"
    prompt: str = Field(..., min_length=1)
    negative_prompt: str = None
    cfg_scale: float = 0.5
    mode: str = "std"
    aspect_ratio: str = "16:9"
    duration: str = "5"
    camera_control: dict = None


@app.get("/api/v1/kling/config")
async def get_config():
    return CONFIG


@app.post("/api/v1/kling/config")
async def update_config(config: dict):
    CONFIG.update(config)
    return {"message": "配置已更新"}


@app.post("/api/v1/kling/verify")
async def verify_connection():
    if not CONFIG["KLING_API_URL"] or not CONFIG["KLING_API_KEY"]:
        return {"message": "API配置不完整", "status": "error"}

    # 测试连接
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CONFIG['KLING_API_URL']}/kling/v1/videos/text2video",
                headers={
                    "Authorization": f"Bearer {CONFIG['KLING_API_KEY']}",
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

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    return {"message": "连接成功", "status": "success"}
                else:
                    return {
                        "message": f"API错误: {result.get('message')}",
                        "status": "error",
                    }
            else:
                return {
                    "message": f"连接失败: HTTP {response.status_code}",
                    "status": "error",
                }

    except Exception as e:
        return {"message": f"连接失败: {str(e)}", "status": "error"}


@app.post("/api/v1/kling/generate")
async def generate_video(request: KlingGenerateRequest):
    if not CONFIG["KLING_ENABLED"]:
        raise HTTPException(status_code=400, detail="可灵服务未启用")

    # 生成任务ID
    task_id = str(uuid.uuid4())
    current_time = int(time.time() * 1000)

    print(f"收到视频生成请求: {request.prompt}")
    print(f"生成任务ID: {task_id}")

    # 如果配置了真实的API，尝试调用
    if (
        CONFIG["KLING_API_URL"] != "your-api-url-here"
        and CONFIG["KLING_API_KEY"] != "your-api-key-here"
    ):
        try:
            # 构建API请求
            api_params = {
                "model_name": request.model_name,
                "prompt": request.prompt,
                "cfg_scale": request.cfg_scale,
                "mode": request.mode,
                "aspect_ratio": request.aspect_ratio,
                "duration": request.duration,
            }

            if request.negative_prompt:
                api_params["negative_prompt"] = request.negative_prompt
            if request.camera_control:
                api_params["camera_control"] = request.camera_control

            # 调用可灵API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{CONFIG['KLING_API_URL']}/kling/v1/videos/text2video",
                    headers={
                        "Authorization": f"Bearer {CONFIG['KLING_API_KEY']}",
                        "Content-Type": "application/json",
                    },
                    json=api_params,
                )

                print(f"可灵API响应: HTTP {response.status_code}")

                if response.is_success:
                    api_result = response.json()
                    print(f"API成功响应: {api_result}")

                    if api_result.get("code") == 0:
                        # 使用真实API响应
                        task_data = api_result["data"]
                        real_task_id = task_data["task_id"]

                        tasks[real_task_id] = {
                            "task_id": real_task_id,
                            "status": task_data["task_status"],
                            "created_at": task_data.get("created_at", current_time),
                            "updated_at": task_data.get("updated_at", current_time),
                            "api_response": api_result,
                        }

                        return {
                            "task_id": real_task_id,
                            "status": task_data["task_status"],
                            "message": "视频生成任务已提交到可灵平台",
                            "credits_used": (
                                CONFIG["KLING_PRO_CREDITS"]
                                if request.mode == "pro"
                                else CONFIG["KLING_STD_CREDITS"]
                            ),
                        }

        except Exception as e:
            print(f"调用真实API失败，使用模拟响应: {e}")

    # 使用模拟响应（用于测试前端功能）
    tasks[task_id] = {
        "task_id": task_id,
        "status": "submitted",
        "created_at": current_time,
        "updated_at": current_time,
        "prompt": request.prompt,
        "mode": request.mode,
        "api_response": {
            "code": 0,
            "message": "success",
            "data": {"task_id": task_id, "task_status": "submitted"},
        },
    }

    # 模拟任务状态变化
    async def simulate_task_progress():
        await asyncio.sleep(5)  # 5秒后变为processing
        if task_id in tasks:
            tasks[task_id]["status"] = "processing"
            tasks[task_id]["updated_at"] = int(time.time() * 1000)

        await asyncio.sleep(15)  # 再15秒后完成
        if task_id in tasks:
            tasks[task_id]["status"] = "succeed"
            tasks[task_id]["updated_at"] = int(time.time() * 1000)
            tasks[task_id]["video_url"] = "https://example.com/demo-video.mp4"
            tasks[task_id]["video_id"] = f"video_{task_id[:8]}"
            tasks[task_id]["video_duration"] = int(request.duration)

    # 后台运行模拟进度
    asyncio.create_task(simulate_task_progress())

    return {
        "task_id": task_id,
        "status": "submitted",
        "message": "视频生成任务已提交（模拟模式）",
        "credits_used": (
            CONFIG["KLING_PRO_CREDITS"]
            if request.mode == "pro"
            else CONFIG["KLING_STD_CREDITS"]
        ),
    }


@app.get("/api/v1/kling/task/{task_id}")
async def get_task_status(task_id: str):
    if task_id in tasks:
        task = tasks[task_id]

        # 尝试从可灵API获取最新状态
        if task["status"] in ["submitted", "processing"]:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{CONFIG['KLING_API_URL']}/kling/v1/videos/text2video/{task_id}",
                        headers={
                            "Authorization": f"Bearer {CONFIG['KLING_API_KEY']}",
                            "Content-Type": "application/json",
                        },
                    )

                    if response.is_success:
                        api_result = response.json()
                        if api_result.get("code") == 0:
                            task_data = api_result["data"]
                            task["status"] = task_data.get(
                                "task_status", task["status"]
                            )
                            task["updated_at"] = task_data.get(
                                "updated_at", int(time.time() * 1000)
                            )
                            if task_data.get("task_result"):
                                videos = task_data["task_result"].get("videos", [])
                                if videos:
                                    task["video_url"] = videos[0].get("url")
                                    task["video_id"] = videos[0].get("id")
                                    task["video_duration"] = videos[0].get("duration")
            except Exception as e:
                print(f"查询任务状态失败: {e}")

        return {
            "task_id": task_id,
            "status": task["status"],
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
            "video_url": task.get("video_url"),
            "video_id": task.get("video_id"),
            "video_duration": task.get("video_duration"),
            "message": f"任务状态: {task['status']}",
        }
    else:
        raise HTTPException(status_code=404, detail="任务不存在")


@app.get("/api/v1/kling/tasks")
async def get_tasks():
    return list(tasks.values())


@app.delete("/api/v1/kling/task/{task_id}")
async def delete_task(task_id: str):
    if task_id in tasks:
        del tasks[task_id]
        return {"message": "任务已删除", "task_id": task_id}
    else:
        raise HTTPException(status_code=404, detail="任务不存在")


@app.get("/api/v1/kling/credits")
async def get_credits():
    return {"user_id": "test", "credits": 100}


if __name__ == "__main__":
    print("启动可灵API测试服务器...")
    print("配置可灵API URL和Key后即可测试")
    uvicorn.run(app, host="0.0.0.0", port=8080)
