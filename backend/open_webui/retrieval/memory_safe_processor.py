"""
Memory-safe document processor for OpenWebUI
优化的文档处理器，解决大文件内存溢出问题
"""

import os
import gc
import uuid
import time
import hashlib
import logging
import psutil
import traceback
from typing import List, Optional, Dict, Any, Generator
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

log = logging.getLogger(__name__)


class MemoryMonitor:
    """内存监控器"""

    def __init__(self, max_memory_mb: int = 1000):
        self.max_memory_mb = max_memory_mb
        self.initial_memory = self.get_memory_usage()

    def get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        return psutil.Process().memory_info().rss / 1024 / 1024

    def check_memory(self) -> bool:
        """检查内存使用是否超限"""
        current = self.get_memory_usage()
        used = current - self.initial_memory

        if used > self.max_memory_mb:
            log.warning(f"Memory usage high: {used:.2f}MB / {self.max_memory_mb}MB")
            gc.collect()  # 尝试垃圾回收
            return False
        return True

    def get_usage_percent(self) -> float:
        """获取内存使用百分比"""
        current = self.get_memory_usage()
        used = current - self.initial_memory
        return (used / self.max_memory_mb) * 100


class SafeDocumentProcessor:
    """
    安全的文档处理器
    - 支持流式处理大文件
    - 内存使用监控和限制
    - 自动垃圾回收
    - 错误恢复机制
    """

    def __init__(
        self,
        max_memory_mb: int = 1000,
        chunk_size: int = 100,
        max_file_size_mb: int = 500,
        batch_size: int = 50,
    ):
        self.max_memory_mb = max_memory_mb
        self.chunk_size = chunk_size
        self.max_file_size_mb = max_file_size_mb
        self.batch_size = batch_size
        self.memory_monitor = None

    def process_documents(
        self,
        docs: List[Document],
        embedding_function,
        collection_name: str,
        vector_db_client,
        metadata: Optional[Dict] = None,
        user=None,
        progress_callback=None,
    ) -> bool:
        """
        安全地处理文档并存储到向量数据库

        Args:
            docs: 文档列表
            embedding_function: 嵌入函数
            collection_name: 集合名称
            vector_db_client: 向量数据库客户端
            metadata: 元数据
            user: 用户对象
            progress_callback: 进度回调函数

        Returns:
            bool: 处理是否成功
        """
        self.memory_monitor = MemoryMonitor(self.max_memory_mb)

        try:
            total_docs = len(docs)
            processed_count = 0
            failed_count = 0

            log.info(f"Starting to process {total_docs} documents")

            # 分批处理文档
            for batch_start in range(0, total_docs, self.batch_size):
                batch_end = min(batch_start + self.batch_size, total_docs)
                batch_docs = docs[batch_start:batch_end]

                # 检查内存
                if not self.memory_monitor.check_memory():
                    log.warning("Memory limit reached, running cleanup")
                    self._cleanup_memory()

                    # 再次检查
                    if not self.memory_monitor.check_memory():
                        raise MemoryError(
                            f"Memory usage exceeds {self.max_memory_mb}MB limit"
                        )

                try:
                    # 处理批次
                    success = self._process_batch(
                        batch_docs,
                        embedding_function,
                        collection_name,
                        vector_db_client,
                        metadata,
                        user,
                    )

                    if success:
                        processed_count += len(batch_docs)
                    else:
                        failed_count += len(batch_docs)

                except Exception as e:
                    log.error(f"Error processing batch {batch_start}-{batch_end}: {e}")
                    failed_count += len(batch_docs)

                # 更新进度
                if progress_callback:
                    progress = (batch_end / total_docs) * 100
                    progress_callback(
                        {
                            "progress": progress,
                            "processed": processed_count,
                            "failed": failed_count,
                            "total": total_docs,
                            "memory_usage": self.memory_monitor.get_usage_percent(),
                        }
                    )

                # 清理批次内存
                del batch_docs
                gc.collect()

            log.info(
                f"Document processing completed. Processed: {processed_count}, Failed: {failed_count}"
            )
            return failed_count == 0

        except Exception as e:
            log.error(f"Fatal error in document processing: {e}")
            log.error(traceback.format_exc())
            return False

        finally:
            # 最终清理
            self._cleanup_memory()

    def _process_batch(
        self,
        docs: List[Document],
        embedding_function,
        collection_name: str,
        vector_db_client,
        metadata: Optional[Dict] = None,
        user=None,
    ) -> bool:
        """处理一批文档"""
        try:
            # 提取文本内容
            texts = []
            for doc in docs:
                # 限制单个文档的大小
                text = doc.page_content
                if len(text) > 1000000:  # 1MB文本限制
                    text = text[:1000000]
                    log.warning(f"Truncated large document to 1MB")
                texts.append(text.replace("\n", " "))

            # 生成嵌入
            embeddings = embedding_function(texts, prefix="knowledge:", user=user)

            # 构建向量数据项
            items = []
            for idx, (text, doc) in enumerate(zip(texts, docs)):
                item = {
                    "id": str(uuid.uuid4()),
                    "text": text,
                    "vector": embeddings[idx],
                    "metadata": {
                        **doc.metadata,
                        **(metadata or {}),
                        "indexed_at": time.time(),
                        "doc_length": len(text),
                    },
                }
                items.append(item)

            # 批量插入到向量数据库
            vector_db_client.insert(collection_name=collection_name, items=items)

            # 清理临时变量
            del texts, embeddings, items

            return True

        except Exception as e:
            log.error(f"Error in _process_batch: {e}")
            return False

    def _cleanup_memory(self):
        """清理内存"""
        gc.collect()
        # Python 3.9+ 支持更激进的垃圾回收
        if hasattr(gc, "freeze"):
            gc.freeze()
            gc.collect()
            gc.unfreeze()

    def process_large_file(
        self,
        file_path: str,
        loader_class,
        text_splitter: RecursiveCharacterTextSplitter,
        **loader_kwargs,
    ) -> Generator[List[Document], None, None]:
        """
        流式处理大文件

        Yields:
            List[Document]: 文档块
        """
        # 检查文件大小
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        if file_size_mb > self.max_file_size_mb:
            raise ValueError(
                f"File too large: {file_size_mb:.2f}MB > {self.max_file_size_mb}MB"
            )

        log.info(f"Processing file: {file_path} ({file_size_mb:.2f}MB)")

        try:
            # 创建加载器实例
            loader = loader_class(file_path, **loader_kwargs)

            # 加载文档
            documents = loader.load()

            # 分割文档
            if text_splitter:
                split_docs = []
                for doc in documents:
                    # 流式分割大文档
                    if len(doc.page_content) > 100000:  # 100KB
                        # 分块处理大文档
                        chunks = self._split_large_text(doc.page_content, 50000)
                        for chunk in chunks:
                            temp_doc = Document(
                                page_content=chunk, metadata=doc.metadata.copy()
                            )
                            split_docs.extend(text_splitter.split_documents([temp_doc]))

                            # 每处理一定数量就yield出去
                            if len(split_docs) >= self.chunk_size:
                                yield split_docs
                                split_docs = []
                                gc.collect()
                    else:
                        split_docs.extend(text_splitter.split_documents([doc]))

                        if len(split_docs) >= self.chunk_size:
                            yield split_docs
                            split_docs = []
                            gc.collect()

                # Yield剩余的文档
                if split_docs:
                    yield split_docs
            else:
                # 不分割，直接分批yield
                for i in range(0, len(documents), self.chunk_size):
                    yield documents[i : i + self.chunk_size]
                    gc.collect()

        except Exception as e:
            log.error(f"Error processing large file: {e}")
            raise
        finally:
            # 清理内存
            self._cleanup_memory()

    def _split_large_text(self, text: str, chunk_size: int) -> List[str]:
        """将大文本分割成块"""
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i : i + chunk_size])
        return chunks


class QueryCache:
    """查询缓存管理器"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}

    def _generate_key(self, query: str, collection_names: List[str], k: int) -> str:
        """生成缓存键"""
        data = f"{query}:{','.join(sorted(collection_names))}:{k}"
        return hashlib.md5(data.encode()).hexdigest()

    def get(self, query: str, collection_names: List[str], k: int) -> Optional[Any]:
        """获取缓存结果"""
        key = self._generate_key(query, collection_names, k)

        if key in self.cache:
            # 检查是否过期
            if time.time() - self.access_times[key] < self.ttl_seconds:
                self.access_times[key] = time.time()  # 更新访问时间
                return self.cache[key]
            else:
                # 过期，删除
                del self.cache[key]
                del self.access_times[key]

        return None

    def set(self, query: str, collection_names: List[str], k: int, result: Any):
        """设置缓存结果"""
        # 检查缓存大小
        if len(self.cache) >= self.max_size:
            # LRU清理：删除最老的项
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]

        key = self._generate_key(query, collection_names, k)
        self.cache[key] = result
        self.access_times[key] = time.time()

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()

    def get_stats(self) -> Dict:
        """获取缓存统计"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "oldest_entry_age": (
                min([time.time() - t for t in self.access_times.values()], default=0)
                if self.access_times
                else 0
            ),
        }


class OptimizedQueryProcessor:
    """优化的查询处理器"""

    def __init__(
        self,
        max_workers: int = 4,
        query_timeout: int = 30,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
    ):
        self.max_workers = max_workers
        self.query_timeout = query_timeout
        self.enable_cache = enable_cache
        self.cache = QueryCache(ttl_seconds=cache_ttl) if enable_cache else None

    def query_collections(
        self,
        collection_names: List[str],
        queries: List[str],
        embedding_function,
        vector_db_client,
        k: int = 10,
        reranker=None,
        user=None,
    ) -> Dict:
        """
        优化的多集合查询

        Returns:
            Dict: 查询结果
        """
        results = []
        errors = []

        # 检查缓存
        if self.enable_cache:
            for query in queries:
                cached_result = self.cache.get(query, collection_names, k)
                if cached_result:
                    log.info(f"Cache hit for query: {query[:50]}...")
                    results.append(cached_result)
                    continue

        # 生成查询嵌入（批量处理）
        try:
            query_embeddings = embedding_function(queries, prefix="query:", user=user)
        except Exception as e:
            log.error(f"Error generating query embeddings: {e}")
            return {"results": [], "errors": [str(e)]}

        # 限制并发数
        actual_workers = min(
            self.max_workers, len(collection_names) * len(queries), 10  # 最大10个线程
        )

        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            futures = []

            for query_idx, (query, query_embedding) in enumerate(
                zip(queries, query_embeddings)
            ):
                for collection_name in collection_names:
                    future = executor.submit(
                        self._query_single_collection,
                        collection_name,
                        query,
                        query_embedding,
                        vector_db_client,
                        k,
                    )
                    futures.append((future, query, collection_name))

            # 收集结果
            for future, query, collection_name in futures:
                try:
                    result = future.result(timeout=self.query_timeout)
                    if result:
                        results.append(result)

                        # 缓存结果
                        if self.enable_cache:
                            self.cache.set(query, [collection_name], k, result)

                except TimeoutError:
                    error_msg = f"Query timeout for collection {collection_name}"
                    log.error(error_msg)
                    errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Query error for collection {collection_name}: {e}"
                    log.error(error_msg)
                    errors.append(error_msg)

        # 重排序（如果有reranker）
        if reranker and results:
            try:
                results = self._rerank_results(results, queries, reranker, k)
            except Exception as e:
                log.error(f"Reranking error: {e}")

        return {
            "results": results,
            "errors": errors,
            "cache_stats": self.cache.get_stats() if self.cache else None,
        }

    def _query_single_collection(
        self,
        collection_name: str,
        query: str,
        query_embedding: List[float],
        vector_db_client,
        k: int,
    ) -> Optional[Dict]:
        """查询单个集合"""
        try:
            result = vector_db_client.query(
                collection_name=collection_name, query_embedding=query_embedding, k=k
            )

            if result:
                return {
                    "collection": collection_name,
                    "query": query,
                    "documents": result.get("documents", []),
                    "scores": result.get("scores", []),
                    "metadata": result.get("metadata", []),
                }

            return None

        except Exception as e:
            log.error(f"Error querying collection {collection_name}: {e}")
            return None

    def _rerank_results(
        self, results: List[Dict], queries: List[str], reranker, k: int
    ) -> List[Dict]:
        """重排序结果"""
        # 实现重排序逻辑
        # 这里需要根据具体的reranker实现
        return results[:k]

    def clear_cache(self):
        """清空查询缓存"""
        if self.cache:
            self.cache.clear()
            log.info("Query cache cleared")


# 导出主要类
__all__ = [
    "SafeDocumentProcessor",
    "OptimizedQueryProcessor",
    "MemoryMonitor",
    "QueryCache",
]
