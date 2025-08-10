<script>
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { getAgentApps, toggleFavoriteApp } from '$lib/apis/agents';
	import { user, showSidebar, mobile } from '$lib/stores';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import AgentCard from './AgentCard.svelte';
	import SearchInput from '$lib/components/layout/Sidebar/SearchInput.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';

	const i18n = getContext('i18n');

	let apps = [];
	let filteredApps = [];
	let categories = ['all', 'general', 'productivity', 'creative', 'analysis'];
	let selectedCategory = 'all';
	let searchQuery = '';
	let loading = false;
	let favoriteApps = new Set();

	// 分页相关
	let currentPage = 1;
	let hasMore = true;
	const pageSize = 12;

	onMount(async () => {
		await loadApps();
	});

	const loadApps = async (page = 1, append = false) => {
		if (loading) return;

		loading = true;

		try {
			// 临时模拟数据，替换为真实API调用
			const mockApps = [
				{
					id: 'app-1',
					display_name: '文档总结助手',
					description: '帮助您快速总结长篇文档内容，提取关键信息',
					category: 'productivity',
					icon: '📄',
					favorite_count: 15,
					usage_count: 120,
					created_at: Date.now(),
					status: 'active'
				},
				{
					id: 'app-2',
					display_name: '创意写作工具',
					description: '激发创意灵感，协助您创作小说、诗歌等文学作品',
					category: 'creative',
					icon: '✍️',
					favorite_count: 28,
					usage_count: 85,
					created_at: Date.now(),
					status: 'active'
				},
				{
					id: 'app-3',
					display_name: '数据分析师',
					description: '分析数据趋势，生成可视化图表和深度分析报告',
					category: 'analysis',
					icon: '📊',
					favorite_count: 42,
					usage_count: 200,
					created_at: Date.now(),
					status: 'active'
				},
				{
					id: 'app-4',
					display_name: '教案生成助手',
					description: '根据学科、阶段、教材等信息，智能生成专业的教案内容',
					category: 'productivity',
					icon: '📚',
					favorite_count: 35,
					usage_count: 168,
					created_at: Date.now(),
					status: 'active'
				}
			];

			// 模拟API响应
			const response = {
				apps: mockApps
					.filter((app) => {
						if (selectedCategory !== 'all' && app.category !== selectedCategory) return false;
						if (searchQuery) {
							const query = searchQuery.toLowerCase();
							return (
								app.display_name.toLowerCase().includes(query) ||
								app.description.toLowerCase().includes(query)
							);
						}
						return true;
					})
					.slice((page - 1) * pageSize, page * pageSize),
				user_favorites: ['app-2'], // 模拟用户收藏
				total: mockApps.length,
				page: page,
				limit: pageSize
			};

			if (response && response.apps) {
				if (append) {
					apps = [...apps, ...response.apps];
				} else {
					apps = response.apps;
				}

				favoriteApps = new Set(response.user_favorites || []);
				hasMore = false; // 模拟数据没有更多页面
				currentPage = page;

				filterApps();
			}
		} catch (error) {
			console.error('Failed to load apps:', error);
			toast.error('暂时无法加载智能体应用，请稍后重试');
		} finally {
			loading = false;
		}
	};

	const filterApps = () => {
		filteredApps = apps.filter((app) => {
			if (selectedCategory !== 'all' && app.category !== selectedCategory) {
				return false;
			}
			if (searchQuery) {
				const query = searchQuery.toLowerCase();
				return (
					app.display_name.toLowerCase().includes(query) ||
					app.description.toLowerCase().includes(query)
				);
			}
			return true;
		});
	};

	const handleCategoryChange = async (category) => {
		selectedCategory = category;
		currentPage = 1;
		await loadApps();
	};

	const handleSearch = async (query) => {
		searchQuery = query;
		currentPage = 1;
		// 重新过滤当前数据而不是重新加载
		filterApps();
	};

	const handleToggleFavorite = async (app) => {
		try {
			// 模拟切换收藏状态
			const isFavorited = favoriteApps.has(app.id);

			if (isFavorited) {
				favoriteApps.delete(app.id);
				toast.success('已移除收藏');
			} else {
				favoriteApps.add(app.id);
				toast.success('已添加到收藏');
			}

			// 触发响应式更新
			favoriteApps = favoriteApps;

			// 更新应用的收藏数
			const appIndex = apps.findIndex((a) => a.id === app.id);
			if (appIndex >= 0) {
				apps[appIndex].favorite_count += isFavorited ? -1 : 1;
				apps = apps;
			}
		} catch (error) {
			console.error('Failed to toggle favorite:', error);
			toast.error('收藏状态更新失败');
		}
	};

	const handleUseApp = (app) => {
		// 导航到应用详情页
		window.location.href = `/agents/${app.id}`;
	};

	const loadMore = async () => {
		if (hasMore && !loading) {
			await loadApps(currentPage + 1, true);
		}
	};

	// 响应式过滤
	$: if (searchQuery !== undefined) {
		filterApps();
	}

	// 分类显示名称映射
	const getCategoryName = (category) => {
		const names = {
			all: '全部',
			general: '通用',
			productivity: '效率',
			creative: '创意',
			analysis: '分析'
		};
		return names[category] || category;
	};

	// 获取分类图标
	const getCategoryIcon = (category) => {
		const icons = {
			all: '🏪',
			general: '🤖',
			productivity: '⚡',
			creative: '🎨',
			analysis: '📊'
		};
		return icons[category] || '📱';
	};
</script>

<div class="w-full h-screen flex flex-col overflow-hidden">
	<!-- 页面头部 -->
	<div
		class="sticky top-0 z-10 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-700 flex-shrink-0"
	>
		<div
			class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 p-4 lg:p-6"
		>
			<div class="flex items-start gap-4 flex-1 min-w-0">
				<!-- 汉堡菜单按钮 (移动端显示) -->
				<div class="{$showSidebar ? 'md:hidden' : ''} flex items-center">
					<button
						class="cursor-pointer p-2 flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition lg:hidden"
						on:click={() => {
							showSidebar.set(!$showSidebar);
						}}
						aria-label="Toggle Sidebar"
					>
						<MenuLines />
					</button>
				</div>

				<div class="flex-1 min-w-0">
					<h1 class="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mb-2">
						智能体广场
					</h1>
					<p class="text-gray-600 dark:text-gray-400 text-sm lg:text-base">
						发现和使用各种AI智能应用
					</p>
				</div>
			</div>

			<div class="w-full lg:w-80 flex-shrink-0">
				<SearchInput
					placeholder="搜索应用..."
					bind:value={searchQuery}
					on:input={() => handleSearch(searchQuery)}
					showClearButton={true}
				/>
			</div>
		</div>

		<!-- 分类导航 -->
		<div class="px-4 lg:px-6 pb-4">
			<div class="flex gap-2 overflow-x-auto scrollbar-hidden">
				{#each categories as category}
					<button
						class="flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition-all
							{selectedCategory === category
							? 'bg-blue-600 text-white shadow-lg'
							: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'}"
						on:click={() => handleCategoryChange(category)}
					>
						<span class="text-lg">{getCategoryIcon(category)}</span>
						<span class="text-sm font-medium">{getCategoryName(category)}</span>
					</button>
				{/each}
			</div>
		</div>
	</div>

	<!-- 主要内容区域 -->
	<div class="flex-1 overflow-y-auto min-h-0">
		<div class="w-full p-3 sm:p-4 lg:p-6">
			{#if loading && apps.length === 0}
				<div class="flex flex-col items-center justify-center py-20">
					<Spinner className="mb-4" />
					<p class="text-gray-600 dark:text-gray-400">加载应用中...</p>
				</div>
			{:else if filteredApps.length === 0}
				<div class="flex flex-col items-center justify-center py-20 text-center">
					<div class="text-6xl mb-6 opacity-50">🤖</div>
					<h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">暂无应用</h3>
					<p class="text-gray-600 dark:text-gray-400 max-w-md">
						{#if searchQuery}
							没有找到匹配 "{searchQuery}" 的应用
						{:else}
							该分类下暂时没有应用
						{/if}
					</p>
				</div>
			{:else}
				<div
					class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3 sm:gap-4 lg:gap-6"
				>
					{#each filteredApps as app (app.id)}
						<AgentCard
							{app}
							isFavorited={favoriteApps.has(app.id)}
							on:favorite={() => handleToggleFavorite(app)}
							on:use={() => handleUseApp(app)}
						/>
					{/each}
				</div>

				<!-- 加载更多按钮 -->
				{#if hasMore}
					<div class="flex justify-center mt-8">
						<button
							class="flex items-center gap-2 px-6 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
							on:click={loadMore}
							disabled={loading}
						>
							{#if loading}
								<Spinner className="w-4 h-4" />
								<span>加载中...</span>
							{:else}
								<span>加载更多</span>
							{/if}
						</button>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>

<style>
	:global(.scrollbar-hidden) {
		scrollbar-width: none;
		-ms-overflow-style: none;
	}

	:global(.scrollbar-hidden::-webkit-scrollbar) {
		display: none;
	}

	/* Mobile optimizations */
	@media (max-width: 768px) {
		/* 防止水平滚动 */
		.w-full.h-screen {
			overflow-x: hidden !important;
			max-width: 100vw !important;
			width: 100vw !important;
		}

		.flex-1.overflow-y-auto {
			-webkit-overflow-scrolling: touch;
			scroll-behavior: smooth;
			overflow-x: hidden !important;
			max-width: 100vw !important;
		}

		/* 移动端单列布局 */
		.grid {
			grid-template-columns: 1fr !important;
			gap: 0.75rem !important;
			max-width: 100% !important;
			overflow-x: hidden !important;
		}

		/* 统一间距，防止超出 */
		.p-4,
		.lg\\:p-6 {
			padding: 1rem !important;
		}

		.p-3,
		.sm\\:p-4 {
			padding: 1rem !important;
		}

		/* Category buttons - 确保不超出 */
		.gap-2.overflow-x-auto {
			scrollbar-width: none;
			-ms-overflow-style: none;
			max-width: 100% !important;
		}

		.gap-2.overflow-x-auto::-webkit-scrollbar {
			display: none;
		}
	}
</style>
