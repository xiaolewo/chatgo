<script>
	import { marked } from 'marked';

	import { onMount, getContext } from 'svelte';
	const i18n = getContext('i18n');

	import { WEBUI_NAME, config, models as _models, settings, models } from '$lib/stores';

	import { getModels } from '$lib/apis';
	import { getGroups } from '$lib/apis/groups';
	import Tooltip from '../common/Tooltip.svelte';
	import Search from '../icons/Search.svelte';
	import ChevronRight from '../icons/ChevronRight.svelte';
	import Spinner from '../common/Spinner.svelte';

	let loaded = false;
	let tagsContainerElement;

	let selectedTag = '';
	let selectedConnectionType = '';
	let modelslist = [];
	let tags = [];
	let searchValue = '';
	let sortBy = '最新';

	// 模拟评分数据（实际项目中应该从API获取）
	const getModelRating = (modelId) => {
		const ratings = {
			default: 4.9,
			论文降重大师: 4.9,
			刑辩专家: 4.8,
			岩土工程助手: 4.7,
			无线通信专家: 4.9,
			眼科医生: 4.6,
			哲学剖析助手: 4.8,
			有机化学研究员: 4.9,
			美术论文顾问: 4.7
		};
		return ratings[modelId] || (4.0 + Math.random() * 1.0).toFixed(1);
	};

	const getModelUsageCount = (modelId) => {
		const usage = {
			论文降重大师: '2.1k',
			刑辩专家: '1.8k',
			岩土工程助手: '1.5k',
			无线通信专家: '2.3k',
			眼科医生: '1.2k',
			哲学剖析助手: '980',
			有机化学研究员: '1.6k',
			美术论文顾问: '890'
		};
		return usage[modelId] || `${Math.floor(Math.random() * 2000 + 100)}`;
	};

	$: {
		let filtered = $models.filter((item) => {
			// 搜索过滤
			if (searchValue.trim() !== '') {
				const searchLower = searchValue.toLowerCase();
				const nameMatch = item.name?.toLowerCase().includes(searchLower);
				const descMatch = item?.info?.meta?.description?.toLowerCase().includes(searchLower);
				if (!nameMatch && !descMatch) return false;
			}

			// 标签过滤
			if (selectedTag === '') {
				return true;
			}
			return (item.tags ?? []).map((tag) => tag.name).includes(selectedTag);
		});

		// 排序
		if (sortBy === '评分') {
			filtered = filtered.sort(
				(a, b) => parseFloat(getModelRating(b.name)) - parseFloat(getModelRating(a.name))
			);
		} else if (sortBy === '使用量') {
			filtered = filtered.sort((a, b) => {
				const aCount = parseInt(
					getModelUsageCount(a.name).replace('k', '000').replace(/[^\d]/g, '')
				);
				const bCount = parseInt(
					getModelUsageCount(b.name).replace('k', '000').replace(/[^\d]/g, '')
				);
				return bCount - aCount;
			});
		}

		modelslist = filtered;
	}

	onMount(async () => {
		modelslist = $models;
		if (modelslist) {
			tags = modelslist
				.filter((item) => !(item.info?.meta?.hidden ?? false))
				.flatMap((item) => item.tags ?? [])
				.map((tag) => tag.name);

			// Remove duplicates and sort
			tags = Array.from(new Set(tags)).sort((a, b) => a.localeCompare(b));
		}

		loaded = true;
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Models')} • {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<!-- 搜索和筛选栏 -->
	<div class="flex flex-col gap-4 my-4">
		<!-- 搜索栏 -->
		<div class="flex items-center gap-4">
			<div class="flex-1 relative">
				<div class="absolute left-3 top-1/2 transform -translate-y-1/2">
					<Search className="size-4 text-gray-400" />
				</div>
				<input
					class="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
					bind:value={searchValue}
					placeholder="搜索助手标题或内容..."
				/>
			</div>

			<!-- 筛选按钮 -->
			<div class="relative">
				<select
					bind:value={sortBy}
					class="px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all cursor-pointer"
				>
					<option value="最新">最新</option>
					<option value="评分">评分</option>
					<option value="使用量">使用量</option>
				</select>
			</div>
		</div>

		<!-- 分类标签 -->
		{#if tags && tags.length > 0}
			<div class="flex flex-wrap gap-2">
				<button
					class="px-4 py-2 rounded-full text-sm font-medium transition-all {selectedTag === ''
						? 'bg-blue-500 text-white'
						: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}"
					on:click={() => {
						selectedTag = '';
					}}
				>
					• 全部
				</button>
				{#each tags as tag}
					<button
						class="px-4 py-2 rounded-full text-sm font-medium transition-all {selectedTag === tag
							? 'bg-blue-500 text-white'
							: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}"
						on:click={() => {
							selectedTag = tag;
						}}
					>
						• {tag}
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<!-- 卡片网格 -->
	<div
		class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8"
		id="model-list"
	>
		{#each modelslist as model}
			<a
				href={`/?models=${encodeURIComponent(model.id)}`}
				class="group block bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg hover:border-gray-300 dark:hover:border-gray-600 transition-all duration-200 cursor-pointer"
				id="model-item-{model.id}"
			>
				<!-- 图标和标题 -->
				<div class="flex items-start gap-3 mb-4">
					<div class="flex-shrink-0">
						<div
							class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 flex items-center justify-center text-2xl"
						>
							{#if model?.info?.meta?.profile_image_url}
								<img
									src={model.info.meta.profile_image_url}
									alt="助手头像"
									class="w-full h-full rounded-xl object-cover"
								/>
							{:else}
								<!-- 根据第一个标签显示不同图标 -->
								{#if model.tags && model.tags.length > 0}
									{#if model.tags[0].name === '学术'}
										📝
									{:else if model.tags[0].name === '职业'}
										💼
									{:else if model.tags[0].name === '文案'}
										✏️
									{:else if model.tags[0].name === '设计'}
										🎨
									{:else if model.tags[0].name === '教育'}
										🎓
									{:else}
										🤖
									{/if}
								{:else}
									🤖
								{/if}
							{/if}
						</div>
					</div>

					<div class="flex-1 min-w-0">
						<h3
							class="font-semibold text-gray-900 dark:text-white text-base line-clamp-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors"
						>
							{model.name}
						</h3>

						<!-- 评分和使用量 -->
						<div class="flex items-center gap-3 mt-1">
							<div class="flex items-center gap-1">
								<span class="text-yellow-400">⭐</span>
								<span class="text-sm font-medium text-gray-700 dark:text-gray-300"
									>{getModelRating(model.name)}</span
								>
							</div>
							<div class="text-xs text-gray-500 dark:text-gray-400">
								{getModelUsageCount(model.name)}使用
							</div>
						</div>
					</div>
				</div>

				<!-- 描述 -->
				<div class="mb-4">
					<p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 leading-relaxed">
						{#if (model?.info?.meta?.description ?? '').trim()}
							{model.info.meta.description}
						{:else}
							{model.id}
						{/if}
					</p>
				</div>

				<!-- 标签 -->
				{#if model?.tags?.length > 0}
					<div class="flex items-center justify-between">
						<div class="flex flex-wrap gap-1">
							{#each model.tags.slice(0, 2) as tag}
								<span
									class="px-2 py-1 text-xs font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-md"
								>
									🏷️ {tag.name}
								</span>
							{/each}
							{#if model.tags.length > 2}
								<span class="px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
									+{model.tags.length - 2}
								</span>
							{/if}
						</div>
					</div>
				{/if}
			</a>
		{/each}
	</div>

	<!-- 空状态 -->
	{#if modelslist.length === 0}
		<div class="text-center py-12">
			<div class="text-6xl mb-4">🔍</div>
			<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">没有找到相关助手</h3>
			<p class="text-gray-500 dark:text-gray-400">尝试调整搜索条件或浏览其他分类</p>
		</div>
	{/if}

	{#if $config?.features.enable_community_sharing}
		{#if false}
			<div class=" my-16">
				<div class=" text-xl font-medium mb-1 line-clamp-1">
					{$i18n.t('Made by Open WebUI Community')}
				</div>

				<a
					class=" flex cursor-pointer items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-850 w-full mb-2 px-3.5 py-1.5 rounded-xl transition"
					href="https://openwebui.com/#open-webui-community"
					target="_blank"
				>
					<div class=" self-center">
						<div class=" font-semibold line-clamp-1">{$i18n.t('Discover a model')}</div>
						<div class=" text-sm line-clamp-1">
							{$i18n.t('Discover, download, and explore model presets')}
						</div>
					</div>

					<div>
						<div>
							<ChevronRight />
						</div>
					</div>
				</a>
			</div>
		{/if}
	{/if}
{:else}
	<div class="w-full h-full flex justify-center items-center">
		<Spinner />
	</div>
{/if}
