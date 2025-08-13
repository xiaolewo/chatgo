<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import AgentAdmin from '$lib/components/agents/AgentAdmin.svelte';
	import { WEBUI_NAME } from '$lib/stores';
	let authorized = false;

	onMount(() => {
		// 检查用户是否已登录
		if (!$user) {
			goto('/auth');
			return;
		}

		// 检查用户是否为管理员
		if ($user.role !== 'admin') {
			toast.error('您需要管理员权限才能访问此页面');
			goto('/');
			return;
		}

		authorized = true;
	});
</script>

<svelte:head>
	<title>智能体管理 - {`${$WEBUI_NAME}`}</title>
	<meta name="description" content="管理智能体应用" />
</svelte:head>

{#if authorized}
	<AgentAdmin />
{:else if $user && $user.role !== 'admin'}
	<div class="unauthorized-container">
		<div class="unauthorized-content">
			<div class="unauthorized-icon">🚫</div>
			<h1>访问被拒绝</h1>
			<p>您需要管理员权限才能访问智能体管理页面。</p>
			<button class="btn-primary" on:click={() => goto('/')}> 返回首页 </button>
		</div>
	</div>
{:else}
	<div class="loading-container">
		<div class="loading-spinner"></div>
		<p>正在验证权限...</p>
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

	.unauthorized-container {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 60vh;
		padding: 2rem;
	}

	.unauthorized-content {
		text-align: center;
		max-width: 400px;
	}

	.unauthorized-icon {
		font-size: 4rem;
		margin-bottom: 1.5rem;
		opacity: 0.7;
	}

	.unauthorized-content h1 {
		font-size: 2rem;
		font-weight: 700;
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.unauthorized-content p {
		color: #6b7280;
		font-size: 1.1rem;
		line-height: 1.6;
		margin-bottom: 2rem;
	}

	.btn-primary {
		padding: 0.75rem 2rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 0.5rem;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.btn-primary:hover {
		background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
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
