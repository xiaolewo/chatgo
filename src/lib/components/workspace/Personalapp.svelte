<script>
	import { marked } from 'marked';

	import { toast } from 'svelte-sonner';
	import Sortable from 'sortablejs';

	import fileSaver from 'file-saver';
	const { saveAs } = fileSaver;

	import { onMount, getContext, tick } from 'svelte';
	import { goto } from '$app/navigation';
	const i18n = getContext('i18n');

	import { WEBUI_NAME, config, mobile, models as _models, settings, user } from '$lib/stores';
	import {
		createNewModel,
		deleteModelById,
		getModels as getWorkspaceModels,
		toggleModelById,
		updateModelById
	} from '$lib/apis/models';

	import { getModels } from '$lib/apis';
	import { getGroups } from '$lib/apis/groups';

	import EllipsisHorizontal from '../icons/EllipsisHorizontal.svelte';
	import ModelMenu from './Models/ModelMenu.svelte';
	import ModelDeleteConfirmDialog from '../common/ConfirmDialog.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import GarbageBin from '../icons/GarbageBin.svelte';
	import Search from '../icons/Search.svelte';
	import Plus from '../icons/Plus.svelte';
	import ChevronRight from '../icons/ChevronRight.svelte';
	import Switch from '../common/Switch.svelte';
	import Spinner from '../common/Spinner.svelte';
	import { capitalizeFirstLetter } from '$lib/utils';

	let shiftKey = false;

	let importFiles;
	let modelsImportInputElement;
	let loaded = false;

	let models = [];

	let filteredModels = [];
	let selectedModel = null;

	let showModelDeleteConfirm = false;

	let group_ids = [];
	let searchValue = '';
	let sortBy = '最新';

	// 模拟评分数据（我的应用通常评分会稍低一些）
	const getModelRating = (modelId) => {
		const ratings = {
			default: 4.5
		};
		return ratings[modelId] || (3.5 + Math.random() * 1.5).toFixed(1);
	};

	const getModelUsageCount = (modelId) => {
		// 我的应用使用量通常较少
		return `${Math.floor(Math.random() * 500 + 50)}`;
	};

	const getModelStatus = (model) => {
		return model.is_active ? '已启用' : '已禁用';
	};

	$: {
		let filtered = models.filter((m) => {
			// 搜索过滤
			if (searchValue.trim() !== '') {
				const searchLower = searchValue.toLowerCase();
				const nameMatch = m.name?.toLowerCase().includes(searchLower);
				const descMatch = m?.meta?.description?.toLowerCase().includes(searchLower);
				if (!nameMatch && !descMatch) return false;
			}
			return true;
		});

		// 排序
		if (sortBy === '评分') {
			filtered = filtered.sort(
				(a, b) => parseFloat(getModelRating(b.name)) - parseFloat(getModelRating(a.name))
			);
		} else if (sortBy === '使用量') {
			filtered = filtered.sort((a, b) => {
				const aCount = parseInt(getModelUsageCount(a.name));
				const bCount = parseInt(getModelUsageCount(b.name));
				return bCount - aCount;
			});
		} else if (sortBy === '状态') {
			filtered = filtered.sort((a, b) => (b.is_active ? 1 : 0) - (a.is_active ? 1 : 0));
		}

		filteredModels = filtered;
	}

	const deleteModelHandler = async (model) => {
		const res = await deleteModelById(localStorage.token, model.id).catch((e) => {
			toast.error(`${e}`);
			return null;
		});

		if (res) {
			toast.success($i18n.t(`Deleted {{name}}`, { name: model.id }));
		}

		await _models.set(
			await getModels(
				localStorage.token,
				$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
			)
		);
		models = await getWorkspaceModels(localStorage.token);
	};

	const cloneModelHandler = async (model) => {
		sessionStorage.model = JSON.stringify({
			...model,
			id: `${model.id}-clone`,
			name: `${model.name} (Clone)`
		});
		goto('/personalapp/create');
	};

	const shareModelHandler = async (model) => {
		toast.success($i18n.t('Redirecting you to Open WebUI Community'));

		const url = 'https://openwebui.com';

		const tab = await window.open(`${url}/models/create`, '_blank');

		const messageHandler = (event) => {
			if (event.origin !== url) return;
			if (event.data === 'loaded') {
				tab.postMessage(JSON.stringify(model), '*');
				window.removeEventListener('message', messageHandler);
			}
		};

		window.addEventListener('message', messageHandler, false);
	};

	const hideModelHandler = async (model) => {
		let info = model.info;

		if (!info) {
			info = {
				id: model.id,
				name: model.name,
				meta: {
					suggestion_prompts: null
				},
				params: {}
			};
		}

		info.meta = {
			...info.meta,
			hidden: !(info?.meta?.hidden ?? false)
		};

		console.log(info);

		const res = await updateModelById(localStorage.token, info.id, info);

		if (res) {
			toast.success(
				$i18n.t(`Model {{name}} is now {{status}}`, {
					name: info.id,
					status: info.meta.hidden ? 'hidden' : 'visible'
				})
			);
		}

		await _models.set(
			await getModels(
				localStorage.token,
				$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
			)
		);
		models = await getWorkspaceModels(localStorage.token);
	};

	const downloadModels = async (models) => {
		let blob = new Blob([JSON.stringify(models)], {
			type: 'application/json'
		});
		saveAs(blob, `models-export-${Date.now()}.json`);
	};

	const exportModelHandler = async (model) => {
		let blob = new Blob([JSON.stringify([model])], {
			type: 'application/json'
		});
		saveAs(blob, `${model.id}-${Date.now()}.json`);
	};

	onMount(async () => {
		models = await getWorkspaceModels(localStorage.token);
		let groups = await getGroups(localStorage.token);
		group_ids = groups.map((group) => group.id);

		loaded = true;

		const onKeyDown = (event) => {
			if (event.key === 'Shift') {
				shiftKey = true;
			}
		};

		const onKeyUp = (event) => {
			if (event.key === 'Shift') {
				shiftKey = false;
			}
		};

		const onBlur = () => {
			shiftKey = false;
		};

		window.addEventListener('keydown', onKeyDown);
		window.addEventListener('keyup', onKeyUp);
		window.addEventListener('blur-sm', onBlur);

		return () => {
			window.removeEventListener('keydown', onKeyDown);
			window.removeEventListener('keyup', onKeyUp);
			window.removeEventListener('blur-sm', onBlur);
		};
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Models')} • {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<ModelDeleteConfirmDialog
		bind:show={showModelDeleteConfirm}
		on:confirm={() => {
			deleteModelHandler(selectedModel);
		}}
	/>

	<!-- 搜索和筛选栏 -->
	<div class="flex flex-col gap-4 my-4">
		<!-- 标题和统计 -->
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<h2 class="text-xl font-semibold text-gray-900 dark:text-white">我的应用</h2>
				<span
					class="px-3 py-1 text-sm font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full"
				>
					{filteredModels.length} 个应用
				</span>
			</div>

			<!-- 创建按钮 -->
			<a
				href="/personalapp/create"
				class="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl transition-colors font-medium"
			>
				<Plus className="size-4" />
				创建应用
			</a>
		</div>

		<!-- 搜索栏 -->
		<div class="flex items-center gap-4">
			<div class="flex-1 relative">
				<div class="absolute left-3 top-1/2 transform -translate-y-1/2">
					<Search className="size-4 text-gray-400" />
				</div>
				<input
					class="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
					bind:value={searchValue}
					placeholder="搜索我的应用..."
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
					<option value="状态">状态</option>
				</select>
			</div>
		</div>
	</div>
	<!-- 卡片网格 -->
	<div
		class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8"
		id="model-list"
	>
		{#each filteredModels as model}
			<div
				class="group bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg hover:border-gray-300 dark:hover:border-gray-600 transition-all duration-200 {model.is_active
					? ''
					: 'opacity-75'}"
				id="model-item-{model.id}"
			>
				<!-- 图标和标题 -->
				<div class="flex items-start gap-3 mb-4">
					<div class="flex-shrink-0">
						<div
							class="w-12 h-12 rounded-xl bg-gradient-to-br from-green-100 to-blue-100 dark:from-green-900 dark:to-blue-900 flex items-center justify-center text-2xl"
						>
							{#if model?.meta?.profile_image_url}
								<img
									src={model.meta.profile_image_url}
									alt="应用头像"
									class="w-full h-full rounded-xl object-cover"
								/>
							{:else}
								🤖
							{/if}
						</div>
					</div>

					<div class="flex-1 min-w-0">
						<a
							href={`/?models=${encodeURIComponent(model.id)}`}
							class="block group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors"
						>
							<h3 class="font-semibold text-gray-900 dark:text-white text-base line-clamp-1">
								{model.name}
							</h3>
						</a>

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
						{#if (model?.meta?.description ?? '').trim()}
							{model.meta.description}
						{:else}
							{model.id}
						{/if}
					</p>
				</div>

				<!-- 状态和操作 -->
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<span
							class="px-2 py-1 text-xs font-medium rounded-md {model.is_active
								? 'bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400'
								: 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}"
						>
							{getModelStatus(model)}
						</span>

						<!-- 开关 -->
						<div class="ml-1">
							<Tooltip content={model.is_active ? '点击禁用' : '点击启用'}>
								<Switch
									bind:state={model.is_active}
									on:change={async (e) => {
										toggleModelById(localStorage.token, model.id);
										_models.set(
											await getModels(
												localStorage.token,
												$config?.features?.enable_direct_connections &&
													($settings?.directConnections ?? null)
											)
										);
									}}
								/>
							</Tooltip>
						</div>
					</div>

					<!-- 操作按钮 -->
					<div class="flex items-center gap-1">
						{#if shiftKey}
							<Tooltip content="删除">
								<button
									class="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
									type="button"
									on:click={() => {
										deleteModelHandler(model);
									}}
								>
									<GarbageBin className="size-4" />
								</button>
							</Tooltip>
						{:else}
							{#if $user?.role === 'admin' || model.user_id === $user?.id || model.access_control.write.group_ids.some( (wg) => group_ids.includes(wg) )}
								<Tooltip content="编辑">
									<a
										class="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
										href={`/personalapp/edit?id=${encodeURIComponent(model.id)}`}
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											fill="none"
											viewBox="0 0 24 24"
											stroke-width="1.5"
											stroke="currentColor"
											class="w-4 h-4"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125"
											/>
										</svg>
									</a>
								</Tooltip>
							{/if}

							<ModelMenu
								user={$user}
								{model}
								shareHandler={() => {
									shareModelHandler(model);
								}}
								cloneHandler={() => {
									cloneModelHandler(model);
								}}
								exportHandler={() => {
									exportModelHandler(model);
								}}
								hideHandler={() => {
									hideModelHandler(model);
								}}
								deleteHandler={() => {
									selectedModel = model;
									showModelDeleteConfirm = true;
								}}
								onClose={() => {}}
							>
								<Tooltip content="更多操作">
									<button
										class="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
										type="button"
									>
										<EllipsisHorizontal className="size-4" />
									</button>
								</Tooltip>
							</ModelMenu>
						{/if}
					</div>
				</div>
			</div>
		{/each}
	</div>

	<!-- 空状态 -->
	{#if filteredModels.length === 0}
		<div class="text-center py-12">
			<div class="text-6xl mb-4">📱</div>
			<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">还没有创建应用</h3>
			<p class="text-gray-500 dark:text-gray-400 mb-4">开始创建你的第一个AI助手应用吧</p>
			<a
				href="/personalapp/create"
				class="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl transition-colors font-medium"
			>
				<Plus className="size-4" />
				创建应用
			</a>
		</div>
	{/if}

	{#if $user?.role === 'admin'}
		<div class=" flex justify-end w-full mb-3">
			<div class="flex space-x-1">
				<input
					id="models-import-input"
					bind:this={modelsImportInputElement}
					bind:files={importFiles}
					type="file"
					accept=".json"
					hidden
					on:change={() => {
						console.log(importFiles);

						let reader = new FileReader();
						reader.onload = async (event) => {
							let savedModels = JSON.parse(event.target.result);
							console.log(savedModels);

							for (const model of savedModels) {
								if (model?.info ?? false) {
									if ($_models.find((m) => m.id === model.id)) {
										await updateModelById(localStorage.token, model.id, model.info).catch(
											(error) => {
												return null;
											}
										);
									} else {
										await createNewModel(localStorage.token, model.info).catch((error) => {
											return null;
										});
									}
								} else {
									if (model?.id && model?.name) {
										await createNewModel(localStorage.token, model).catch((error) => {
											return null;
										});
									}
								}
							}

							await _models.set(
								await getModels(
									localStorage.token,
									$config?.features?.enable_direct_connections &&
										($settings?.directConnections ?? null)
								)
							);
							models = await getWorkspaceModels(localStorage.token);
						};

						reader.readAsText(importFiles[0]);
					}}
				/>

				<button
					class="flex text-xs items-center space-x-1 px-3 py-1.5 rounded-xl bg-gray-50 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-200 transition"
					on:click={() => {
						modelsImportInputElement.click();
					}}
				>
					<div class=" self-center mr-2 font-medium line-clamp-1">{$i18n.t('Import Models')}</div>

					<div class=" self-center">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 16 16"
							fill="currentColor"
							class="w-3.5 h-3.5"
						>
							<path
								fill-rule="evenodd"
								d="M4 2a1.5 1.5 0 0 0-1.5 1.5v9A1.5 1.5 0 0 0 4 14h8a1.5 1.5 0 0 0 1.5-1.5V6.621a1.5 1.5 0 0 0-.44-1.06L9.94 2.439A1.5 1.5 0 0 0 8.878 2H4Zm4 9.5a.75.75 0 0 1-.75-.75V8.06l-.72.72a.75.75 0 0 1-1.06-1.06l2-2a.75.75 0 0 1 1.06 0l2 2a.75.75 0 1 1-1.06 1.06l-.72-.72v2.69a.75.75 0 0 1-.75.75Z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
				</button>

				{#if models.length}
					<button
						class="flex text-xs items-center space-x-1 px-3 py-1.5 rounded-xl bg-gray-50 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-200 transition"
						on:click={async () => {
							downloadModels(models);
						}}
					>
						<div class=" self-center mr-2 font-medium line-clamp-1">
							{$i18n.t('Export Models')}
						</div>

						<div class=" self-center">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3.5 h-3.5"
							>
								<path
									fill-rule="evenodd"
									d="M4 2a1.5 1.5 0 0 0-1.5 1.5v9A1.5 1.5 0 0 0 4 14h8a1.5 1.5 0 0 0 1.5-1.5V6.621a1.5 1.5 0 0 0-.44-1.06L9.94 2.439A1.5 1.5 0 0 0 8.878 2H4Zm4 3.5a.75.75 0 0 1 .75.75v2.69l.72-.72a.75.75 0 1 1 1.06 1.06l-2 2a.75.75 0 0 1-1.06 0l-2-2a.75.75 0 0 1 1.06-1.06l.72.72V6.25A.75.75 0 0 1 8 5.5Z"
									clip-rule="evenodd"
								/>
							</svg>
						</div>
					</button>
				{/if}
			</div>
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
