<script>
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { user } from '$lib/stores';
	import Switch from '$lib/components/common/Switch.svelte';
	import { getMidJourneyConfig, updateMidJourneyConfig } from '$lib/apis/midjourney.js';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;
	let saving = false;
	let config = {
		enabled: false,
		api_url: '',
		api_key: '',
		fast_credits: 10,
		relax_credits: 5,
		turbo_credits: 15
	};

	// 加载配置
	const loadConfig = async () => {
		if (!$user?.token) return;

		loading = true;
		try {
			const response = await getMidJourneyConfig($user.token);
			config = { ...config, ...response };
			console.log('MidJourney配置加载成功, 状态:', config.enabled ? '已启用' : '未启用');
		} catch (error) {
			console.error('加载MidJourney配置失败:', error);
			toast.error('加载配置失败: ' + error.message);
		} finally {
			loading = false;
		}
	};

	// 保存配置
	const saveHandler = async () => {
		if (!$user?.token) {
			toast.error('未登录，无法保存配置');
			return;
		}

		saving = true;
		try {
			const response = await updateMidJourneyConfig($user.token, config);
			toast.success('MidJourney配置保存成功');
			dispatch('save');
			console.log('配置保存响应:', response);
		} catch (error) {
			console.error('保存MidJourney配置失败:', error);
			toast.error('保存失败: ' + error.message);
		} finally {
			saving = false;
		}
	};

	// 验证配置
	const validateConfig = () => {
		if (config.enabled) {
			if (!config.api_url.trim()) {
				toast.error('请填写API URL');
				return false;
			}
			if (!config.api_key.trim()) {
				toast.error('请填写API密钥');
				return false;
			}
		}
		return true;
	};

	// 保存前验证
	const handleSave = async () => {
		if (!validateConfig()) return;
		await saveHandler();
	};

	// 组件挂载时加载配置
	onMount(() => {
		loadConfig();
	});
</script>

<div class="flex flex-col h-full justify-between space-y-3 text-sm">
	<div class="space-y-3 overflow-y-scroll scrollbar-hidden pr-2">
		<div>
			<div class="mb-1 text-sm font-medium">MidJourney 设置</div>
			<div class="py-1 flex w-full justify-between">
				<div class="self-center text-xs font-medium">启用 MidJourney</div>
				<Switch bind:state={config.enabled} />
			</div>
		</div>

		{#if config.enabled}
			<hr class="border-gray-100 dark:border-gray-850" />
			<div>
				<div class="mb-1 text-xs font-medium">API URL</div>
				<input
					class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:bg-gray-850 outline-none"
					bind:value={config.api_url}
					placeholder="https://api.midjourney.com"
				/>
			</div>
			<div>
				<div class="mb-1 text-xs font-medium">API Key</div>
				<input
					type="password"
					class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:bg-gray-850 outline-none"
					bind:value={config.api_key}
					placeholder="输入API密钥"
				/>
			</div>
			<div class="grid grid-cols-2 gap-3">
				<div>
					<div class="mb-1 text-xs font-medium">Fast模式积分</div>
					<input
						type="number"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:bg-gray-850 outline-none"
						bind:value={config.fast_credits}
						min="1"
					/>
				</div>
				<div>
					<div class="mb-1 text-xs font-medium">Relax模式积分</div>
					<input
						type="number"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:bg-gray-850 outline-none"
						bind:value={config.relax_credits}
						min="1"
					/>
				</div>
				<div>
					<div class="mb-1 text-xs font-medium">Turbo模式积分</div>
					<input
						type="number"
						class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:bg-gray-850 outline-none"
						bind:value={config.turbo_credits}
						min="1"
					/>
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full disabled:opacity-50"
			on:click={handleSave}
			disabled={loading || saving}
		>
			{#if loading}
				加载中...
			{:else if saving}
				保存中...
			{:else}
				保存配置
			{/if}
		</button>
	</div>
</div>
