<script>
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user, creditName, showSidebar, mobile } from '$lib/stores';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';

	// 可灵 APIs
	import {
		generateVideo as klingGenerateVideo,
		getTaskStatus as klingGetTaskStatus,
		getUserTasks as klingGetUserTasks,
		getKlingConfig,
		getUserCredits as klingGetUserCredits,
		deleteTask as klingDeleteTask,
		TASK_STATUS as KLING_TASK_STATUS,
		KLING_MODELS,
		GENERATION_MODES,
		ASPECT_RATIOS as KLING_ASPECT_RATIOS,
		DURATIONS as KLING_DURATIONS,
		CAMERA_TYPES,
		CAMERA_CONFIG_OPTIONS,
		getModeLabel,
		getStatusText as klingGetStatusText,
		getStatusColor as klingGetStatusColor,
		formatTime,
		downloadVideo as klingDownloadVideo,
		buildGenerateRequest as klingBuildGenerateRequest,
		validateCameraConfig
	} from '$lib/apis/kling.js';

	// 即梦 APIs
	import {
		generateVideo as jimengGenerateVideo,
		getTaskStatus as jimengGetTaskStatus,
		getUserTasks as jimengGetUserTasks,
		getJimengConfig,
		getUserCredits as jimengGetUserCredits,
		deleteTask as jimengDeleteTask,
		TASK_STATUS as JIMENG_TASK_STATUS,
		DURATIONS as JIMENG_DURATIONS,
		ASPECT_RATIOS as JIMENG_ASPECT_RATIOS,
		getStatusText as jimengGetStatusText,
		getStatusColor as jimengGetStatusColor,
		downloadVideo as jimengDownloadVideo,
		buildGenerateRequest as jimengBuildGenerateRequest,
		getDurationLabel,
		formatTime as jimengFormatTime
	} from '$lib/apis/jimeng.js';

	const i18n = getContext('i18n');

	// 全局状态
	let loaded = false;
	let query = '';
	let generating = false;
	let prompt = '';
	let negativePrompt = '';
	let selectedService = 'kling'; // 'kling' or 'jimeng'

	// 服务配置和用户状态
	let klingConfig = null;
	let jimengConfig = null;
	let userCredits = 0;
	let pollingIntervals = new Map(); // 存储轮询任务的定时器

	// 生成参数
	let selectedModel = 'kling-v1';
	let selectedMode = 'std';
	let selectedAspectRatio = '16:9';
	let selectedDuration = '5';
	let cfgScale = 0.5;

	// 摄像机控制
	let enableCameraControl = false;
	let cameraType = 'simple';
	let cameraConfig = {
		horizontal: 0,
		vertical: 0,
		pan: 0,
		tilt: 0,
		roll: 0,
		zoom: 0
	};

	// 视频历史
	let videoHistory = [];
	let filteredVideos = [];
	let sortBy = 'latest';

	// 获取对应的积分消耗
	const getCreditsNeeded = () => {
		if (selectedService === 'kling') {
			if (!klingConfig) return null;
			return selectedMode === 'pro' ? klingConfig.pro_credits : klingConfig.std_credits;
		} else {
			if (!jimengConfig) return null;
			return selectedDuration === 10 ? jimengConfig.credits_10s : jimengConfig.credits_5s;
		}
	};

	// 加载配置和数据
	const loadConfigs = async () => {
		try {
			if ($user?.token) {
				// 并行加载配置和积分
				const [klingConfigResult, jimengConfigResult, creditsResult] = await Promise.all([
					getKlingConfig($user.token).catch((e) => {
						console.error('加载可灵配置失败:', e);
						return null;
					}),
					getJimengConfig($user.token).catch((e) => {
						console.error('加载即梦配置失败:', e);
						return null;
					}),
					klingGetUserCredits($user.token).catch((e) => {
						console.error('加载用户积分失败:', e);
						return { credits: 0 };
					})
				]);

				klingConfig = klingConfigResult;
				jimengConfig = jimengConfigResult;
				userCredits = creditsResult?.credits || 0;
			}
		} catch (error) {
			console.error('加载配置失败:', error);
		}
	};

	// 加载用户任务
	const loadUserTasks = async () => {
		try {
			if ($user?.token) {
				// 并行加载两个服务的任务
				const [klingTasks, jimengTasks] = await Promise.all([
					klingGetUserTasks($user.token).catch((e) => {
						console.error('加载可灵任务失败:', e);
						return [];
					}),
					jimengGetUserTasks($user.token).catch((e) => {
						console.error('加载即梦任务失败:', e);
						return [];
					})
				]);

				// 处理可灵任务
				const klingVideos = klingTasks.map((task) => {
					let displayStatus = 'completed';
					let displayMessage = task.task_status_msg || '已完成';

					// 根据任务状态设置显示状态
					if (
						task.status === KLING_TASK_STATUS.PROCESSING ||
						task.status === KLING_TASK_STATUS.SUBMITTED
					) {
						displayStatus = 'generating';
						displayMessage = task.task_status_msg || '正在生成视频...';
					} else if (task.status === KLING_TASK_STATUS.FAILED) {
						displayStatus = 'failed';
						displayMessage = task.task_status_msg || '生成失败';
					}

					return {
						id: `kling-${task.task_id}`,
						task_id: task.task_id,
						service: 'kling',
						serviceName: '可灵',
						prompt: task.prompt,
						negative_prompt: task.negative_prompt,
						model: task.model_name,
						mode: task.mode,
						aspect_ratio: task.aspect_ratio,
						duration: task.duration,
						cfg_scale: task.cfg_scale,
						video_url: task.video_url,
						video_id: task.video_id,
						video_duration: task.video_duration,
						status: displayStatus,
						message: displayMessage,
						credits_used: task.credits_used,
						created_at: task.created_at,
						updated_at: task.updated_at
					};
				});

				// 处理即梦任务
				const jimengVideos = jimengTasks.map((task) => {
					let displayStatus = 'completed';
					let displayMessage = task.fail_reason || '已完成';

					// 根据任务状态设置显示状态
					if (
						task.status === JIMENG_TASK_STATUS.IN_PROGRESS ||
						task.status === JIMENG_TASK_STATUS.QUEUED ||
						task.status === JIMENG_TASK_STATUS.SUBMITTED
					) {
						displayStatus = 'generating';
						displayMessage = '正在生成视频...';
					} else if (task.status === JIMENG_TASK_STATUS.FAILURE) {
						displayStatus = 'failed';
						displayMessage = task.fail_reason || '生成失败';
					} else if (task.status === JIMENG_TASK_STATUS.SUCCESS) {
						displayStatus = 'completed';
						displayMessage = '已完成';
					}

					return {
						id: `jimeng-${task.task_id}`,
						task_id: task.task_id,
						service: 'jimeng',
						serviceName: '即梦',
						prompt: task.prompt,
						image_url: task.image_url,
						aspect_ratio: task.aspect_ratio,
						duration: task.duration,
						cfg_scale: task.cfg_scale,
						video_url: task.video_url,
						video_id: task.video_id,
						status: displayStatus,
						message: displayMessage,
						credits_used: task.credits_used,
						created_at: task.created_at,
						updated_at: task.updated_at
					};
				});

				// 合并所有任务
				videoHistory = [...klingVideos, ...jimengVideos];

				// 为正在生成的任务启动轮询
				videoHistory.forEach((video) => {
					if (video.status === 'generating') {
						startPolling(video.task_id, video.service);
					}
				});

				filterAndSortVideos();
			}
		} catch (error) {
			console.error('加载用户任务失败:', error);
			toast.error('加载视频历史失败');
		}
	};

	// 启动轮询任务状态
	const startPolling = (taskId, service = 'kling') => {
		if (pollingIntervals.has(taskId)) return; // 避免重复轮询

		const interval = setInterval(async () => {
			try {
				console.log(`轮询任务 ${taskId} (${service}) 状态...`);
				const taskStatus =
					service === 'jimeng'
						? await jimengGetTaskStatus($user.token, taskId)
						: await klingGetTaskStatus($user.token, taskId);
				console.log(`任务 ${taskId} 状态响应:`, taskStatus);

				// 更新本地任务状态
				const videoIndex = videoHistory.findIndex((v) => v.task_id === taskId);
				if (videoIndex !== -1) {
					const video = videoHistory[videoIndex];
					const oldStatus = video.status;

					console.log(`任务 ${taskId}: ${oldStatus} -> ${taskStatus.status}`);

					const isCompleted =
						service === 'jimeng'
							? taskStatus.status === JIMENG_TASK_STATUS.SUCCESS
							: taskStatus.status === KLING_TASK_STATUS.SUCCEED;

					const isFailed =
						service === 'jimeng'
							? taskStatus.status === JIMENG_TASK_STATUS.FAILURE
							: taskStatus.status === KLING_TASK_STATUS.FAILED;

					if (isCompleted) {
						// 任务完成
						console.log(`任务 ${taskId} 完成，视频URL: ${taskStatus.video_url}`);
						video.status = 'completed';
						video.message = '视频生成完成';
						video.video_url = taskStatus.video_url;
						video.video_id = taskStatus.video_id;
						video.video_duration = taskStatus.video_duration;
						video.updated_at = taskStatus.updated_at;

						// 停止轮询
						clearInterval(interval);
						pollingIntervals.delete(taskId);

						toast.success('视频生成完成！');
					} else if (isFailed) {
						// 任务失败
						console.log(`任务 ${taskId} 失败: ${taskStatus.task_status_msg}`);
						video.status = 'failed';
						video.message = taskStatus.task_status_msg || '生成失败';
						video.updated_at = taskStatus.updated_at;

						// 停止轮询
						clearInterval(interval);
						pollingIntervals.delete(taskId);

						toast.error(`视频生成失败: ${video.message}`);
					} else {
						// 更新处理状态
						console.log(`任务 ${taskId} 处理中: ${taskStatus.task_status_msg}`);
						video.message = taskStatus.task_status_msg || '正在生成视频...';
						video.updated_at = taskStatus.updated_at;
					}

					videoHistory[videoIndex] = video;
					filterAndSortVideos();
				}
			} catch (error) {
				console.error(`轮询任务 ${taskId} 状态失败:`, error);
			}
		}, 30000); // 每30秒轮询一次（回调为主，轮询为备用）

		pollingIntervals.set(taskId, interval);
	};

	// 生成视频
	const handleGenerate = async () => {
		if (!prompt.trim()) {
			toast.error('请输入提示词');
			return;
		}

		// 检查服务是否启用
		if (selectedService === 'kling' && !klingConfig?.enabled) {
			toast.error('可灵服务未启用，请联系管理员');
			return;
		}
		if (selectedService === 'jimeng' && !jimengConfig?.enabled) {
			toast.error('即梦服务未启用，请联系管理员');
			return;
		}

		const requiredCredits = getCreditsNeeded();
		if (requiredCredits === null) {
			toast.error('服务配置未加载，请稍后重试');
			return;
		}

		if (userCredits < requiredCredits) {
			toast.error(
				`积分不足，需要${requiredCredits}${$creditName}，当前仅有${userCredits}${$creditName}`
			);
			return;
		}

		// 验证摄像机控制配置（仅可灵）
		if (selectedService === 'kling' && enableCameraControl && cameraType === 'simple') {
			if (!validateCameraConfig(cameraConfig)) {
				toast.error('摄像机控制配置错误：简单运镜模式下只能有一个参数不为0');
				return;
			}
		}

		try {
			generating = true;

			let result;
			if (selectedService === 'jimeng') {
				// 即梦视频生成
				const generateParams = jimengBuildGenerateRequest({
					prompt: prompt.trim(),
					aspect_ratio: selectedAspectRatio,
					duration: parseInt(selectedDuration),
					cfg_scale: cfgScale
				});

				result = await jimengGenerateVideo($user.token, generateParams);

				if (result.task_id) {
					// 创建新的历史记录项
					const newVideo = {
						id: `jimeng-${result.task_id}`,
						task_id: result.task_id,
						service: 'jimeng',
						serviceName: '即梦',
						prompt: prompt.trim(),
						aspect_ratio: selectedAspectRatio,
						duration: parseInt(selectedDuration),
						cfg_scale: cfgScale,
						video_url: null,
						video_id: null,
						status: 'generating',
						message: result.message || '正在生成视频...',
						credits_used: result.credits_used,
						created_at: Date.now(),
						updated_at: Date.now()
					};

					videoHistory = [newVideo, ...videoHistory];
					filterAndSortVideos();
					userCredits -= result.credits_used;
					startPolling(result.task_id, 'jimeng');
				}
			} else {
				// 可灵视频生成
				const generateParams = klingBuildGenerateRequest({
					model_name: selectedModel,
					prompt: prompt.trim(),
					negative_prompt: negativePrompt.trim() || null,
					cfg_scale: cfgScale,
					mode: selectedMode,
					aspect_ratio: selectedAspectRatio,
					duration: selectedDuration,
					camera_control: enableCameraControl
						? {
								type: cameraType,
								config: cameraType === 'simple' ? cameraConfig : null
							}
						: null
				});

				result = await klingGenerateVideo($user.token, generateParams);

				if (result.task_id) {
					// 创建新的历史记录项
					const newVideo = {
						id: `kling-${result.task_id}`,
						task_id: result.task_id,
						service: 'kling',
						serviceName: '可灵',
						prompt: prompt.trim(),
						negative_prompt: negativePrompt.trim() || null,
						model: selectedModel,
						mode: selectedMode,
						aspect_ratio: selectedAspectRatio,
						duration: selectedDuration,
						cfg_scale: cfgScale,
						video_url: null,
						video_id: null,
						video_duration: null,
						status: 'generating',
						message: result.message || '正在生成视频...',
						credits_used: result.credits_used,
						created_at: Date.now(),
						updated_at: Date.now()
					};

					videoHistory = [newVideo, ...videoHistory];
					filterAndSortVideos();
					userCredits -= result.credits_used;
					startPolling(result.task_id, 'kling');
				}
			}

			if (result.task_id) {
				toast.success('视频生成任务已提交，请稍等...');
			}
		} catch (error) {
			console.error('生成视频失败:', error);
			toast.error(`生成视频失败: ${error.message}`);
		} finally {
			generating = false;
		}
	};

	// 筛选和排序视频
	const filterAndSortVideos = () => {
		let filtered = videoHistory;

		// 搜索筛选
		if (query.trim()) {
			const searchQuery = query.toLowerCase();
			filtered = filtered.filter(
				(video) =>
					video.prompt?.toLowerCase().includes(searchQuery) ||
					video.negative_prompt?.toLowerCase().includes(searchQuery)
			);
		}

		// 排序
		switch (sortBy) {
			case 'latest':
				filtered.sort((a, b) => b.created_at - a.created_at);
				break;
			case 'oldest':
				filtered.sort((a, b) => a.created_at - b.created_at);
				break;
			case 'status':
				filtered.sort((a, b) => {
					const statusOrder = { generating: 0, completed: 1, failed: 2 };
					return (statusOrder[a.status] || 3) - (statusOrder[b.status] || 3);
				});
				break;
		}

		filteredVideos = filtered;
	};

	// 强制刷新任务状态
	const forceRefreshTask = async (video) => {
		try {
			console.log(`强制刷新任务 ${video.task_id} 状态...`);
			const taskStatus = await getTaskStatus($user.token, video.task_id);
			console.log(`强制刷新结果:`, taskStatus);

			// 检查时间戳是否有变化
			const oldTimestamp = video.updated_at;
			const newTimestamp = taskStatus.updated_at;
			console.log(
				`时间戳对比: ${oldTimestamp} -> ${newTimestamp}, 是否有变化: ${oldTimestamp !== newTimestamp}`
			);

			if (oldTimestamp === newTimestamp) {
				console.warn('⚠️ 警告: 时间戳没有变化，可能后端没有成功查询外部API');
				toast.warning('状态没有更新，可能API配置有问题或后端服务异常');
			}

			// 更新本地任务状态
			const videoIndex = videoHistory.findIndex((v) => v.task_id === video.task_id);
			if (videoIndex !== -1) {
				const updatedVideo = videoHistory[videoIndex];

				if (taskStatus.status === KLING_TASK_STATUS.SUCCEED) {
					console.log('✅ 任务完成，更新视频信息');
					updatedVideo.status = 'completed';
					updatedVideo.message = '视频生成完成';
					updatedVideo.video_url = taskStatus.video_url;
					updatedVideo.video_id = taskStatus.video_id;
					updatedVideo.video_duration = taskStatus.video_duration;
					updatedVideo.updated_at = taskStatus.updated_at;

					// 停止该任务的轮询
					if (pollingIntervals.has(video.task_id)) {
						clearInterval(pollingIntervals.get(video.task_id));
						pollingIntervals.delete(video.task_id);
					}

					toast.success('任务状态已更新，视频生成完成！');
				} else if (taskStatus.status === KLING_TASK_STATUS.FAILED) {
					console.log('❌ 任务失败');
					updatedVideo.status = 'failed';
					updatedVideo.message = taskStatus.task_status_msg || '生成失败';
					updatedVideo.updated_at = taskStatus.updated_at;

					// 停止该任务的轮询
					if (pollingIntervals.has(video.task_id)) {
						clearInterval(pollingIntervals.get(video.task_id));
						pollingIntervals.delete(video.task_id);
					}

					toast.error('任务已失败');
				} else {
					console.log(`⏳ 任务仍在处理: ${taskStatus.status}`);
					updatedVideo.message = taskStatus.task_status_msg || '正在生成视频...';
					updatedVideo.updated_at = taskStatus.updated_at;

					if (oldTimestamp === newTimestamp) {
						toast.warning('状态未更新，可能需要检查API配置');
					} else {
						toast.info('任务仍在处理中');
					}
				}

				videoHistory[videoIndex] = updatedVideo;
				filterAndSortVideos();
			}
		} catch (error) {
			console.error(`强制刷新任务 ${video.task_id} 失败:`, error);
			console.error('错误详情:', error.message, error.stack);
			toast.error(`刷新失败: ${error.message}`);
		}
	};

	// 删除失败的任务
	const deleteFailedTask = async (video) => {
		try {
			if (video.service === 'jimeng') {
				await jimengDeleteTask($user.token, video.task_id);
			} else {
				await klingDeleteTask($user.token, video.task_id);
			}

			// 从本地历史中移除
			videoHistory = videoHistory.filter((v) => v.id !== video.id);
			filterAndSortVideos();

			toast.success('任务已删除');
		} catch (error) {
			console.error('删除任务失败:', error);
			toast.error('删除任务失败');
		}
	};

	// 复制提示词
	const copyPrompt = (video) => {
		prompt = video.prompt;
		negativePrompt = video.negative_prompt || '';
		toast.success('提示词已复制');
	};

	// 下载视频
	const handleDownload = async (video) => {
		try {
			const filename = `${video.service || 'video'}-${video.task_id}-${Date.now()}.mp4`;
			if (video.service === 'jimeng') {
				await jimengDownloadVideo(video.video_url, filename);
			} else {
				await klingDownloadVideo(video.video_url, filename);
			}
			toast.success('视频下载完成');
		} catch (error) {
			console.error('下载失败:', error);
			toast.error('下载失败');
		}
	};

	// 摄像机控制配置变化处理
	const handleCameraConfigChange = (key, value) => {
		// 简单运镜模式下，只能有一个参数不为0
		if (cameraType === 'simple') {
			// 重置所有参数为0
			Object.keys(cameraConfig).forEach((k) => {
				cameraConfig[k] = k === key ? value : 0;
			});
		} else {
			cameraConfig[key] = value;
		}
	};

	// 重置摄像机控制
	const resetCameraControl = () => {
		Object.keys(cameraConfig).forEach((key) => {
			cameraConfig[key] = 0;
		});
	};

	// 组件挂载
	onMount(async () => {
		await loadConfigs();
		await loadUserTasks();
		loaded = true;
	});

	// 响应式更新
	$: {
		if (query !== undefined) {
			filterAndSortVideos();
		}
	}

	$: {
		if (sortBy !== undefined) {
			filterAndSortVideos();
		}
	}

	// 组件销毁时清理轮询
	import { onDestroy } from 'svelte';
	onDestroy(() => {
		pollingIntervals.forEach((interval) => clearInterval(interval));
		pollingIntervals.clear();
	});
</script>

<!-- 页面内容 -->
<div class="size-full flex flex-col">
	<!-- 页面头部 -->
	<div class="px-2.5 flex justify-between space-x-4 bg-white dark:bg-gray-900">
		<div class="flex items-center space-x-2">
			<!-- 汉堡菜单按钮 (移动端显示) -->
			<div class="{$showSidebar ? 'md:hidden' : ''} flex items-center">
				<button
					class="cursor-pointer p-2 flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition lg:hidden"
					on:click={() => {
						showSidebar.set(!$showSidebar);
					}}
					aria-label="Toggle Sidebar"
				>
					<MenuLines />
				</button>
			</div>

			<div class="flex items-center space-x-2">
				<div class="w-8 h-8 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center">
					<svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
						/>
					</svg>
				</div>
				<h1 class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">视频生成</h1>
			</div>
		</div>

		<div class="flex items-center space-x-3">
			<!-- 积分余额显示 -->
			<div class="flex items-center space-x-2 px-3 py-1.5 bg-red-50 dark:bg-red-900/20 rounded-lg">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-4 h-4 text-red-600 dark:text-red-400"
				>
					<path
						d="M10 9a3 3 0 100-6 3 3 0 000 6zM6 8a2 2 0 11-4 0 2 2 0 014 0zM1.49 15.326a.78.78 0 01-.358-.442 3 3 0 014.308-3.516 6.484 6.484 0 00-1.905 3.959c-.023.222-.014.442.025.654a4.97 4.97 0 01-2.07-.655zM16.44 15.98a4.97 4.97 0 002.07-.654.78.78 0 00.357-.442 3 3 0 00-4.308-3.517 6.484 6.484 0 011.907 3.96 2.32 2.32 0 01-.026.654zM18 8a2 2 0 11-4 0 2 2 0 014 0zM5.304 16.19a.844.844 0 01-.277-.71 5 5 0 019.947 0 .843.843 0 01-.277.71A6.975 6.975 0 0110 18a6.974 6.974 0 01-4.696-1.81z"
					/>
				</svg>
				<span class="text-sm font-medium text-red-800 dark:text-red-200">
					{userCredits}
					{$creditName}
				</span>
			</div>
		</div>
	</div>

	<hr class="border-gray-100 dark:border-gray-850" />

	{#if !loaded}
		<div class="flex-1 flex justify-center items-center">
			<Spinner className="size-6" />
		</div>
	{:else if !klingConfig?.enabled}
		<div class="flex-1 flex items-center justify-center">
			<div class="text-center py-12">
				<div
					class="w-16 h-16 mx-auto mb-4 rounded-lg bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center"
				>
					<svg class="size-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
						/>
					</svg>
				</div>
				<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
					可灵视频生成服务未启用
				</h3>
				<p class="text-gray-600 dark:text-gray-400">请联系管理员在设置中启用可灵服务</p>
			</div>
		</div>
	{:else}
		<div class="flex-1 flex flex-col lg:flex-row overflow-hidden">
			<!-- 左侧生成面板 -->
			<div
				class="flex-none w-full lg:w-96 p-3 sm:p-4 border-b lg:border-b-0 lg:border-r border-gray-100 dark:border-gray-850 overflow-y-auto max-h-[50vh] lg:max-h-none"
			>
				<!-- 服务选择 -->
				<div class="mb-4">
					<label class="block text-sm font-medium mb-2">选择视频生成服务</label>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
						<button
							class="p-3 sm:p-4 rounded-lg border-2 transition-all text-sm sm:text-base touch-manipulation {selectedService ===
							'kling'
								? 'border-red-500 bg-red-50 dark:bg-red-900/20'
								: 'border-gray-200 dark:border-gray-700'}"
							on:click={() => (selectedService = 'kling')}
							disabled={!klingConfig?.enabled}
						>
							<div
								class="font-medium {selectedService === 'kling'
									? 'text-red-600 dark:text-red-400'
									: ''}"
							>
								可灵
							</div>
							<div class="text-xs text-gray-500 mt-1">
								{klingConfig?.enabled ? '✓ 已启用' : '✗ 未启用'}
							</div>
						</button>
						<button
							class="p-3 sm:p-4 rounded-lg border-2 transition-all text-sm sm:text-base touch-manipulation {selectedService ===
							'jimeng'
								? 'border-red-500 bg-red-50 dark:bg-red-900/20'
								: 'border-gray-200 dark:border-gray-700'}"
							on:click={() => (selectedService = 'jimeng')}
							disabled={!jimengConfig?.enabled}
						>
							<div
								class="font-medium {selectedService === 'jimeng'
									? 'text-red-600 dark:text-red-400'
									: ''}"
							>
								即梦视频
							</div>
							<div class="text-xs text-gray-500 mt-1">
								{jimengConfig?.enabled ? '✓ 已启用' : '✗ 未启用'}
							</div>
						</button>
					</div>
				</div>

				<!-- 积分消耗提示 -->
				<div
					class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800"
				>
					<div class="text-xs text-gray-600 dark:text-gray-400">
						当前服务: <span class="font-medium">
							{selectedService === 'jimeng' ? '即梦视频生成' : '可灵视频生成'}
						</span>
					</div>
					<div class="text-xs text-gray-600 dark:text-gray-400">
						消耗积分: <span class="font-medium text-red-600 dark:text-red-400">
							{#if selectedService === 'jimeng'}
								{#if jimengConfig}
									{selectedDuration === 10
										? jimengConfig.credits_10s || 10
										: jimengConfig.credits_5s || 5}{$creditName}
								{:else}
									加载中...
								{/if}
							{:else if klingConfig}
								{selectedMode === 'pro'
									? klingConfig.pro_credits || 10
									: klingConfig.std_credits || 5}{$creditName}
							{:else}
								加载中...
							{/if}
						</span>
					</div>
				</div>

				<!-- 基础参数 -->
				<div class="space-y-4">
					<!-- 提示词输入 -->
					<div>
						<label class="block text-sm font-medium mb-2">视频描述</label>
						<textarea
							bind:value={prompt}
							placeholder="描述你想要生成的视频..."
							class="w-full h-20 sm:h-24 p-2 sm:p-3 text-sm sm:text-base border border-gray-200 dark:border-gray-700 rounded-lg resize-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
							maxlength="500"
						></textarea>
						<div class="text-xs text-gray-500 mt-1">{prompt.length}/500</div>
					</div>

					<!-- 负向提示词 -->
					<div>
						<label class="block text-sm font-medium mb-2">负向提示词 (可选)</label>
						<textarea
							bind:value={negativePrompt}
							placeholder="描述你不希望出现在视频中的内容..."
							class="w-full h-14 sm:h-16 p-2 sm:p-3 text-sm sm:text-base border border-gray-200 dark:border-gray-700 rounded-lg resize-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
							maxlength="200"
						></textarea>
						<div class="text-xs text-gray-500 mt-1">{negativePrompt.length}/200</div>
					</div>

					<!-- 基础参数 -->
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
						{#if selectedService === 'kling'}
							<!-- 模型选择（仅可灵） -->
							<div>
								<label class="block text-sm font-medium mb-2">模型版本</label>
								<select
									bind:value={selectedModel}
									class="w-full p-2 sm:p-2.5 text-sm sm:text-base border border-gray-200 dark:border-gray-700 rounded-lg touch-manipulation"
								>
									{#each KLING_MODELS as model}
										<option value={model.value}>{model.label}</option>
									{/each}
								</select>
							</div>

							<!-- 生成模式（仅可灵） -->
							<div>
								<label class="block text-sm font-medium mb-2">生成模式</label>
								<select
									bind:value={selectedMode}
									class="w-full p-2 sm:p-2.5 text-sm sm:text-base border border-gray-200 dark:border-gray-700 rounded-lg touch-manipulation"
								>
									{#each GENERATION_MODES as mode}
										<option value={mode.value}>
											{getModeLabel(mode.value, klingConfig, $creditName)}
										</option>
									{/each}
								</select>
							</div>
						{/if}

						<!-- 画面比例 -->
						<div>
							<label class="block text-sm font-medium mb-2">画面比例</label>
							<select
								bind:value={selectedAspectRatio}
								class="w-full p-2 sm:p-2.5 text-sm sm:text-base border border-gray-200 dark:border-gray-700 rounded-lg touch-manipulation"
							>
								{#each selectedService === 'jimeng' ? JIMENG_ASPECT_RATIOS : KLING_ASPECT_RATIOS as ratio}
									<option value={ratio.value}>{ratio.label}</option>
								{/each}
							</select>
						</div>

						<!-- 视频时长 -->
						<div>
							<label class="block text-sm font-medium mb-2">视频时长</label>
							<select
								bind:value={selectedDuration}
								class="w-full p-2 sm:p-2.5 text-sm sm:text-base border border-gray-200 dark:border-gray-700 rounded-lg touch-manipulation"
							>
								{#each selectedService === 'jimeng' ? JIMENG_DURATIONS : KLING_DURATIONS as duration}
									<option value={duration.value}>{duration.label}</option>
								{/each}
							</select>
						</div>
					</div>

					<!-- CFG Scale 滑块 -->
					<div>
						<label class="block text-sm font-medium mb-2">生成自由度 ({cfgScale.toFixed(1)})</label>
						<input type="range" bind:value={cfgScale} min="0" max="1" step="0.1" class="w-full" />
						<div class="flex justify-between text-xs text-gray-500 mt-1">
							<span>更自由</span>
							<span>更贴合提示词</span>
						</div>
					</div>

					<!-- 摄像机运动控制（仅可灵） -->
					{#if selectedService === 'kling'}
						<div>
							<div class="flex items-center space-x-2 mb-3">
								<input
									type="checkbox"
									bind:checked={enableCameraControl}
									id="camera-control"
									class="rounded"
								/>
								<label for="camera-control" class="text-sm font-medium">摄像机运动控制</label>
							</div>

							{#if enableCameraControl}
								<div class="space-y-3 pl-6">
									<!-- 运镜类型选择 -->
									<div>
										<label class="block text-sm font-medium mb-2">运镜类型</label>
										<select
											bind:value={cameraType}
											class="w-full p-2 border border-gray-200 dark:border-gray-700 rounded-lg"
										>
											{#each CAMERA_TYPES as type}
												<option value={type.value}>{type.label}</option>
											{/each}
										</select>
									</div>

									<!-- 简单运镜配置 -->
									{#if cameraType === 'simple'}
										<div class="space-y-3">
											<div class="flex justify-between items-center">
												<span class="text-sm text-gray-600 dark:text-gray-400">运镜配置 (6选1)</span
												>
												<button
													type="button"
													on:click={resetCameraControl}
													class="text-xs text-red-600 hover:text-red-700"
												>
													重置
												</button>
											</div>
											{#each CAMERA_CONFIG_OPTIONS as option}
												<div>
													<label
														class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1"
													>
														{option.label}: {cameraConfig[option.key]}
													</label>
													<input
														type="range"
														value={cameraConfig[option.key]}
														on:input={(e) =>
															handleCameraConfigChange(option.key, parseFloat(e.target.value))}
														min={option.range[0]}
														max={option.range[1]}
														step="0.5"
														class="w-full"
													/>
													<div
														class="flex justify-between text-xs text-gray-500 dark:text-gray-400"
													>
														<span>{option.range[0]}</span>
														<span>{option.range[1]}</span>
													</div>
												</div>
											{/each}
										</div>
									{/if}
								</div>
							{/if}
						</div>
					{/if}

					<!-- 生成按钮 -->
					<button
						on:click={handleGenerate}
						disabled={generating ||
							!prompt.trim() ||
							(selectedService === 'kling' ? !klingConfig : !jimengConfig) ||
							userCredits < (getCreditsNeeded() || 0)}
						class="w-full py-3 bg-gradient-to-r from-red-500 to-orange-600 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:from-red-600 hover:to-orange-700 transition-all flex items-center justify-center space-x-2"
					>
						{#if generating}
							<Spinner className="w-4 h-4" />
							<span>生成中...</span>
						{:else}
							<span
								>生成视频 ({getCreditsNeeded() !== null
									? `${getCreditsNeeded()}${$creditName}`
									: '配置加载中...'})</span
							>
						{/if}
					</button>
				</div>
			</div>

			<!-- 右侧视频展示区域 -->
			<div class="flex-1 flex flex-col overflow-hidden">
				<!-- 搜索和筛选 -->
				<div class="p-4 border-b border-gray-100 dark:border-gray-850">
					<div class="flex items-center space-x-4">
						<div class="flex-1 relative">
							<Search
								className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
							/>
							<input
								bind:value={query}
								placeholder="搜索视频历史..."
								class="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg"
							/>
						</div>
						<div class="flex items-center space-x-2">
							<select
								bind:value={sortBy}
								class="px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg"
							>
								<option value="latest">最新</option>
								<option value="oldest">最早</option>
								<option value="status">状态</option>
							</select>
							<div class="text-sm text-gray-500">
								共 {filteredVideos.length} 个视频
							</div>
						</div>
					</div>
				</div>

				<!-- 视频网格 -->
				<div class="flex-1 p-4 overflow-y-auto">
					{#if filteredVideos.length === 0}
						<div class="flex flex-col items-center justify-center h-64 text-gray-500">
							<div
								class="w-16 h-16 mx-auto mb-4 rounded-lg bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center"
							>
								<svg
									class="size-8 text-white"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
									/>
								</svg>
							</div>
							<p class="text-lg font-medium mb-2">还没有生成任何视频</p>
							<p class="text-sm">在左侧面板中输入描述，开始创建你的第一个AI视频</p>
						</div>
					{:else}
						<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
							{#each filteredVideos as video (video.id)}
								<div
									class="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
								>
									<!-- 视频 -->
									<div class="relative aspect-video">
										{#if video.status === 'generating'}
											<div
												class="w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center"
											>
												<div class="text-center">
													<Spinner className="w-8 h-8 mx-auto mb-2" />
													<div class="text-sm text-gray-600 dark:text-gray-400 mb-3">
														{video.message}
													</div>
													<!-- 手动刷新按钮 -->
													<button
														on:click|stopPropagation={() => forceRefreshTask(video)}
														class="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
														title="强制刷新状态"
													>
														刷新状态
													</button>
												</div>
											</div>
										{:else if video.status === 'failed'}
											<div
												class="w-full h-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center"
											>
												<div class="text-center text-red-600 dark:text-red-400">
													<svg
														class="w-8 h-8 mx-auto mb-2"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
														/>
													</svg>
													<div class="text-sm">生成失败</div>
													<div class="text-xs mt-1">{video.message}</div>
												</div>
											</div>
										{:else if video.video_url}
											<video
												src={video.video_url}
												controls
												autoplay
												muted
												loop
												class="w-full h-full object-cover"
												poster={video.video_url}
											>
												您的浏览器不支持视频播放。
											</video>
										{:else}
											<div
												class="w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center"
											>
												<div class="text-gray-500">无视频</div>
											</div>
										{/if}

										<!-- 服务标识 -->
										<div class="absolute top-2 left-2">
											<span
												class="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-200"
											>
												{video.serviceName || '未知服务'}
											</span>
										</div>

										<!-- 操作按钮 -->
										{#if video.status === 'completed' && video.video_url}
											<div
												class="absolute top-2 right-2 flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity"
											>
												<button
													on:click|stopPropagation={() => handleDownload(video)}
													class="p-1.5 bg-black/60 text-white rounded-full hover:bg-black/80 transition-colors"
													title="下载视频"
												>
													<svg
														class="w-4 h-4"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
														/>
													</svg>
												</button>
											</div>
										{:else if video.status === 'failed'}
											<div
												class="absolute top-2 right-2 flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity"
											>
												<button
													on:click|stopPropagation={() => deleteFailedTask(video)}
													class="p-1.5 bg-red-600/80 text-white rounded-full hover:bg-red-700/90 transition-colors"
													title="删除失败任务"
												>
													<svg
														class="w-4 h-4"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
														/>
													</svg>
												</button>
											</div>
										{/if}
									</div>

									<!-- 视频信息 -->
									<div class="p-4">
										<div class="text-sm text-gray-900 dark:text-gray-100 mb-2 line-clamp-2">
											{video.prompt}
										</div>
										<div class="flex items-center justify-between text-xs text-gray-500 mb-2">
											<span>{video.model || video.serviceName}</span>
											<span
												>{video.service === 'jimeng'
													? jimengFormatTime(video.created_at)
													: formatTime(video.created_at)}</span
											>
										</div>

										<!-- 参数标签 -->
										<div class="flex flex-wrap gap-1 mb-2">
											{#if video.mode}
												<span
													class="px-2 py-1 text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300 rounded"
												>
													{video.mode === 'pro' ? '专家' : '标准'}
												</span>
											{/if}
											<span
												class="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded"
											>
												{video.aspect_ratio}
											</span>
											<span
												class="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded"
											>
												{video.duration}秒
											</span>
										</div>

										<!-- 操作按钮 -->
										{#if video.status === 'completed'}
											<div class="flex space-x-2">
												<button
													on:click={() => copyPrompt(video)}
													class="flex-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
												>
													复制提示词
												</button>
											</div>
										{:else if video.status === 'failed'}
											<div class="flex space-x-2">
												<button
													on:click={() => copyPrompt(video)}
													class="flex-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
												>
													复制提示词
												</button>
												<button
													on:click={() => deleteFailedTask(video)}
													class="px-2 py-1 text-xs bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-800/40 transition-colors"
												>
													删除任务
												</button>
											</div>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	/* 文本截断样式 */
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
