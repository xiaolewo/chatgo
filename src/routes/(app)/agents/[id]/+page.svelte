<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import AgentDetail from '$lib/components/agents/AgentDetail.svelte';
	import { WEBUI_NAME } from '$lib/stores';
	$: appId = $page.params.id;

	onMount(() => {
		// 检查用户是否已登录
		if (!$user) {
			goto('/auth');
			return;
		}

		// 检查应用ID是否有效
		if (!appId) {
			goto('/agents');
			return;
		}
	});
</script>

<svelte:head>
	<title>智能体应用详情 - {`${$WEBUI_NAME}`}</title>
	<meta name="description" content="查看和使用智能体应用" />
</svelte:head>

{#if $user && appId}
	<AgentDetail {appId} />
{:else}
	<div class="loading-container">
		<div class="loading-spinner"></div>
		<p>正在加载应用详情...</p>
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
