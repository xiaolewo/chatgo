<script>
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, getContext, onMount } from 'svelte';
	import { user } from '$lib/stores';
	import Switch from '$lib/components/common/Switch.svelte';
	import { getKlingConfig, updateKlingConfig, verifyKlingConnection } from '$lib/apis/kling.js';

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
		std_credits: 5,
		pro_credits: 10
	};

	// 加载配置
	const loadConfig = async () => {
		if (!$user?.token) return;

		loading = true;
		try {
			const response = await getKlingConfig($user.token);
			config = { ...config, ...response };
			console.log('可灵配置加载成功, 状态:', config.enabled ? '已启用' : '未启用');
		} catch (error) {
			console.error('加载可灵配置失败:', error);
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
			const response = await updateKlingConfig($user.token, config);
			toast.success('可灵配置保存成功');
			connectionStatus = null; // 配置改变后重置连接状态
		} catch (error) {
			console.error('保存可灵配置失败:', error);
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
			const response = await verifyKlingConnection($user.token);
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
		<!-- 服务概述 -->
		<div
			class="bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 p-6 rounded-xl border border-red-200 dark:border-red-800"
		>
			<div class="flex items-start gap-4">
				<div
					class="w-12 h-12 rounded-lg bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center flex-shrink-0"
				>
					<svg class="size-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
						/>
					</svg>
				</div>
				<div class="flex-1 min-w-0">
					<h3 class="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">可灵视频生成</h3>
					<p class="text-sm text-red-700 dark:text-red-300 mb-3">
						快手可灵AI文生视频服务，支持多种模型版本和专业的摄像机运动控制，生成高质量的AI视频内容。
					</p>
					<div class="grid grid-cols-2 gap-4 text-xs">
						<div class="space-y-1">
							<h4 class="font-medium text-red-800 dark:text-red-200">功能特色</h4>
							<ul class="space-y-0.5 text-red-600 dark:text-red-400">
								<li>• 多版本模型支持</li>
								<li>• 专业摄像机控制</li>
								<li>• 多种画面比例</li>
								<li>• 可调节视频时长</li>
							</ul>
						</div>
						<div class="space-y-1">
							<h4 class="font-medium text-red-800 dark:text-red-200">技术优势</h4>
							<ul class="space-y-0.5 text-red-600 dark:text-red-400">
								<li>• 异步任务处理</li>
								<li>• 实时状态轮询</li>
								<li>• 积分透明计费</li>
								<li>• 安全API认证</li>
							</ul>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- 基础配置 -->
		<div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
			<div class="p-6 border-b border-gray-200 dark:border-gray-700">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white">基础配置</h3>
				<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">配置可灵API连接信息</p>
			</div>

			<div class="p-6 space-y-4">
				<!-- 服务启用开关 -->
				<div class="flex items-center justify-between">
					<div>
						<label class="text-sm font-medium text-gray-700 dark:text-gray-300">启用可灵服务</label>
						<p class="text-xs text-gray-500 dark:text-gray-400">
							启用后用户可以使用可灵视频生成功能
						</p>
					</div>
					<Switch bind:state={config.enabled} />
				</div>

				<!-- API URL -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						API Base URL <span class="text-red-500">*</span>
					</label>
					<input
						bind:value={config.api_url}
						type="url"
						placeholder="https://api.example.com"
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 dark:bg-gray-700 dark:text-white"
						required
					/>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">可灵API服务的基础URL地址</p>
				</div>

				<!-- API Key -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						API Key <span class="text-red-500">*</span>
					</label>
					<input
						bind:value={config.api_key}
						type="password"
						placeholder="Bearer token..."
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 dark:bg-gray-700 dark:text-white"
						required
					/>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">从可灵服务提供商获取的API密钥</p>
				</div>

				<!-- 连接验证 -->
				<div class="pt-4 border-t border-gray-200 dark:border-gray-700">
					<button
						type="button"
						on:click={verifyConnection}
						disabled={verifying || !config.api_url.trim() || !config.api_key.trim()}
						class="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
					>
						{#if verifying}
							<svg class="animate-spin size-4" fill="none" viewBox="0 0 24 24">
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
									d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								></path>
							</svg>
							<span>验证中...</span>
						{:else}
							<svg class="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
							<span>验证连接</span>
						{/if}
					</button>

					{#if connectionStatus === 'success'}
						<div class="mt-2 flex items-center gap-2 text-green-600 dark:text-green-400">
							<svg class="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
							<span class="text-sm">连接成功！API配置正确</span>
						</div>
					{:else if connectionStatus === 'failed'}
						<div class="mt-2 flex items-center gap-2 text-red-600 dark:text-red-400">
							<svg class="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
								/>
							</svg>
							<span class="text-sm">连接失败，请检查配置</span>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- 计费配置 -->
		<div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
			<div class="p-6 border-b border-gray-200 dark:border-gray-700">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white">计费配置</h3>
				<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">设置不同生成模式的积分消耗</p>
			</div>

			<div class="p-6 space-y-4">
				<!-- 标准模式积分 -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						标准模式积分消耗
					</label>
					<div class="flex items-center gap-3">
						<input
							bind:value={config.std_credits}
							type="number"
							min="1"
							max="100"
							class="w-24 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 dark:bg-gray-700 dark:text-white"
						/>
						<span class="text-sm text-gray-600 dark:text-gray-400">积分/次</span>
					</div>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
						标准模式性价比高，推荐用于基础视频生成
					</p>
				</div>

				<!-- 专家模式积分 -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						专家模式积分消耗
					</label>
					<div class="flex items-center gap-3">
						<input
							bind:value={config.pro_credits}
							type="number"
							min="1"
							max="100"
							class="w-24 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 dark:bg-gray-700 dark:text-white"
						/>
						<span class="text-sm text-gray-600 dark:text-gray-400">积分/次</span>
					</div>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
						专家模式质量更高，适用于高品质视频需求
					</p>
				</div>

				<!-- 计费说明 -->
				<div
					class="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800"
				>
					<h4 class="text-sm font-medium text-amber-800 dark:text-amber-200 mb-2">计费说明</h4>
					<ul class="text-xs text-amber-700 dark:text-amber-300 space-y-1">
						<li>• 提交任务时预扣积分，任务失败时自动退还</li>
						<li>• 积分消耗与视频时长无关，按次计费</li>
						<li>• 专家模式生成质量更高，但消耗积分更多</li>
						<li>• 建议根据用户需求合理设置积分消耗</li>
					</ul>
				</div>
			</div>
		</div>

		<!-- API使用说明 -->
		<div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
			<div class="p-6 border-b border-gray-200 dark:border-gray-700">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white">API使用说明</h3>
			</div>

			<div class="p-6">
				<div class="space-y-4 text-sm text-gray-600 dark:text-gray-400">
					<div>
						<h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2">支持的模型版本</h4>
						<ul class="space-y-1 ml-4">
							<li>
								• <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">kling-v1</code> - 基础版本
							</li>
							<li>
								• <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">kling-v1-6</code> - 增强版本
							</li>
							<li>
								• <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">kling-v2-master</code> - 专业版本
							</li>
							<li>
								• <code class="bg-gray-100 dark:bg-gray-700 px-1 rounded">kling-v2-1-master</code> -
								最新版本
							</li>
						</ul>
					</div>

					<div>
						<h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2">生成模式</h4>
						<ul class="space-y-1 ml-4">
							<li>• <strong>标准模式 (std)</strong> - 性价比高，基础质量</li>
							<li>• <strong>专家模式 (pro)</strong> - 高品质，生成质量更佳</li>
						</ul>
					</div>

					<div>
						<h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2">视频规格</h4>
						<ul class="space-y-1 ml-4">
							<li>• <strong>画面比例</strong>: 16:9 (横屏)、9:16 (竖屏)、1:1 (方形)</li>
							<li>• <strong>视频时长</strong>: 5秒、10秒</li>
							<li>• <strong>提示词长度</strong>: 最多2500个字符</li>
						</ul>
					</div>

					<div>
						<h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2">摄像机控制</h4>
						<ul class="space-y-1 ml-4">
							<li>• <strong>简单运镜</strong> - 6选1基础运镜控制</li>
							<li>• <strong>预设运镜</strong> - 下移拉远、推进上移、左右旋转等</li>
							<li>• <strong>运镜参数</strong> - 支持水平、垂直、旋转、变焦等精细控制</li>
						</ul>
					</div>
				</div>
			</div>
		</div>

		<!-- 保存按钮 -->
		<div class="flex justify-end">
			<button
				type="button"
				on:click={saveHandler}
				disabled={saving || loading}
				class="flex items-center gap-2 px-6 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed"
			>
				{#if saving}
					<svg class="animate-spin size-4" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					<span>保存中...</span>
				{:else if loading}
					<span>加载中...</span>
				{:else}
					<svg class="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M5 13l4 4L19 7"
						/>
					</svg>
					<span>保存配置</span>
				{/if}
			</button>
		</div>
	</div>
</div>
