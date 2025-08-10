<script>
	import Fuse from 'fuse.js';

	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	dayjs.extend(relativeTime);

	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	const i18n = getContext('i18n');

	import { WEBUI_NAME, knowledge } from '$lib/stores';
	import {
		getKnowledgeBases,
		deleteKnowledgeById,
		getKnowledgeBaseList
	} from '$lib/apis/knowledge';

	import { goto } from '$app/navigation';

	import DeleteConfirmDialog from '../common/ConfirmDialog.svelte';
	import ItemMenu from './Knowledge/ItemMenu.svelte';
	import Badge from '../common/Badge.svelte';
	import Search from '../icons/Search.svelte';
	import Plus from '../icons/Plus.svelte';
	import Spinner from '../common/Spinner.svelte';
	import { capitalizeFirstLetter } from '$lib/utils';
	import Tooltip from '../common/Tooltip.svelte';

	let loaded = false;

	let query = '';
	let selectedItem = null;
	let showDeleteConfirm = false;
	let sortBy = '最新';

	let fuse = null;

	let knowledgeBases = [];
	let filteredItems = [];

	// 模拟评分数据（知识库）
	const getKnowledgeRating = (itemId) => {
		return (4.2 + Math.random() * 0.8).toFixed(1);
	};

	const getKnowledgeUsageCount = (itemId) => {
		return `${Math.floor(Math.random() * 1000 + 200)}`;
	};

	$: if (knowledgeBases) {
		fuse = new Fuse(knowledgeBases, {
			keys: ['name', 'description']
		});
	}

	$: {
		let filtered = query ? fuse?.search(query).map((e) => e.item) || [] : knowledgeBases;

		// 排序
		if (sortBy === '评分') {
			filtered = filtered.sort(
				(a, b) => parseFloat(getKnowledgeRating(b.id)) - parseFloat(getKnowledgeRating(a.id))
			);
		} else if (sortBy === '使用量') {
			filtered = filtered.sort((a, b) => {
				const aCount = parseInt(getKnowledgeUsageCount(a.id));
				const bCount = parseInt(getKnowledgeUsageCount(b.id));
				return bCount - aCount;
			});
		}

		filteredItems = filtered;
	}

	const deleteHandler = async (item) => {
		const res = await deleteKnowledgeById(localStorage.token, item.id).catch((e) => {
			toast.error(`${e}`);
		});

		if (res) {
			knowledgeBases = await getKnowledgeBaseList(localStorage.token);
			knowledge.set(await getKnowledgeBases(localStorage.token));
			toast.success($i18n.t('Knowledge deleted successfully.'));
		}
	};

	onMount(async () => {
		knowledgeBases = await getKnowledgeBaseList(localStorage.token);
		loaded = true;
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Knowledge')} • {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<DeleteConfirmDialog
		bind:show={showDeleteConfirm}
		on:confirm={() => {
			deleteHandler(selectedItem);
		}}
	/>

	<!-- 搜索和筛选栏 -->
	<div class="flex flex-col gap-4 my-4">
		<!-- 标题和统计 -->
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<h2 class="text-xl font-semibold text-gray-900 dark:text-white">知识库</h2>
				<span
					class="px-3 py-1 text-sm font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-full"
				>
					{filteredItems.length} 个知识库
				</span>
			</div>

			<!-- 创建按钮 -->
			<button
				class="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-xl transition-colors font-medium"
				aria-label={$i18n.t('Create Knowledge')}
				on:click={() => {
					goto('/knowledge/create');
				}}
			>
				<Plus className="size-4" />
				创建知识库
			</button>
		</div>

		<!-- 搜索栏 -->
		<div class="flex items-center gap-4">
			<div class="flex-1 relative">
				<div class="absolute left-3 top-1/2 transform -translate-y-1/2">
					<Search className="size-4 text-gray-400" />
				</div>
				<input
					class="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
					bind:value={query}
					placeholder="搜索知识库标题或描述..."
				/>
			</div>

			<!-- 筛选按钮 -->
			<div class="relative">
				<select
					bind:value={sortBy}
					class="px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all cursor-pointer"
				>
					<option value="最新">最新</option>
					<option value="评分">评分</option>
					<option value="使用量">使用量</option>
				</select>
			</div>
		</div>
	</div>

	<!-- 卡片网格 -->
	<div
		class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8"
		id="knowledge-list"
	>
		{#each filteredItems as item}
			<div
				class="group bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg hover:border-gray-300 dark:hover:border-gray-600 transition-all duration-200 cursor-pointer"
				on:click={() => {
					if (item?.meta?.document) {
						toast.error(
							$i18n.t(
								'Only collections can be edited, create a new knowledge base to edit/add documents.'
							)
						);
					} else {
						goto(`/knowledge/${item.id}`);
					}
				}}
			>
				<!-- 图标和标题 -->
				<div class="flex items-start gap-3 mb-4">
					<div class="flex-shrink-0">
						<div
							class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-100 to-indigo-100 dark:from-purple-900 dark:to-indigo-900 flex items-center justify-center text-2xl"
						>
							{#if item?.meta?.document}
								📄
							{:else}
								📚
							{/if}
						</div>
					</div>

					<div class="flex-1 min-w-0">
						<h3
							class="font-semibold text-gray-900 dark:text-white text-base line-clamp-1 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors"
						>
							{item.name}
						</h3>

						<!-- 评分和使用量 -->
						<div class="flex items-center gap-3 mt-1">
							<div class="flex items-center gap-1">
								<span class="text-yellow-400">⭐</span>
								<span class="text-sm font-medium text-gray-700 dark:text-gray-300"
									>{getKnowledgeRating(item.id)}</span
								>
							</div>
							<div class="text-xs text-gray-500 dark:text-gray-400">
								{getKnowledgeUsageCount(item.id)}使用
							</div>
						</div>
					</div>
				</div>

				<!-- 描述 -->
				<div class="mb-4">
					<p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 leading-relaxed">
						{#if item.description?.trim()}
							{item.description}
						{:else}
							暂无描述
						{/if}
					</p>
				</div>

				<!-- 标签和操作 -->
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						{#if item?.meta?.document}
							<span
								class="px-2 py-1 text-xs font-medium bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-md"
							>
								📄 文档
							</span>
						{:else}
							<span
								class="px-2 py-1 text-xs font-medium bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-md"
							>
								📚 集合
							</span>
						{/if}
					</div>

					<!-- 操作按钮 -->
					<div class="flex items-center gap-1">
						<ItemMenu
							on:delete={() => {
								selectedItem = item;
								showDeleteConfirm = true;
							}}
						/>
					</div>
				</div>

				<!-- 底部信息 -->
				<div
					class="flex items-center justify-between mt-4 pt-4 border-t border-gray-100 dark:border-gray-700"
				>
					<div class="text-xs text-gray-500 dark:text-gray-400">
						<Tooltip
							content={item?.user?.email ?? $i18n.t('Deleted User')}
							className="flex shrink-0"
							placement="top-start"
						>
							创建者: {capitalizeFirstLetter(
								item?.user?.name ?? item?.user?.email ?? $i18n.t('Deleted User')
							)}
						</Tooltip>
					</div>
					<div class="text-xs text-gray-500 dark:text-gray-400">
						{dayjs(item.updated_at * 1000).fromNow()}
					</div>
				</div>
			</div>
		{/each}
	</div>

	<!-- 空状态 -->
	{#if filteredItems.length === 0}
		<div class="text-center py-12">
			<div class="text-6xl mb-4">📚</div>
			<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">还没有创建知识库</h3>
			<p class="text-gray-500 dark:text-gray-400 mb-4">开始创建你的第一个知识库来管理文档和信息</p>
			<button
				class="inline-flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-xl transition-colors font-medium"
				on:click={() => {
					goto('/knowledge/create');
				}}
			>
				<Plus className="size-4" />
				创建知识库
			</button>
		</div>
	{/if}

	<div class="text-center text-gray-500 text-xs mt-8 mb-2">
		💡 提示：在聊天输入框中使用 '#' 符号可以快速加载和引用你的知识库内容
	</div>
{:else}
	<div class="w-full h-full flex justify-center items-center">
		<Spinner />
	</div>
{/if}
