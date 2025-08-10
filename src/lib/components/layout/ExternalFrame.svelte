<script>
	import { createEventDispatcher } from 'svelte';

	export let show = false;
	export let url = '';

	const dispatch = createEventDispatcher();

	const handleClose = () => {
		show = false;
		dispatch('close');
	};
</script>

{#if show}
	<div class="fixed inset-0 z-40 flex">
		<!-- 左侧保留区域（用于侧边栏） -->
		<div class="w-64 lg:w-80 flex-shrink-0"></div>

		<!-- iframe容器 -->
		<div class="flex-1 bg-white dark:bg-gray-900 relative">
			<!-- 头部工具栏 -->
			<div
				class="h-12 bg-gray-100 dark:bg-gray-800 border-b dark:border-gray-700 flex items-center justify-between px-4"
			>
				<div class="flex items-center space-x-3">
					<button
						class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition"
						on:click={handleClose}
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
					<span class="text-sm font-medium truncate max-w-md">{url}</span>
				</div>

				<div class="flex items-center space-x-2">
					<!-- 刷新按钮 -->
					<button
						class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition"
						on:click={() => {
							const iframe = document.getElementById('external-iframe');
							if (iframe) {
								iframe.src = iframe.src;
							}
						}}
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
							/>
						</svg>
					</button>

					<!-- 新窗口打开 -->
					<button
						class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition"
						on:click={() => window.open(url, '_blank')}
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
							/>
						</svg>
					</button>
				</div>
			</div>

			<!-- iframe -->
			<iframe
				id="external-iframe"
				src={url}
				title="External Content"
				class="w-full h-[calc(100%-3rem)]"
				frameborder="0"
				allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
				allowfullscreen
			></iframe>
		</div>
	</div>
{/if}

<style>
	iframe {
		border: none;
	}
</style>
