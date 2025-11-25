# syntax=docker/dockerfile:1
# Initialize device type args
# use build args in the docker build command with --build-arg="BUILDARG=true"
ARG USE_CUDA=false
ARG USE_OLLAMA=false
# Tested with cu117 for CUDA 11 and cu121 for CUDA 12 (default)
ARG USE_CUDA_VER=cu128
# any sentence transformer model; models to use can be found at https://huggingface.co/models?library=sentence-transformers
# Leaderboard: https://huggingface.co/spaces/mteb/leaderboard 
# for better performance and multilangauge support use "intfloat/multilingual-e5-large" (~2.5GB) or "intfloat/multilingual-e5-base" (~1.5GB)
# IMPORTANT: If you change the embedding model (sentence-transformers/all-MiniLM-L6-v2) and vice versa, you aren't able to use RAG Chat with your previous documents loaded in the WebUI! You need to re-embed them.
ARG USE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ARG USE_RERANKING_MODEL=""

# Tiktoken encoding name; models to use can be found at https://huggingface.co/models?library=tiktoken
ARG USE_TIKTOKEN_ENCODING_NAME="cl100k_base"

ARG BUILD_HASH=dev-build
# Override at your own risk - non-root configurations are untested
ARG UID=0
ARG GID=0

######## WebUI frontend ########
FROM --platform=$BUILDPLATFORM node:22-alpine3.20 AS build
ARG BUILD_HASH

WORKDIR /app

# 优化npm配置，减少缓存
RUN npm config set cache /tmp/npm-cache --global
RUN npm config set progress false --global
RUN npm config set fund false --global

COPY package.json package-lock.json ./
RUN npm ci --no-progress && rm -rf /tmp/npm-cache

COPY . .
ENV APP_BUILD_HASH=${BUILD_HASH}
RUN npm run build && rm -rf node_modules

######## WebUI backend ########
FROM python:3.11-slim-bookworm AS base

# Use args
ARG USE_CUDA
ARG USE_OLLAMA
ARG USE_CUDA_VER
ARG USE_EMBEDDING_MODEL
ARG USE_RERANKING_MODEL
ARG UID
ARG GID

## Basis ##
ENV ENV=prod \
    PORT=8080 \
    # pass build args to the build
    USE_OLLAMA_DOCKER=${USE_OLLAMA} \
    USE_CUDA_DOCKER=${USE_CUDA} \
    USE_CUDA_DOCKER_VER=${USE_CUDA_VER} \
    USE_EMBEDDING_MODEL_DOCKER=${USE_EMBEDDING_MODEL} \
    USE_RERANKING_MODEL_DOCKER=${USE_RERANKING_MODEL}

## Basis URL Config ##
ENV OLLAMA_BASE_URL="/ollama" \
    OPENAI_API_BASE_URL=""

## API Key and Security Config ##
ENV OPENAI_API_KEY="" \
    WEBUI_SECRET_KEY="" \
    SCARF_NO_ANALYTICS=true \
    DO_NOT_TRACK=true \
    ANONYMIZED_TELEMETRY=false

#### Other models #########################################################
## whisper TTS model settings ##
ENV WHISPER_MODEL="base" \
    WHISPER_MODEL_DIR="/app/backend/data/cache/whisper/models"

## RAG Embedding model settings ##
ENV RAG_EMBEDDING_MODEL="$USE_EMBEDDING_MODEL_DOCKER" \
    RAG_RERANKING_MODEL="$USE_RERANKING_MODEL_DOCKER" \
    SENTENCE_TRANSFORMERS_HOME="/app/backend/data/cache/embedding/models"

## Tiktoken model settings ##
ENV TIKTOKEN_ENCODING_NAME="cl100k_base" \
    TIKTOKEN_CACHE_DIR="/app/backend/data/cache/tiktoken"

## Hugging Face download cache ##
ENV HF_HOME="/app/backend/data/cache/embedding/models"

## Torch Extensions ##
# ENV TORCH_EXTENSIONS_DIR="/.cache/torch_extensions"

#### Other models ##########################################################

WORKDIR /app/backend

ENV HOME=/root
# Create user and group if not root
RUN if [ $UID -ne 0 ]; then \
    if [ $GID -ne 0 ]; then \
    addgroup --gid $GID app; \
    fi; \
    adduser --uid $UID --gid $GID --home $HOME --disabled-password --no-create-home app; \
    fi

RUN mkdir -p $HOME/.cache/chroma
RUN echo -n 00000000-0000-0000-0000-000000000000 > $HOME/.cache/chroma/telemetry_user_id

# 提前创建data目录，避免后续权限错误
RUN mkdir -p /app/backend/data/

# Make sure the user has access to the app and root directory
RUN chown -R $UID:$GID /app $HOME

# 优化apt-get安装，减少缓存
RUN apt-get update && \
    if [ "$USE_OLLAMA" = "true" ]; then \
    # Install pandoc and netcat
    apt-get install -y --no-install-recommends git build-essential pandoc netcat-openbsd curl gcc python3-dev ffmpeg libsm6 libxext6 jq && \
    # install ollama
    curl -fsSL https://ollama.com/install.sh | sh; \
    else \
    # Install pandoc, netcat and gcc
    apt-get install -y --no-install-recommends git build-essential pandoc gcc netcat-openbsd curl jq python3-dev ffmpeg libsm6 libxext6; \
    fi && \
    # 清理apt缓存
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# install python dependencies
COPY --chown=$UID:$GID ./backend/requirements.txt ./requirements.txt

# 优化pip安装，减少磁盘空间占用
RUN pip3 cache purge && rm -rf /root/.cache/pip/ && \
    # 设置pip配置，减少缓存
    pip3 config set global.cache-dir /tmp/pip-cache && \
    pip3 config set global.no-cache-dir true && \
    pip3 install --no-cache-dir pipdeptree && \
    if [ "$USE_CUDA" = "true" ]; then \
    # 安装CUDA版本的PyTorch
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/$USE_CUDA_DOCKER_VER --no-cache-dir && \
    pip3 install --no-cache-dir --force-reinstall -r requirements.txt; \
    else \
    # 安装CPU版本的PyTorch
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --no-cache-dir && \
    pip3 install --no-cache-dir --force-reinstall -r requirements.txt; \
    fi && \
    # 延迟模型下载，改为在首次运行时下载，减少构建时磁盘占用
    # 只下载tiktoken编码，因为它比较小
    python -c "import os; import tiktoken; tiktoken.get_encoding(os.environ['TIKTOKEN_ENCODING_NAME'])" && \
    # 清理pip缓存和临时文件
    rm -rf /tmp/pip-cache /tmp/* /var/tmp/* && \
    chown -R $UID:$GID /app/backend/data/

# copy built frontend files
COPY --chown=$UID:$GID --from=build /app/build /app/build
COPY --chown=$UID:$GID --from=build /app/CHANGELOG.md /app/CHANGELOG.md
COPY --chown=$UID:$GID --from=build /app/CHANGELOG_EXTRA.md /app/CHANGELOG_EXTRA.md
COPY --chown=$UID:$GID --from=build /app/package.json /app/package.json

# copy backend files
COPY --chown=$UID:$GID ./backend .

EXPOSE 8080

HEALTHCHECK CMD curl --silent --fail http://localhost:${PORT:-8080}/health | jq -ne 'input.status == true' || exit 1

USER $UID:$GID

ARG BUILD_HASH
ENV WEBUI_BUILD_VERSION=${BUILD_HASH}
ENV DOCKER=true

CMD [ "bash", "start.sh"]
