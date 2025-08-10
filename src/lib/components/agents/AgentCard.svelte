<script>
	import { createEventDispatcher } from 'svelte';

	export let app;
	export let isFavorited = false;
	export let size = 'normal'; // normal, compact

	const dispatch = createEventDispatcher();

	const handleFavorite = (e) => {
		e.stopPropagation();
		dispatch('favorite', app);
	};

	const handleUse = () => {
		dispatch('use', app);
	};

	const formatCreatedTime = (timestamp) => {
		try {
			const date = new Date(timestamp);
			const now = new Date();
			const diffInMs = now - date;
			const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

			if (diffInDays === 0) return '今天创建';
			if (diffInDays === 1) return '昨天创建';
			if (diffInDays < 7) return `${diffInDays}天前创建`;
			if (diffInDays < 30) return `${Math.floor(diffInDays / 7)}周前创建`;
			return `${Math.floor(diffInDays / 30)}个月前创建`;
		} catch {
			return '';
		}
	};

	// 获取分类显示信息
	const getCategoryInfo = (category) => {
		const categoryMap = {
			general: { name: '通用', color: '#6b7280', bg: '#f3f4f6' },
			productivity: { name: '效率', color: '#059669', bg: '#d1fae5' },
			creative: { name: '创意', color: '#dc2626', bg: '#fee2e2' },
			analysis: { name: '分析', color: '#2563eb', bg: '#dbeafe' }
		};
		return categoryMap[category] || { name: category, color: '#6b7280', bg: '#f3f4f6' };
	};

	$: categoryInfo = getCategoryInfo(app.category);
</script>

<div
	class="agent-card {size}"
	on:click={handleUse}
	on:keydown={handleUse}
	role="button"
	tabindex="0"
>
	<div class="card-main">
		<!-- 左侧图标 -->
		<div class="app-icon">
			{app.icon || '🤖'}
		</div>

		<!-- 右侧内容 -->
		<div class="app-content">
			<!-- 标题和收藏按钮 -->
			<div class="app-header">
				<h3 class="app-title">{app.display_name}</h3>
				<button
					class="favorite-btn {isFavorited ? 'favorited' : ''}"
					on:click={handleFavorite}
					title={isFavorited ? '取消收藏' : '收藏'}
				>
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none">
						<path
							d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
							fill={isFavorited ? '#ef4444' : 'none'}
							stroke={isFavorited ? '#ef4444' : 'currentColor'}
							stroke-width="2"
						/>
					</svg>
				</button>
			</div>

			<!-- 分类标签 -->
			<div
				class="app-category"
				style="color: {categoryInfo.color}; background-color: {categoryInfo.bg};"
			>
				{categoryInfo.name}
			</div>

			<!-- 描述 -->
			<p class="app-description">
				{app.description || '暂无描述'}
			</p>

			<!-- 底部信息 -->
			<div class="card-footer">
				<!-- 统计信息 -->
				<div class="app-stats">
					<div class="stat-item">
						<span class="stat-icon">👥</span>
						<span class="stat-text">{app.usage_count || 0} 次使用</span>
					</div>
					<div class="stat-item">
						<span class="stat-icon">⭐</span>
						<span class="stat-text">{app.favorite_count || 0} 收藏</span>
					</div>
				</div>

				<!-- 创建时间 -->
				<div class="created-info">
					<span class="created-text">
						{formatCreatedTime(app.created_at)}
					</span>
				</div>
			</div>
		</div>
	</div>

	<!-- 使用按钮 -->
	<button class="use-btn">
		<span>立即使用</span>
		<svg width="14" height="14" viewBox="0 0 24 24" fill="none">
			<path
				d="M5 12h14m-7-7l7 7-7 7"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
		</svg>
	</button>
</div>

<style>
	.agent-card {
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		transition: all 0.2s ease;
		cursor: pointer;
		display: flex;
		flex-direction: column;
		height: auto;
		overflow: hidden;
		border: 1px solid #e5e7eb;
		touch-action: manipulation;
		position: relative;
	}

	.card-main {
		display: flex;
		padding: 0.75rem;
		gap: 0.75rem;
		flex: 1;
	}

	/* 左侧图标 */
	.app-icon {
		font-size: 2rem;
		flex-shrink: 0;
		line-height: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 3rem;
		height: 3rem;
		background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
		border-radius: 0.5rem;
	}

	/* 右侧内容区域 */
	.app-content {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	/* 标题和收藏按钮 */
	.app-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 0.5rem;
	}

	.app-title {
		font-size: 0.875rem;
		font-weight: 600;
		color: #1f2937;
		margin: 0;
		line-height: 1.3;
		display: -webkit-box;
		-webkit-line-clamp: 1;
		-webkit-box-orient: vertical;
		overflow: hidden;
		flex: 1;
	}

	.favorite-btn {
		flex-shrink: 0;
		width: 1.5rem;
		height: 1.5rem;
		border-radius: 50%;
		border: none;
		background: transparent;
		color: #6b7280;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
		cursor: pointer;
	}

	.favorite-btn:hover {
		background: #f3f4f6;
		color: #374151;
	}

	.favorite-btn.favorited {
		color: #ef4444;
	}

	/* 分类标签 */
	.app-category {
		display: inline-flex;
		align-items: center;
		padding: 0.125rem 0.5rem;
		border-radius: 0.75rem;
		font-size: 0.6rem;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.025em;
		width: fit-content;
	}

	/* 描述文本 */
	.app-description {
		color: #6b7280;
		font-size: 0.75rem;
		line-height: 1.4;
		margin: 0;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		flex: 1;
	}

	/* 底部信息 */
	.card-footer {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 0.5rem;
		margin-top: 0.25rem;
	}

	.app-stats {
		display: flex;
		gap: 0.75rem;
		flex: 1;
	}

	.stat-item {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		color: #6b7280;
		font-size: 0.65rem;
	}

	.stat-icon {
		font-size: 0.7rem;
	}

	.created-info {
		flex-shrink: 0;
	}

	.created-text {
		color: #9ca3af;
		font-size: 0.6rem;
		font-weight: 400;
	}

	/* 使用按钮 */
	.use-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.375rem;
		padding: 0.5rem 0.75rem;
		border-radius: 0 0 0.75rem 0.75rem;
		border: none;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		font-size: 0.75rem;
		font-weight: 500;
		transition: all 0.2s ease;
		cursor: pointer;
		width: 100%;
		border-top: 1px solid #e5e7eb;
	}

	.use-btn:hover {
		background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
	}

	/* Dark mode support */
	:global(.dark) .agent-card {
		background: #1f2937;
		border-color: #374151;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
	}

	:global(.dark) .app-title {
		color: #f9fafb;
	}

	:global(.dark) .use-btn {
		border-top-color: #374151;
	}

	.agent-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		border-color: #d1d5db;
	}

	/* 移动端响应式 */
	@media (max-width: 768px) {
		.agent-card {
			max-width: 100% !important;
			width: 100% !important;
			overflow: hidden !important;
			box-sizing: border-box !important;
		}

		.card-main {
			padding: 0.625rem;
			gap: 0.625rem;
			max-width: 100% !important;
			overflow: hidden !important;
		}

		.app-icon {
			width: 2.5rem;
			height: 2.5rem;
			font-size: 1.75rem;
			flex-shrink: 0 !important;
		}

		.app-content {
			min-width: 0 !important;
			overflow: hidden !important;
		}

		.app-title {
			font-size: 0.8rem;
			overflow: hidden !important;
		}

		.app-description {
			font-size: 0.7rem;
			overflow: hidden !important;
		}

		.app-stats {
			flex-wrap: wrap !important;
			overflow: hidden !important;
		}

		.stat-item {
			font-size: 0.6rem;
			white-space: nowrap !important;
		}

		.created-text {
			font-size: 0.55rem;
			white-space: nowrap !important;
		}

		.use-btn {
			padding: 0.4rem 0.6rem;
			font-size: 0.7rem;
			overflow: hidden !important;
		}
	}
</style>
