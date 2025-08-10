<script>
	import { onMount, getContext } from 'svelte';
	import { config, models, settings } from '$lib/stores';
	import { getModels } from '$lib/apis';
	import Personalapp from '$lib/components/workspace/Personalapp.svelte';
	import Publicapp from '$lib/components/workspace/Publicapp.svelte';

	// 定义标签页数据
	const TABS = [
		{ id: 'app-gallery', label: '应用广场' },
		{ id: 'my-apps', label: '我的应用' }
	];

	// 状态管理
	let activeTab = TABS[0].label;

	// 国际化上下文
	const i18n = getContext('i18n');

	onMount(async () => {
		try {
			models.set(
				await getModels(
					localStorage.token,
					$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
				)
			);
		} catch (error) {
			console.error('Error loading models:', error);
		}
	});

	// 切换标签页的方法
	function setActiveTab(tabLabel) {
		activeTab = tabLabel;
	}
</script>

{#if $models !== null}
	<div class="w-full flex flex-col h-full">
		<div class="flex gap-2 mb-4">
			{#each TABS as tab}
				<button
					on:click={() => setActiveTab(tab.label)}
					class:selected={activeTab == tab.label}
					class="min-w-fit rounded-full px-4 py-2 text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white transition"
				>
					{tab.label}
				</button>
			{/each}
		</div>
		<div class="flex-1">
			{#if activeTab === '应用广场'}
				<Publicapp />
			{:else}
				<Personalapp />
			{/if}
		</div>
	</div>
{:else}
	<div class="w-full h-full flex justify-center items-center">
		<div>Loading...</div>
	</div>
{/if}

<style>
	.selected {
		color: #4e4e4e;
		background-color: rgba(0, 0, 0, 0.05);
	}
	:global(.dark) .selected {
		color: white;
		background-color: rgba(255, 255, 255, 0.1);
	}
</style>
