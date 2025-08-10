<script>
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { user } from '$lib/stores';
	import Switch from '$lib/components/common/Switch.svelte';
	import {
		getSeedreamConfig,
		updateSeedreamConfig,
		verifySeedreamConnection
	} from '$lib/apis/seedream.js';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;
	let saving = false;
	let verifying = false;
	let connectionStatus = null; // null, 'success', 'failed'

	let config = {
		enabled: false,
		api_url: '',
		api_key: '',
		credits_per_generation: 1
	};

	// 加载配置
	const loadConfig = async () => {
		if (!$user?.token) return;

		loading = true;
		try {
			const response = await getSeedreamConfig($user.token);
			config = { ...config, ...response };
			console.log('即梦3.0配置加载成功, 状态:', config.enabled ? '已启用' : '未启用');
		} catch (error) {
			console.error('加载即梦3.0配置失败:', error);
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
			const response = await updateSeedreamConfig($user.token, config);
			toast.success('即梦3.0配置保存成功');
			dispatch('save');
			console.log('配置保存响应:', response);
		} catch (error) {
			console.error('保存即梦3.0配置失败:', error);
			toast.error('保存失败: ' + error.message);
		} finally {
			saving = false;
		}
	};

	// 验证连接
	const verifyConnection = async () => {
		if (!validateConfig()) return;

		verifying = true;
		connectionStatus = null;

		try {
			// 先保存配置
			await updateSeedreamConfig($user.token, config);

			// 然后验证连接
			const response = await verifySeedreamConnection($user.token);

			if (response.status === 'success') {
				connectionStatus = 'success';
				toast.success('连接验证成功！');
			} else {
				connectionStatus = 'failed';
				toast.error(`连接验证失败: ${response.message}`);
			}
		} catch (error) {
			connectionStatus = 'failed';
			console.error('验证即梦3.0连接失败:', error);
			toast.error('验证失败: ' + error.message);
		} finally {
			verifying = false;
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
			if (!config.credits_per_generation || config.credits_per_generation < 1) {
				toast.error('每次生成积分消耗必须大于0');
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
			<div class="mb-1 text-sm font-medium">即梦3.0 设置</div>
			<div class="text-xs text-gray-500 mb-3">
				基于火山引擎视觉智能的新一代文生图模型，支持2K高清输出
			</div>
			<div class="py-1 flex w-full justify-between">
				<div class="self-center text-xs font-medium">启用即梦3.0</div>
				<Switch bind:state={config.enabled} />
			</div>
		</div>

		{#if config.enabled}
			<hr class="border-gray-100 dark:border-gray-850" />

			<div
				class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3"
			>
				<div class="text-xs font-medium text-blue-800 dark:text-blue-200 mb-2">配置说明</div>
				<div class="text-xs text-blue-700 dark:text-blue-300 space-y-1">
					<div>• API URL：平台提供的Base_URL，例如 https://api.example.com</div>
					<div>• API Key：平台生成的Bearer token，格式为 sk-xxxxxxx</div>
					<div>• 积分消耗：官方定价0.2元/次，可根据实际情况调整积分消耗</div>
				</div>
			</div>

			<div>
				<div class="mb-1 text-xs font-medium">API URL</div>
				<input
					class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:bg-gray-850 outline-none"
					bind:value={config.api_url}
					placeholder="https://api.example.com（平台Base_URL）"
				/>
				<div class="text-xs text-gray-500 mt-1">
					请填写平台提供的Base_URL，系统会自动添加/volcv/v1路径
				</div>
			</div>

			<div>
				<div class="mb-1 text-xs font-medium">API Key</div>
				<input
					type="password"
					class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:bg-gray-850 outline-none"
					bind:value={config.api_key}
					placeholder="sk-xxxxxxx（Bearer token）"
				/>
				<div class="text-xs text-gray-500 mt-1">请填写平台生成的API Key，格式通常为sk-开头</div>
			</div>

			<div>
				<div class="mb-1 text-xs font-medium">每次生成积分消耗</div>
				<input
					type="number"
					class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:bg-gray-850 outline-none"
					bind:value={config.credits_per_generation}
					min="1"
					placeholder="1"
				/>
				<div class="text-xs text-gray-500 mt-1">
					官方定价0.2元/次，建议设置1积分=0.2元，可根据实际情况调整
				</div>
			</div>

			<div class="flex space-x-2">
				<button
					class="flex-1 px-3 py-2 text-sm bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-800 dark:text-blue-200 rounded-lg transition disabled:opacity-50"
					on:click={verifyConnection}
					disabled={verifying || !config.api_url.trim() || !config.api_key.trim()}
				>
					{#if verifying}
						验证中...
					{:else}
						验证连接
					{/if}
				</button>

				{#if connectionStatus === 'success'}
					<div
						class="flex items-center px-3 py-2 bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300 rounded-lg text-xs"
					>
						✓ 连接成功
					</div>
				{:else if connectionStatus === 'failed'}
					<div
						class="flex items-center px-3 py-2 bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300 rounded-lg text-xs"
					>
						✗ 连接失败
					</div>
				{/if}
			</div>

			<div
				class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3"
			>
				<div class="text-xs font-medium text-amber-800 dark:text-amber-200 mb-2">功能特性</div>
				<div class="text-xs text-amber-700 dark:text-amber-300 space-y-1">
					<div>• 逼真人像质感：人像质感的真实重塑与情绪表达</div>
					<div>• 强大文字响应：精准的字号、字体和字重响应</div>
					<div>• 高清大图呈现：支持2K输出，图像清晰度显著提升</div>
					<div>• 影视质感增强：语义理解和影视质感的增强</div>
					<div>• 同步生成：无需轮询，直接返回结果</div>
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
