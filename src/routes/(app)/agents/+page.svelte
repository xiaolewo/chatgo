<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import AgentMarketplace from '$lib/components/agents/AgentMarketplace.svelte';
	import { WEBUI_NAME } from '$lib/stores';
	onMount(() => {
		// 检查用户是否已登录
		if (!$user) {
			goto('/auth');
			return;
		}
	});
</script>

<svelte:head>
	<title>智能体广场 - {`${$WEBUI_NAME}`}</title>
	<meta name="description" content="发现和使用各种AI智能应用" />
</svelte:head>

{#if $user}
	<AgentMarketplace />
{:else}
	<div class="loading-container">
		<div class="loading-spinner"></div>
		<p>正在加载...</p>
	</div>
{/if}

<style>
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 50vh;
		gap: 1rem;
	}

	.loading-spinner {
		width: 2rem;
		height: 2rem;
		border: 2px solid #e5e7eb;
		border-top: 2px solid #667eea;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}
</style>
