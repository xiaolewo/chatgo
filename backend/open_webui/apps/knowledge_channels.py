"""
Knowledge Acquisition Channels for OpenWebUI
多渠道知识获取系统，支持RSS、API、社交媒体等数据源
"""

import json
import time
import uuid
import asyncio
import hashlib
import logging
import feedparser
import aiohttp
import requests
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum

from langchain.docstore.document import Document
from sqlalchemy import Column, String, BigInteger, Boolean, Text, Integer, JSON
from open_webui.internal.db import Base, get_db

log = logging.getLogger(__name__)


# ========== 枚举和数据类 ==========


class ChannelType(Enum):
    """渠道类型枚举"""

    RSS = "rss"
    API = "api"
    WEBHOOK = "webhook"
    SOCIAL_MEDIA = "social_media"
    CLOUD_STORAGE = "cloud_storage"
    DATABASE = "database"
    WEB_SCRAPER = "web_scraper"
    EMAIL = "email"


class ChannelStatus(Enum):
    """渠道状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SYNCING = "syncing"
    PAUSED = "paused"


@dataclass
class ChannelConfig:
    """渠道配置数据类"""

    channel_id: str
    name: str
    type: ChannelType
    config: Dict[str, Any]
    schedule: Optional[str] = None  # Cron表达式
    enabled: bool = True
    auto_index: bool = True
    filters: Optional[Dict] = None
    metadata: Optional[Dict] = None


@dataclass
class FetchResult:
    """数据获取结果"""

    success: bool
    documents: List[Document]
    error: Optional[str] = None
    metadata: Optional[Dict] = None
    next_cursor: Optional[str] = None  # 用于分页


# ========== 数据库模型 ==========


class KnowledgeChannel(Base):
    """知识获取渠道表"""

    __tablename__ = "knowledge_channel"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    config = Column(JSON, default={})
    schedule = Column(String)  # Cron表达式
    enabled = Column(Boolean, default=True)
    auto_index = Column(Boolean, default=True)
    filters = Column(JSON, default={})
    status = Column(String, default=ChannelStatus.INACTIVE.value)
    last_sync = Column(BigInteger)
    next_sync = Column(BigInteger)
    sync_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    metadata = Column(JSON, default={})
    created_by = Column(String)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    updated_at = Column(BigInteger, default=lambda: int(time.time()))


class ChannelSyncLog(Base):
    """渠道同步日志表"""

    __tablename__ = "channel_sync_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    channel_id = Column(String, nullable=False, index=True)
    sync_start = Column(BigInteger, nullable=False)
    sync_end = Column(BigInteger)
    status = Column(String, nullable=False)  # 'success', 'partial', 'failed'
    documents_fetched = Column(Integer, default=0)
    documents_indexed = Column(Integer, default=0)
    error_message = Column(Text)
    metadata = Column(JSON, default={})


# ========== 基础渠道类 ==========


class BaseChannel(ABC):
    """渠道基类"""

    def __init__(self, config: ChannelConfig):
        self.config = config
        self.channel_id = config.channel_id
        self.name = config.name

    @abstractmethod
    async def fetch(self, **kwargs) -> FetchResult:
        """获取数据"""
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """验证渠道配置"""
        pass

    def apply_filters(self, documents: List[Document]) -> List[Document]:
        """应用过滤器"""
        if not self.config.filters:
            return documents

        filtered = []
        for doc in documents:
            if self._check_filters(doc):
                filtered.append(doc)

        return filtered

    def _check_filters(self, doc: Document) -> bool:
        """检查文档是否符合过滤条件"""
        filters = self.config.filters

        # 关键词过滤
        if "keywords" in filters:
            keywords = filters["keywords"]
            content = doc.page_content.lower()
            if not any(kw.lower() in content for kw in keywords):
                return False

        # 排除词过滤
        if "exclude_keywords" in filters:
            exclude_keywords = filters["exclude_keywords"]
            content = doc.page_content.lower()
            if any(kw.lower() in content for kw in exclude_keywords):
                return False

        # 日期过滤
        if "date_after" in filters:
            doc_date = doc.metadata.get("date")
            if doc_date and doc_date < filters["date_after"]:
                return False

        # 长度过滤
        if "min_length" in filters:
            if len(doc.page_content) < filters["min_length"]:
                return False

        if "max_length" in filters:
            if len(doc.page_content) > filters["max_length"]:
                return False

        return True


# ========== RSS渠道 ==========


class RSSChannel(BaseChannel):
    """RSS订阅渠道"""

    async def fetch(self, limit: int = 50, **kwargs) -> FetchResult:
        """从RSS源获取内容"""
        try:
            feed_url = self.config.config.get("feed_url")
            if not feed_url:
                return FetchResult(False, [], error="No feed URL configured")

            # 解析RSS
            feed = await self._fetch_feed(feed_url)

            documents = []
            for entry in feed.entries[:limit]:
                # 创建文档
                content = self._extract_content(entry)
                metadata = {
                    "source": "rss",
                    "channel_id": self.channel_id,
                    "channel_name": self.name,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "author": entry.get("author", ""),
                    "tags": [tag.term for tag in entry.get("tags", [])],
                }

                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)

            # 应用过滤器
            documents = self.apply_filters(documents)

            return FetchResult(
                success=True,
                documents=documents,
                metadata={"feed_title": feed.feed.get("title", "")},
            )

        except Exception as e:
            log.error(f"Error fetching RSS feed: {e}")
            return FetchResult(False, [], error=str(e))

    async def _fetch_feed(self, url: str) -> Any:
        """异步获取RSS内容"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, feedparser.parse, url)

    def _extract_content(self, entry: Any) -> str:
        """提取文章内容"""
        content_parts = []

        # 标题
        if entry.get("title"):
            content_parts.append(f"# {entry.title}\n")

        # 摘要
        if entry.get("summary"):
            content_parts.append(entry.summary)

        # 全文内容
        if hasattr(entry, "content"):
            for content in entry.content:
                if content.get("value"):
                    content_parts.append(content["value"])

        return "\n\n".join(content_parts)

    async def validate(self) -> bool:
        """验证RSS源"""
        try:
            feed_url = self.config.config.get("feed_url")
            if not feed_url:
                return False

            feed = await self._fetch_feed(feed_url)
            return len(feed.entries) > 0

        except Exception as e:
            log.error(f"RSS validation failed: {e}")
            return False


# ========== API渠道 ==========


class APIChannel(BaseChannel):
    """API数据源渠道"""

    async def fetch(self, **kwargs) -> FetchResult:
        """从API获取数据"""
        try:
            api_config = self.config.config
            url = api_config.get("url")
            method = api_config.get("method", "GET")
            headers = api_config.get("headers", {})
            params = api_config.get("params", {})
            body = api_config.get("body", {})

            # 支持分页
            page = kwargs.get("page", 1)
            if api_config.get("pagination"):
                page_param = api_config["pagination"].get("page_param", "page")
                params[page_param] = page

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=body if method in ["POST", "PUT"] else None,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status != 200:
                        return FetchResult(
                            False, [], error=f"API returned {response.status}"
                        )

                    data = await response.json()

                    # 解析响应
                    documents = self._parse_api_response(data, api_config)

                    # 检查是否有更多数据
                    next_cursor = None
                    if api_config.get("pagination"):
                        next_page_path = api_config["pagination"].get("next_page_path")
                        if next_page_path:
                            next_cursor = self._get_nested_value(data, next_page_path)

                    return FetchResult(
                        success=True, documents=documents, next_cursor=next_cursor
                    )

        except Exception as e:
            log.error(f"Error fetching from API: {e}")
            return FetchResult(False, [], error=str(e))

    def _parse_api_response(self, data: Any, config: Dict) -> List[Document]:
        """解析API响应"""
        documents = []

        # 获取数据列表路径
        data_path = config.get("data_path", "")
        if data_path:
            items = self._get_nested_value(data, data_path)
        else:
            items = data if isinstance(data, list) else [data]

        # 字段映射
        field_mapping = config.get("field_mapping", {})

        for item in items:
            # 提取内容
            content_fields = field_mapping.get(
                "content", ["content", "text", "description"]
            )
            content_parts = []
            for field in content_fields:
                value = self._get_nested_value(item, field)
                if value:
                    content_parts.append(str(value))

            if not content_parts:
                continue

            # 提取元数据
            metadata = {
                "source": "api",
                "channel_id": self.channel_id,
                "channel_name": self.name,
                "api_url": config.get("url"),
            }

            # 添加映射的元数据字段
            metadata_mapping = field_mapping.get("metadata", {})
            for meta_key, item_path in metadata_mapping.items():
                value = self._get_nested_value(item, item_path)
                if value:
                    metadata[meta_key] = value

            doc = Document(page_content="\n\n".join(content_parts), metadata=metadata)
            documents.append(doc)

        return self.apply_filters(documents)

    def _get_nested_value(self, data: Any, path: str) -> Any:
        """获取嵌套数据值"""
        if not path:
            return data

        keys = path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                index = int(key)
                if index < len(value):
                    value = value[index]
                else:
                    return None
            else:
                return None

            if value is None:
                return None

        return value

    async def validate(self) -> bool:
        """验证API配置"""
        try:
            result = await self.fetch()
            return result.success
        except:
            return False


# ========== 社交媒体渠道 ==========


class SocialMediaChannel(BaseChannel):
    """社交媒体渠道"""

    async def fetch(self, **kwargs) -> FetchResult:
        """从社交媒体获取内容"""
        platform = self.config.config.get("platform")

        if platform == "twitter":
            return await self._fetch_twitter()
        elif platform == "reddit":
            return await self._fetch_reddit()
        else:
            return FetchResult(False, [], error=f"Unsupported platform: {platform}")

    async def _fetch_twitter(self) -> FetchResult:
        """获取Twitter内容"""
        # 需要Twitter API凭证
        api_key = self.config.config.get("api_key")
        api_secret = self.config.config.get("api_secret")

        if not api_key or not api_secret:
            return FetchResult(False, [], error="Twitter API credentials required")

        # TODO: 实现Twitter API调用
        # 这里需要使用tweepy或其他Twitter客户端库

        return FetchResult(True, [], metadata={"platform": "twitter"})

    async def _fetch_reddit(self) -> FetchResult:
        """获取Reddit内容"""
        subreddit = self.config.config.get("subreddit")
        sort = self.config.config.get("sort", "hot")
        limit = self.config.config.get("limit", 25)

        if not subreddit:
            return FetchResult(False, [], error="Subreddit required")

        try:
            url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
            headers = {"User-Agent": "OpenWebUI Knowledge Bot 1.0"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, params={"limit": limit}
                ) as response:
                    if response.status != 200:
                        return FetchResult(
                            False, [], error=f"Reddit API returned {response.status}"
                        )

                    data = await response.json()
                    documents = self._parse_reddit_response(data)

                    return FetchResult(
                        success=True,
                        documents=documents,
                        metadata={"subreddit": subreddit, "sort": sort},
                    )

        except Exception as e:
            log.error(f"Error fetching from Reddit: {e}")
            return FetchResult(False, [], error=str(e))

    def _parse_reddit_response(self, data: Dict) -> List[Document]:
        """解析Reddit响应"""
        documents = []

        posts = data.get("data", {}).get("children", [])
        for post in posts:
            post_data = post.get("data", {})

            # 构建内容
            content_parts = []
            if post_data.get("title"):
                content_parts.append(f"# {post_data['title']}\n")
            if post_data.get("selftext"):
                content_parts.append(post_data["selftext"])

            if not content_parts:
                continue

            # 元数据
            metadata = {
                "source": "reddit",
                "channel_id": self.channel_id,
                "channel_name": self.name,
                "subreddit": post_data.get("subreddit"),
                "author": post_data.get("author"),
                "score": post_data.get("score"),
                "url": f"https://reddit.com{post_data.get('permalink', '')}",
                "created_utc": post_data.get("created_utc"),
                "num_comments": post_data.get("num_comments", 0),
            }

            doc = Document(page_content="\n\n".join(content_parts), metadata=metadata)
            documents.append(doc)

        return self.apply_filters(documents)

    async def validate(self) -> bool:
        """验证社交媒体配置"""
        platform = self.config.config.get("platform")

        if platform == "twitter":
            return bool(self.config.config.get("api_key"))
        elif platform == "reddit":
            return bool(self.config.config.get("subreddit"))

        return False


# ========== 云存储渠道 ==========


class CloudStorageChannel(BaseChannel):
    """云存储渠道（Google Drive, OneDrive, SharePoint等）"""

    async def fetch(self, **kwargs) -> FetchResult:
        """从云存储获取文档"""
        provider = self.config.config.get("provider")

        if provider == "google_drive":
            return await self._fetch_google_drive()
        elif provider == "onedrive":
            return await self._fetch_onedrive()
        elif provider == "sharepoint":
            return await self._fetch_sharepoint()
        else:
            return FetchResult(False, [], error=f"Unsupported provider: {provider}")

    async def _fetch_google_drive(self) -> FetchResult:
        """从Google Drive获取文档"""
        # 需要Google Drive API凭证
        credentials = self.config.config.get("credentials")
        folder_id = self.config.config.get("folder_id")

        if not credentials:
            return FetchResult(False, [], error="Google Drive credentials required")

        # TODO: 实现Google Drive API调用
        # 使用google-api-python-client库

        return FetchResult(True, [], metadata={"provider": "google_drive"})

    async def _fetch_onedrive(self) -> FetchResult:
        """从OneDrive获取文档"""
        # 需要Microsoft Graph API凭证
        client_id = self.config.config.get("client_id")
        client_secret = self.config.config.get("client_secret")
        tenant_id = self.config.config.get("tenant_id")

        if not all([client_id, client_secret, tenant_id]):
            return FetchResult(False, [], error="OneDrive credentials required")

        # TODO: 实现Microsoft Graph API调用

        return FetchResult(True, [], metadata={"provider": "onedrive"})

    async def _fetch_sharepoint(self) -> FetchResult:
        """从SharePoint获取文档"""
        # SharePoint配置
        site_url = self.config.config.get("site_url")
        username = self.config.config.get("username")
        password = self.config.config.get("password")

        if not all([site_url, username, password]):
            return FetchResult(False, [], error="SharePoint credentials required")

        # TODO: 实现SharePoint API调用
        # 使用Office365-REST-Python-Client库

        return FetchResult(True, [], metadata={"provider": "sharepoint"})

    async def validate(self) -> bool:
        """验证云存储配置"""
        provider = self.config.config.get("provider")

        if provider == "google_drive":
            return bool(self.config.config.get("credentials"))
        elif provider == "onedrive":
            return all(
                [
                    self.config.config.get("client_id"),
                    self.config.config.get("client_secret"),
                    self.config.config.get("tenant_id"),
                ]
            )
        elif provider == "sharepoint":
            return all(
                [
                    self.config.config.get("site_url"),
                    self.config.config.get("username"),
                    self.config.config.get("password"),
                ]
            )

        return False


# ========== Webhook渠道 ==========


class WebhookChannel(BaseChannel):
    """Webhook接收渠道"""

    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.pending_documents = []

    async def fetch(self, **kwargs) -> FetchResult:
        """获取待处理的webhook数据"""
        # Webhook是被动接收，返回缓存的文档
        documents = self.pending_documents.copy()
        self.pending_documents.clear()

        return FetchResult(
            success=True,
            documents=documents,
            metadata={"webhook_url": self.get_webhook_url()},
        )

    def receive_webhook(self, data: Dict) -> bool:
        """接收webhook数据"""
        try:
            # 解析webhook数据
            content = self._parse_webhook_data(data)

            if content:
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": "webhook",
                        "channel_id": self.channel_id,
                        "channel_name": self.name,
                        "received_at": int(time.time()),
                        "webhook_data": data,
                    },
                )

                self.pending_documents.append(doc)
                return True

            return False

        except Exception as e:
            log.error(f"Error processing webhook data: {e}")
            return False

    def _parse_webhook_data(self, data: Dict) -> str:
        """解析webhook数据"""
        # 根据配置提取内容
        content_path = self.config.config.get("content_path", "content")
        content = self._extract_value(data, content_path)

        if not content:
            # 尝试常见字段
            content = (
                data.get("content")
                or data.get("text")
                or data.get("message")
                or str(data)
            )

        return content

    def _extract_value(self, data: Dict, path: str) -> Any:
        """从嵌套数据中提取值"""
        keys = path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

            if value is None:
                return None

        return value

    def get_webhook_url(self) -> str:
        """获取webhook URL"""
        # 生成唯一的webhook URL
        base_url = self.config.config.get("base_url", "http://localhost:8000")
        return f"{base_url}/api/v1/knowledge/channels/{self.channel_id}/webhook"

    async def validate(self) -> bool:
        """验证webhook配置"""
        return True  # Webhook总是有效的


# ========== 渠道管理器 ==========


class ChannelManager:
    """渠道管理器"""

    def __init__(self):
        self.channels = {}
        self.channel_classes = {
            ChannelType.RSS: RSSChannel,
            ChannelType.API: APIChannel,
            ChannelType.SOCIAL_MEDIA: SocialMediaChannel,
            ChannelType.CLOUD_STORAGE: CloudStorageChannel,
            ChannelType.WEBHOOK: WebhookChannel,
        }

    def create_channel(self, config: ChannelConfig) -> Optional[BaseChannel]:
        """创建渠道实例"""
        channel_class = self.channel_classes.get(config.type)

        if not channel_class:
            log.error(f"Unsupported channel type: {config.type}")
            return None

        try:
            channel = channel_class(config)
            self.channels[config.channel_id] = channel
            return channel

        except Exception as e:
            log.error(f"Error creating channel: {e}")
            return None

    def get_channel(self, channel_id: str) -> Optional[BaseChannel]:
        """获取渠道实例"""
        return self.channels.get(channel_id)

    async def sync_channel(self, channel_id: str) -> Dict:
        """同步渠道数据"""
        channel = self.get_channel(channel_id)
        if not channel:
            return {"success": False, "error": "Channel not found"}

        sync_log_id = None

        try:
            # 记录同步开始
            with get_db() as db:
                sync_log = ChannelSyncLog(
                    channel_id=channel_id, sync_start=int(time.time()), status="running"
                )
                db.add(sync_log)
                db.commit()
                sync_log_id = sync_log.id

            # 获取数据
            result = await channel.fetch()

            if result.success:
                # TODO: 将文档索引到知识库
                # 这里需要调用知识库的索引功能

                # 更新同步日志
                with get_db() as db:
                    sync_log = (
                        db.query(ChannelSyncLog)
                        .filter(ChannelSyncLog.id == sync_log_id)
                        .first()
                    )

                    if sync_log:
                        sync_log.sync_end = int(time.time())
                        sync_log.status = "success"
                        sync_log.documents_fetched = len(result.documents)
                        sync_log.documents_indexed = len(
                            result.documents
                        )  # TODO: 实际索引数量
                        sync_log.metadata = result.metadata
                        db.commit()

                # 更新渠道状态
                self._update_channel_status(
                    channel_id, ChannelStatus.ACTIVE, sync_count_increment=1
                )

                return {
                    "success": True,
                    "documents_count": len(result.documents),
                    "metadata": result.metadata,
                }
            else:
                # 记录错误
                with get_db() as db:
                    sync_log = (
                        db.query(ChannelSyncLog)
                        .filter(ChannelSyncLog.id == sync_log_id)
                        .first()
                    )

                    if sync_log:
                        sync_log.sync_end = int(time.time())
                        sync_log.status = "failed"
                        sync_log.error_message = result.error
                        db.commit()

                # 更新渠道状态
                self._update_channel_status(
                    channel_id,
                    ChannelStatus.ERROR,
                    error_count_increment=1,
                    last_error=result.error,
                )

                return {"success": False, "error": result.error}

        except Exception as e:
            log.error(f"Error syncing channel {channel_id}: {e}")

            # 更新错误状态
            if sync_log_id:
                with get_db() as db:
                    sync_log = (
                        db.query(ChannelSyncLog)
                        .filter(ChannelSyncLog.id == sync_log_id)
                        .first()
                    )

                    if sync_log:
                        sync_log.sync_end = int(time.time())
                        sync_log.status = "failed"
                        sync_log.error_message = str(e)
                        db.commit()

            self._update_channel_status(
                channel_id,
                ChannelStatus.ERROR,
                error_count_increment=1,
                last_error=str(e),
            )

            return {"success": False, "error": str(e)}

    def _update_channel_status(
        self,
        channel_id: str,
        status: ChannelStatus,
        sync_count_increment: int = 0,
        error_count_increment: int = 0,
        last_error: Optional[str] = None,
    ):
        """更新渠道状态"""
        try:
            with get_db() as db:
                channel = (
                    db.query(KnowledgeChannel)
                    .filter(KnowledgeChannel.id == channel_id)
                    .first()
                )

                if channel:
                    channel.status = status.value
                    channel.last_sync = int(time.time())
                    channel.updated_at = int(time.time())

                    if sync_count_increment:
                        channel.sync_count += sync_count_increment

                    if error_count_increment:
                        channel.error_count += error_count_increment

                    if last_error:
                        channel.last_error = last_error

                    db.commit()

        except Exception as e:
            log.error(f"Error updating channel status: {e}")

    async def validate_channel(self, channel_id: str) -> bool:
        """验证渠道配置"""
        channel = self.get_channel(channel_id)
        if not channel:
            return False

        return await channel.validate()


# 导出主要类
__all__ = [
    "ChannelType",
    "ChannelStatus",
    "ChannelConfig",
    "FetchResult",
    "BaseChannel",
    "RSSChannel",
    "APIChannel",
    "SocialMediaChannel",
    "CloudStorageChannel",
    "WebhookChannel",
    "ChannelManager",
    "KnowledgeChannel",
    "ChannelSyncLog",
]
