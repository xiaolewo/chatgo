<script>
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { user } from '$lib/stores';
	import Switch from '$lib/components/common/Switch.svelte';
	import { getPptConfig, updatePptConfig, verifyPptConnection } from '$lib/apis/ppt.js';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	let loading = false;
	let saving = false;
	let verifying = false;
	let connectionStatus = null; // null, 'success', 'failed'

	let config = {
		enabled: false,
		api_url: 'https://open.docmee.cn',
		api_key: '',
		credits_per_ppt: 10
	};

	// 加载配置
	const loadConfig = async () => {
		if (!$user?.token) return;

		loading = true;
		try {
			const response = await getPptConfig($user.token);
			config = { ...config, ...response };
			console.log('PPT配置加载成功, 状态:', config.enabled ? '已启用' : '未启用');
		} catch (error) {
			console.error('加载PPT配置失败:', error);
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
			const response = await updatePptConfig($user.token, config);
			console.log('PPT配置保存成功:', config);

			// 保存成功后重新加载配置确保状态一致
			await loadConfig();

			// 显示成功消息
			toast.success(`PPT功能已${config.enabled ? '启用' : '禁用'}，配置已保存`);
			dispatch('save');
		} catch (error) {
			console.error('保存PPT配置失败:', error);
			toast.error('保存配置失败: ' + error.message);
		} finally {
			saving = false;
		}
	};

	// 验证连接
	const verifyConnection = async () => {
		if (!config.api_key.trim() || !config.api_url.trim()) {
			toast.error('请先填写API地址和API密钥');
			return;
		}

		verifying = true;
		connectionStatus = null;
		try {
			const result = await verifyPptConnection(config.api_url, config.api_key);
			connectionStatus = 'success';
			toast.success('连接验证成功');
		} catch (error) {
			connectionStatus = 'failed';
			toast.error('连接验证失败: ' + error.message);
		} finally {
			verifying = false;
		}
	};

	onMount(loadConfig);
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class="space-y-3">
		<!-- 标题 -->
		<div class="flex items-center justify-between">
			<div class="flex items-center space-x-3">
				<div class="text-xl font-semibold">PPT生成配置</div>
				<div
					class="text-sm px-2 py-1 rounded-full {config.enabled
						? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
						: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}"
				>
					{config.enabled ? '已启用' : '未启用'}
				</div>
			</div>
			<Switch bind:state={config.enabled} />
		</div>

		<hr />

		<!-- API配置 -->
		<div class="space-y-4">
			<div>
				<div class="mb-2 text-sm font-medium">API地址</div>
				<input
					bind:value={config.api_url}
					placeholder="https://open.docmee.cn"
					class="w-full rounded-lg px-3 py-2.5 text-sm bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 focus:outline-none focus:border-primary-500"
					required
				/>
			</div>

			<div>
				<div class="mb-2 text-sm font-medium">API密钥</div>
				<input
					bind:value={config.api_key}
					type="password"
					placeholder="请输入API密钥"
					class="w-full rounded-lg px-3 py-2.5 text-sm bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 focus:outline-none focus:border-primary-500"
					required
				/>
				<div class="text-xs text-gray-500 mt-1">从文多多开放平台获取API密钥</div>
			</div>

			<div>
				<div class="mb-2 text-sm font-medium">每PPT消耗积分</div>
				<input
					bind:value={config.credits_per_ppt}
					type="number"
					min="1"
					placeholder="10"
					class="w-full rounded-lg px-3 py-2.5 text-sm bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 focus:outline-none focus:border-primary-500"
					required
				/>
			</div>
		</div>

		<!-- 连接测试 -->
		<div class="flex items-center gap-2">
			<button
				on:click={verifyConnection}
				disabled={verifying || !config.api_key.trim() || !config.api_url.trim()}
				class="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-100 text-blue-600 hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
			>
				{#if verifying}
					<svg class="w-3 h-3 animate-spin" viewBox="0 0 24 24">
						<circle
							class="opacity-25"
							cx="12"
							cy="12"
							r="10"
							stroke="currentColor"
							stroke-width="4"
							fill="none"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					验证中...
				{:else}
					测试连接
				{/if}
			</button>

			{#if connectionStatus === 'success'}
				<div class="flex items-center gap-1 text-green-600">
					<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
							clip-rule="evenodd"
						/>
					</svg>
					连接成功
				</div>
			{:else if connectionStatus === 'failed'}
				<div class="flex items-center gap-1 text-red-600">
					<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
							clip-rule="evenodd"
						/>
					</svg>
					连接失败
				</div>
			{/if}
		</div>

		<!-- 配置说明 -->
		<div class="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
			<div class="text-sm text-blue-800 dark:text-blue-200">
				<div class="font-medium mb-2">配置说明：</div>
				<ul class="space-y-1 text-xs">
					<li>• 需要在文多多开放平台获取API密钥</li>
					<li>• 填写配置信息后，<strong>请点击右上角开关启用PPT功能</strong></li>
					<li>• 支持多种生成方式：智能生成、文件生成、思维导图等</li>
					<li>• 用户每次生成PPT将消耗对应积分</li>
					<li>• API地址通常为：https://open.docmee.cn</li>
				</ul>
			</div>
		</div>

		{#if loading}
			<div class="flex justify-center items-center py-4">
				<div
					class="animate-spin w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full"
				></div>
			</div>
		{/if}
	</div>

	<!-- 保存按钮 -->
	<div class="flex justify-end pt-3">
		<button
			class="px-3 py-1 text-xs font-medium bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition disabled:opacity-50"
			on:click={saveHandler}
			disabled={saving}
		>
			{saving ? '保存中...' : '保存配置'}
		</button>
	</div>
</div>
