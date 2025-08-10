<script>
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { user } from '$lib/stores';
	import Switch from '$lib/components/common/Switch.svelte';
	import { getJimengConfig, updateJimengConfig, verifyJimengConnection } from '$lib/apis/jimeng.js';

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
		credits_5s: 5,
		credits_10s: 10
	};

	// 加载配置
	const loadConfig = async () => {
		if (!$user?.token) return;

		loading = true;
		try {
			const response = await getJimengConfig($user.token);
			config = { ...config, ...response };
			console.log('即梦配置加载成功, 状态:', config.enabled ? '已启用' : '未启用');
		} catch (error) {
			console.error('加载即梦配置失败:', error);
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
			const response = await updateJimengConfig($user.token, config);
			toast.success('即梦配置保存成功');
			connectionStatus = null; // 配置改变后重置连接状态
		} catch (error) {
			console.error('保存即梦配置失败:', error);
			toast.error('保存配置失败: ' + error.message);
		} finally {
			saving = false;
		}
	};

	// 验证连接
	const verifyConnection = async () => {
		if (!$user?.token) {
			toast.error('未登录，无法验证连接');
			return;
		}

		if (!config.api_url.trim() || !config.api_key.trim()) {
			toast.error('请先填写API URL和API Key');
			return;
		}

		verifying = true;
		connectionStatus = null;

		try {
			const response = await verifyJimengConnection($user.token);
			connectionStatus = response.status === 'success' ? 'success' : 'failed';

			if (connectionStatus === 'success') {
				toast.success('连接验证成功');
			} else {
				toast.error('连接验证失败: ' + response.message);
			}
		} catch (error) {
			console.error('验证连接失败:', error);
			connectionStatus = 'failed';
			toast.error('验证连接失败: ' + error.message);
		} finally {
			verifying = false;
		}
	};

	onMount(() => {
		loadConfig();
	});
</script>

<div class="w-full max-w-2xl mx-auto">
	<div class="space-y-6">
		<!-- 启用状态 -->
		<div class="flex items-center justify-between">
			<div>
				<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">启用即梦视频服务</h3>
				<p class="text-sm text-gray-500 dark:text-gray-400">启用后用户可以使用即梦生成视频</p>
			</div>
			<Switch bind:state={config.enabled} />
		</div>

		{#if config.enabled}
			<!-- API配置 -->
			<div class="space-y-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
				<h4 class="font-medium text-gray-900 dark:text-gray-100">API配置</h4>

				<!-- API URL -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						API URL
					</label>
					<input
						type="text"
						bind:value={config.api_url}
						placeholder="https://api.example.com"
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
					/>
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						即梦API的基础URL，不包含路径部分
					</p>
				</div>

				<!-- API Key -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						API Key
					</label>
					<input
						type="password"
						bind:value={config.api_key}
						placeholder="Bearer token"
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
					/>
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">用于验证API请求的Bearer token</p>
				</div>

				<!-- 验证连接按钮 -->
				<div>
					<button
						on:click={verifyConnection}
						disabled={verifying || !config.api_url || !config.api_key}
						class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{#if verifying}
							<span class="flex items-center">
								<svg
									class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
								>
									<circle
										class="opacity-25"
										cx="12"
										cy="12"
										r="10"
										stroke="currentColor"
										stroke-width="4"
									></circle>
									<path
										class="opacity-75"
										fill="currentColor"
										d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
									></path>
								</svg>
								验证中...
							</span>
						{:else}
							验证连接
						{/if}
					</button>

					{#if connectionStatus === 'success'}
						<span class="ml-3 text-green-600">✓ 连接成功</span>
					{:else if connectionStatus === 'failed'}
						<span class="ml-3 text-red-600">✗ 连接失败</span>
					{/if}
				</div>
			</div>

			<!-- 积分配置 -->
			<div class="space-y-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
				<h4 class="font-medium text-gray-900 dark:text-gray-100">积分消耗配置</h4>

				<!-- 5秒视频积分 -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						5秒视频积分消耗
					</label>
					<input
						type="number"
						bind:value={config.credits_5s}
						min="1"
						max="100"
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
					/>
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">生成5秒视频所需的积分数量</p>
				</div>

				<!-- 10秒视频积分 -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						10秒视频积分消耗
					</label>
					<input
						type="number"
						bind:value={config.credits_10s}
						min="1"
						max="100"
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
					/>
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">生成10秒视频所需的积分数量</p>
				</div>
			</div>
		{/if}

		<!-- 保存按钮 -->
		<div class="flex justify-end">
			<button
				on:click={saveHandler}
				disabled={saving || loading}
				class="px-6 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
			>
				{#if saving}
					<span class="flex items-center">
						<svg
							class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
						>
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							></circle>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							></path>
						</svg>
						保存中...
					</span>
				{:else}
					保存配置
				{/if}
			</button>
		</div>
	</div>
</div>
