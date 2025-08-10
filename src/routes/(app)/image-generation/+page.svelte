<script>
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user, creditName, showSidebar, mobile } from '$lib/stores';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';

	// MidJourney APIs
	import {
		generateImageWithPolling as mjGenerateImageWithPolling,
		getUserTasks as mjGetUserTasks,
		getMidJourneyConfig,
		getUserCredits as mjGetUserCredits,
		executeActionWithPolling,
		fileToBase64,
		GENERATION_MODE,
		TASK_STATUS as MJ_TASK_STATUS,
		ASPECT_RATIOS,
		MJ_VERSIONS,
		REFERENCE_TYPES,
		ACTION_TYPES
	} from '$lib/apis/midjourney.js';

	// 即梦3.0 APIs
	import {
		generateImage as seedreamGenerateImage,
		getUserTasks as seedreamGetUserTasks,
		getSeedreamConfig,
		getUserCredits as seedreamGetUserCredits,
		TASK_STATUS as SEEDREAM_TASK_STATUS,
		RECOMMENDED_SIZES,
		buildGenerateRequest,
		getSizeLabel
	} from '$lib/apis/seedream.js';

	const i18n = getContext('i18n');

	// 全局状态
	let loaded = false;
	let query = '';
	let generating = false;
	let prompt = '';

	// 服务选择
	let selectedService = 'midjourney'; // 'midjourney' 或 'seedream'
	let midJourneyConfig = null;
	let seedreamConfig = null;
	let userCredits = 0;

	// MidJourney 特有参数
	let negativePrompt = '';
	let selectedMode = 'fast';
	let imageSize = '1:1';
	let showAdvancedOptions = false;
	let chaos = null;
	let stylize = null;
	let seed = null;
	let selectedVersion = null;
	let quality = 1.0;
	let weird = null;
	let tileMode = false;
	let referenceImages = [];
	let styleReferenceImages = [];
	let fileInputRef;
	let styleFileInputRef;

	// 即梦3.0 特有参数
	let usePreLlm = false;
	let seedreamSeed = -1;
	let scale = 2.5;
	let selectedSize = '1:1 正方形';
	let customWidth = 1328;
	let customHeight = 1328;
	let useCustomSize = false;
	let addWatermark = false;
	let watermarkPosition = 0;
	let watermarkLanguage = 0;
	let watermarkOpacity = 0.3;
	let watermarkText = '';

	// 任务和历史
	let imageHistory = [];
	let currentTask = null;
	let executingAction = false;
	let selectedImageForAction = null;

	// 图片预览
	let showImageModal = false;
	let previewImage = null;

	let filteredImages = imageHistory;

	$: {
		filteredImages = query
			? imageHistory.filter(
					(img) =>
						img.prompt.toLowerCase().includes(query.toLowerCase()) ||
						img.service.toLowerCase().includes(query.toLowerCase())
				)
			: imageHistory;
	}

	// 根据选择的服务更新可用积分信息
	$: serviceCredits = getServiceCredits();

	// 根据选择的尺寸更新宽高
	$: {
		if (selectedService === 'seedream' && !useCustomSize) {
			const sizeInfo = RECOMMENDED_SIZES[selectedSize];
			if (sizeInfo) {
				customWidth = sizeInfo.width;
				customHeight = sizeInfo.height;
			}
		}
	}

	function getServiceCredits() {
		if (selectedService === 'midjourney') {
			if (!midJourneyConfig) return null;
			if (selectedMode === 'fast') return midJourneyConfig.fast_credits || 10;
			if (selectedMode === 'relax') return midJourneyConfig.relax_credits || 5;
			if (selectedMode === 'turbo') return midJourneyConfig.turbo_credits || 15;
			return 10;
		} else if (selectedService === 'seedream') {
			if (!seedreamConfig) return null;
			return seedreamConfig.credits_per_generation || 1;
		}
		return null;
	}

	// 加载配置
	const loadConfigs = async () => {
		if (!$user?.token) return;

		try {
			// 并行加载两个服务的配置
			const [mjConfig, seedreamConf, creditsData] = await Promise.allSettled([
				getMidJourneyConfig($user.token),
				getSeedreamConfig($user.token),
				mjGetUserCredits($user.token) // 使用MidJourney的积分接口
			]);

			if (mjConfig.status === 'fulfilled') {
				midJourneyConfig = mjConfig.value;
				console.log(
					'MidJourney配置加载成功, 服务状态:',
					midJourneyConfig?.enabled ? '已启用' : '未启用'
				);
			} else {
				console.error('加载MidJourney配置失败:', mjConfig.reason);
			}

			if (seedreamConf.status === 'fulfilled') {
				seedreamConfig = seedreamConf.value;
				console.log(
					'即梦3.0配置加载成功, 服务状态:',
					seedreamConfig?.enabled ? '已启用' : '未启用'
				);
			} else {
				console.error('加载即梦3.0配置失败:', seedreamConf.reason);
			}

			if (creditsData.status === 'fulfilled') {
				userCredits = creditsData.value.credits || 0;
				console.log('用户积分余额加载成功:', userCredits);
			} else {
				console.error('加载用户积分余额失败:', creditsData.reason);
				userCredits = 0;
			}

			// 如果当前选择的服务未启用，自动切换到已启用的服务
			if (
				selectedService === 'midjourney' &&
				!midJourneyConfig?.enabled &&
				seedreamConfig?.enabled
			) {
				selectedService = 'seedream';
				toast.info('MidJourney服务未启用，已切换到即梦3.0');
			} else if (
				selectedService === 'seedream' &&
				!seedreamConfig?.enabled &&
				midJourneyConfig?.enabled
			) {
				selectedService = 'midjourney';
				toast.info('即梦3.0服务未启用，已切换到MidJourney');
			}
		} catch (error) {
			console.error('加载配置失败:', error);
		}
	};

	// 加载用户任务历史
	const loadUserTasks = async () => {
		if (!$user?.token) return;

		try {
			// 并行加载两个服务的任务历史
			const [mjTasks, seedreamTasks] = await Promise.allSettled([
				mjGetUserTasks($user.token),
				seedreamGetUserTasks($user.token)
			]);

			let allTasks = [];

			// 处理MidJourney任务 - 包括所有状态的任务
			if (mjTasks.status === 'fulfilled') {
				const mjTaskList = mjTasks.value.tasks || [];
				const mjHistoryTasks = mjTaskList.map((task) => {
					// 根据任务状态设置显示状态
					let displayStatus = 'completed';
					let displayMessage = '图像生成完成';
					let displayProgress = 100;
					let displayImage = task.image_url;

					if (
						task.status === MJ_TASK_STATUS.PROCESSING ||
						task.status === MJ_TASK_STATUS.SUBMITTED
					) {
						displayStatus = 'generating';
						displayMessage = task.message || '正在生成图像...';
						displayProgress = task.progress || 0;
						displayImage = null;
					} else if (task.status === MJ_TASK_STATUS.FAILED) {
						displayStatus = 'failed';
						displayMessage = task.message || '生成失败';
						displayProgress = 0;
						displayImage = null;
					} else if (task.status === MJ_TASK_STATUS.CANCELLED) {
						displayStatus = 'failed';
						displayMessage = '任务已取消';
						displayProgress = 0;
						displayImage = null;
					}

					return {
						id: task.task_id,
						prompt: task.prompt,
						image: displayImage,
						timestamp: task.completed_at
							? new Date(task.completed_at * 1000)
							: new Date(task.created_at * 1000),
						service: 'MidJourney',
						model: `MidJourney (${task.mode})`,
						task_id: task.task_id,
						actions: task.actions || [],
						seed: task.seed,
						final_prompt: task.final_prompt,
						aspect_ratio: task.aspect_ratio || '1:1',
						status: displayStatus,
						progress: displayProgress,
						message: displayMessage
					};
				});
				allTasks = [...allTasks, ...mjHistoryTasks];
			}

			// 处理即梦3.0任务 - 包括所有状态的任务
			if (seedreamTasks.status === 'fulfilled') {
				const seedreamTaskList = seedreamTasks.value.tasks || [];
				const seedreamHistoryTasks = seedreamTaskList.map((task) => {
					// 根据任务状态设置显示状态
					let displayStatus = 'completed';
					let displayMessage = '图像生成完成';
					let displayProgress = 100;
					let displayImage =
						task.image_url ||
						(task.image_data ? `data:image/jpeg;base64,${task.image_data}` : null);

					if (
						task.status === SEEDREAM_TASK_STATUS.PROCESSING ||
						task.status === SEEDREAM_TASK_STATUS.SUBMITTED
					) {
						displayStatus = 'generating';
						displayMessage = task.message || '正在生成图像...';
						displayProgress = task.progress || 0;
						displayImage = null;
					} else if (task.status === SEEDREAM_TASK_STATUS.FAILED) {
						displayStatus = 'failed';
						displayMessage = task.message || '生成失败';
						displayProgress = 0;
						displayImage = null;
					}

					return {
						id: task.task_id,
						prompt: task.prompt,
						image: displayImage,
						timestamp: task.completed_at
							? new Date(task.completed_at * 1000)
							: new Date(task.created_at * 1000),
						service: '即梦3.0',
						model: `即梦3.0 (${task.width}×${task.height})`,
						task_id: task.task_id,
						width: task.width,
						height: task.height,
						scale: task.scale,
						seed: task.seed,
						status: displayStatus,
						progress: displayProgress,
						message: displayMessage
					};
				});
				allTasks = [...allTasks, ...seedreamHistoryTasks];
			}

			// 按时间排序
			allTasks.sort((a, b) => b.timestamp - a.timestamp);
			imageHistory = allTasks;

			if (allTasks.length > 0) {
				console.log('加载了', allTasks.length, '个历史任务');
			} else {
				console.log('没有找到历史任务');
			}
		} catch (error) {
			console.error('加载用户任务失败:', error);
		}
	};

	// 生成图像
	const generateImage = async () => {
		if (!prompt.trim()) {
			toast.error('请输入图像描述');
			return;
		}

		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		// 检查服务是否启用
		const currentConfig = selectedService === 'midjourney' ? midJourneyConfig : seedreamConfig;
		if (!currentConfig?.enabled) {
			toast.error(
				`${selectedService === 'midjourney' ? 'MidJourney' : '即梦3.0'}服务未启用，请联系管理员配置`
			);
			return;
		}

		// 检查积分
		let requiredCredits;
		if (selectedService === 'midjourney') {
			if (!midJourneyConfig) {
				toast.error('MidJourney服务配置未加载，请稍后重试');
				return;
			}
			if (selectedMode === 'fast') {
				requiredCredits = midJourneyConfig.fast_credits || 10;
			} else if (selectedMode === 'relax') {
				requiredCredits = midJourneyConfig.relax_credits || 5;
			} else if (selectedMode === 'turbo') {
				requiredCredits = midJourneyConfig.turbo_credits || 15;
			} else {
				requiredCredits = 10;
			}
		} else if (selectedService === 'seedream') {
			if (!seedreamConfig) {
				toast.error('即梦3.0服务配置未加载，请稍后重试');
				return;
			}
			requiredCredits = seedreamConfig.credits_per_generation || 1;
		} else {
			toast.error('未知的图像生成服务');
			return;
		}

		if (userCredits < requiredCredits) {
			toast.error(
				`${$creditName}余额不足，需要${requiredCredits}${$creditName}，当前余额：${userCredits.toFixed(2)}${$creditName}`
			);
			return;
		}

		generating = true;
		currentTask = null;

		try {
			if (selectedService === 'midjourney') {
				await generateMidJourneyImage();
			} else if (selectedService === 'seedream') {
				await generateSeedreamImage();
			}
		} catch (error) {
			console.error('图像生成失败:', error);
			toast.error(`图像生成失败: ${error.message}`);
		} finally {
			generating = false;
		}
	};

	// MidJourney图像生成
	const generateMidJourneyImage = async () => {
		const request = {
			prompt: prompt.trim(),
			mode: selectedMode,
			aspect_ratio: imageSize,
			negative_prompt: negativePrompt?.trim() || null,
			reference_images: [...referenceImages, ...styleReferenceImages],
			advanced_params: {
				chaos: chaos !== null && chaos !== '' ? parseInt(chaos) : null,
				stylize: stylize !== null && stylize !== '' ? parseInt(stylize) : null,
				seed: seed !== null && seed !== '' ? parseInt(seed) : null,
				version: selectedVersion || null,
				quality: quality !== 1.0 ? quality : null,
				weird: weird !== null && weird !== '' ? parseInt(weird) : null,
				tile: tileMode
			}
		};

		// 添加临时任务到历史中
		const tempTaskId = 'temp_mj_' + Date.now();
		const tempTask = {
			id: tempTaskId,
			prompt: prompt.trim(),
			image: null,
			timestamp: new Date(),
			service: 'MidJourney',
			model: `MidJourney (${selectedMode})`,
			task_id: tempTaskId,
			status: 'generating',
			progress: 0,
			message: '正在生成图像...'
		};
		imageHistory = [tempTask, ...imageHistory];

		try {
			const result = await mjGenerateImageWithPolling($user.token, request, (statusUpdate) => {
				// 更新任务状态
				updateTaskInHistory(tempTaskId, statusUpdate);
			});

			// 任务完成，添加到历史
			const completedTask = {
				id: result.task_id,
				prompt: prompt.trim(),
				image: result.image_url,
				timestamp: new Date(),
				service: 'MidJourney',
				model: `MidJourney (${selectedMode})`,
				task_id: result.task_id,
				actions: result.actions || [],
				seed: result.seed,
				final_prompt: result.final_prompt,
				aspect_ratio: imageSize,
				status: 'completed',
				progress: 100,
				message: '图像生成完成'
			};

			// 替换临时任务
			replaceTaskInHistory(tempTaskId, completedTask);

			// 更新积分余额
			await loadConfigs();

			toast.success('MidJourney图像生成完成');
		} catch (error) {
			// 任务失败，更新状态
			updateTaskInHistory(tempTaskId, {
				status: 'failed',
				message: `生成失败: ${error.message}`,
				progress: 0
			});
			throw error;
		}
	};

	// 即梦3.0图像生成
	const generateSeedreamImage = async () => {
		const logoInfo = addWatermark
			? {
					add_logo: true,
					position: watermarkPosition,
					language: watermarkLanguage,
					opacity: watermarkOpacity,
					logo_text_content: watermarkText || undefined
				}
			: null;

		const request = buildGenerateRequest({
			prompt: prompt.trim(),
			use_pre_llm: usePreLlm,
			seed: seedreamSeed,
			scale: scale,
			width: customWidth,
			height: customHeight,
			return_url: true,
			logo_info: logoInfo
		});

		// 添加临时任务到历史中
		const tempTaskId = 'temp_seedream_' + Date.now();
		const tempTask = {
			id: tempTaskId,
			prompt: prompt.trim(),
			image: null,
			timestamp: new Date(),
			service: '即梦3.0',
			model: `即梦3.0 (${customWidth}×${customHeight})`,
			task_id: tempTaskId,
			status: 'generating',
			progress: 0,
			message: '正在生成图像...'
		};
		imageHistory = [tempTask, ...imageHistory];

		try {
			const result = await seedreamGenerateImage($user.token, request);

			// 任务完成，添加到历史
			const completedTask = {
				id: result.task_id,
				prompt: prompt.trim(),
				image:
					result.image_url ||
					(result.image_data ? `data:image/jpeg;base64,${result.image_data}` : null),
				timestamp: new Date(),
				service: '即梦3.0',
				model: `即梦3.0 (${customWidth}×${customHeight})`,
				task_id: result.task_id,
				width: customWidth,
				height: customHeight,
				scale: scale,
				seed: seedreamSeed,
				status: 'completed',
				progress: 100,
				message: '图像生成完成'
			};

			// 替换临时任务
			replaceTaskInHistory(tempTaskId, completedTask);

			// 更新积分余额
			await loadConfigs();

			toast.success('即梦3.0图像生成完成');
		} catch (error) {
			// 任务失败，更新状态
			updateTaskInHistory(tempTaskId, {
				status: 'failed',
				message: `生成失败: ${error.message}`,
				progress: 0
			});
			throw error;
		}
	};

	// 更新历史中的任务状态
	const updateTaskInHistory = (taskId, updates) => {
		imageHistory = imageHistory.map((task) =>
			task.id === taskId || task.task_id === taskId ? { ...task, ...updates } : task
		);
	};

	// 替换历史中的任务
	const replaceTaskInHistory = (tempTaskId, newTask) => {
		imageHistory = imageHistory.map((task) => (task.id === tempTaskId ? newTask : task));
	};

	// 处理参考图片上传（MidJourney）
	const handleImageUpload = async (event, isStyle = false) => {
		const files = Array.from(event.target.files);
		if (files.length === 0) return;

		const targetArray = isStyle ? styleReferenceImages : referenceImages;

		for (const file of files) {
			if (targetArray.length >= 5) {
				toast.error('最多只能上传5张参考图片');
				break;
			}

			try {
				const base64 = await fileToBase64(file);
				const imageRef = {
					base64: base64,
					filename: file.name,
					weight: 1.0,
					type: isStyle ? REFERENCE_TYPES.STYLE : REFERENCE_TYPES.REFERENCE
				};

				if (isStyle) {
					styleReferenceImages = [...styleReferenceImages, imageRef];
				} else {
					referenceImages = [...referenceImages, imageRef];
				}
			} catch (error) {
				console.error('处理图片失败:', error);
				toast.error(`处理图片 ${file.name} 失败`);
			}
		}

		// 清空文件输入
		event.target.value = '';
	};

	// 移除参考图片
	const removeReferenceImage = (index, isStyle = false) => {
		if (isStyle) {
			styleReferenceImages = styleReferenceImages.filter((_, i) => i !== index);
		} else {
			referenceImages = referenceImages.filter((_, i) => i !== index);
		}
	};

	// 执行MidJourney动作
	const executeAction = async (image, action) => {
		if (!$user?.token || executingAction) return;

		executingAction = true;
		selectedImageForAction = image.id;

		try {
			const result = await executeActionWithPolling(
				$user.token,
				image.task_id,
				action,
				(statusUpdate) => {
					console.log('动作执行状态更新:', statusUpdate);
				}
			);

			// 添加新的结果图片到历史
			const newTask = {
				id: result.task_id,
				prompt: image.prompt,
				image: result.image_url,
				timestamp: new Date(),
				service: 'MidJourney',
				model: `MidJourney (${result.action_type})`,
				task_id: result.task_id,
				parent_task_id: result.parent_task_id,
				action_type: result.action_type,
				actions: result.actions || [],
				status: 'completed',
				progress: 100,
				message: `${result.action_type}操作完成`
			};

			imageHistory = [newTask, ...imageHistory];

			// 更新积分余额
			await loadConfigs();

			toast.success(`${result.action_type}操作完成`);
		} catch (error) {
			console.error('执行动作失败:', error);
			toast.error(`执行动作失败: ${error.message}`);
		} finally {
			executingAction = false;
			selectedImageForAction = null;
		}
	};

	// 打开图片预览
	const openImageModal = (image) => {
		previewImage = image;
		showImageModal = true;
	};

	// 下载图片
	const downloadImage = (imageUrl, filename) => {
		const link = document.createElement('a');
		link.href = imageUrl;
		link.download = filename || 'generated-image.jpg';
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
	};

	// 复制提示词
	const copyPrompt = (promptText) => {
		navigator.clipboard.writeText(promptText);
		toast.success('提示词已复制到剪贴板');
	};

	// 重新生成
	const regenerateWithPrompt = (promptText) => {
		prompt = promptText;
		document.getElementById('prompt-input')?.focus();
		toast.info('提示词已填入，可以修改后重新生成');
	};

	// 删除失败的任务
	const deleteFailedTask = async (image) => {
		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		try {
			// 根据服务类型调用不同的删除API
			if (image.service === 'MidJourney') {
				await import('$lib/apis/midjourney.js').then((module) =>
					module.cancelTask($user.token, image.task_id)
				);
			} else if (image.service === '即梦3.0') {
				await import('$lib/apis/seedream.js').then((module) =>
					module.deleteTask($user.token, image.task_id)
				);
			}

			// 从本地历史中移除任务
			imageHistory = imageHistory.filter((task) => task.id !== image.id);

			toast.success('任务已删除');
		} catch (error) {
			console.error('删除任务失败:', error);
			toast.error(`删除任务失败: ${error.message}`);
		}
	};

	// 页面加载时初始化
	onMount(async () => {
		await loadConfigs();
		await loadUserTasks();
		loaded = true;
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
				<div
					class="w-8 h-8 bg-pink-100 dark:bg-pink-900 rounded-lg flex items-center justify-center"
				>
					<svg class="w-5 h-5 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"
						/>
					</svg>
				</div>
				<h1 class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">图像生成</h1>
			</div>
		</div>

		<div class="flex items-center space-x-3">
			<!-- 积分余额显示 -->
			<div
				class="flex items-center space-x-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/20 rounded-lg"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-4 h-4 text-blue-600 dark:text-blue-400"
				>
					<path
						d="M10 9a3 3 0 100-6 3 3 0 000 6zM6 8a2 2 0 11-4 0 2 2 0 014 0zM1.49 15.326a.78.78 0 01-.358-.442 3 3 0 014.308-3.516 6.484 6.484 0 00-1.905 3.959c-.023.222-.014.442.025.654a4.97 4.97 0 01-2.07-.655zM16.44 15.98a4.97 4.97 0 002.07-.654.78.78 0 00.357-.442 3 3 0 00-4.308-3.517 6.484 6.484 0 711.907 3.96 2.32 2.32 0 01-.026.654zM18 8a2 2 0 11-4 0 2 2 0 014 0zM5.304 16.19a.844.844 0 01-.277-.71 5 5 0 019.947 0 .843.843 0 01-.277.71A6.975 6.975 0 0110 18a6.974 6.974 0 01-4.696-1.81z"
					/>
				</svg>
				<span class="text-sm font-medium text-blue-800 dark:text-blue-200">
					{userCredits.toFixed(2)}
					{$creditName}
				</span>
			</div>
		</div>
	</div>

	<hr class="border-gray-100 dark:border-gray-850" />

	<div class="flex-1 flex flex-col lg:flex-row overflow-hidden">
		<!-- 左侧生成面板 -->
		<div
			class="flex-none w-full lg:w-96 p-3 sm:p-4 border-b lg:border-b-0 lg:border-r border-gray-100 dark:border-gray-850 overflow-y-auto max-h-[50vh] lg:max-h-none"
		>
			<!-- 服务选择 -->
			<div class="mb-6">
				<label class="block text-sm font-medium mb-2">图像生成服务</label>
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
					<button
						class="p-2 sm:p-3 rounded-lg border transition-all text-sm sm:text-base {selectedService ===
						'midjourney'
							? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200'
							: 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
						on:click={() => (selectedService = 'midjourney')}
						disabled={!midJourneyConfig?.enabled}
					>
						<div class="text-center">
							<div class="text-sm font-medium">MidJourney</div>
							<div class="text-xs text-gray-500 mt-1">
								{midJourneyConfig?.enabled ? '已启用' : '未启用'}
							</div>
						</div>
					</button>
					<button
						class="p-3 rounded-lg border transition-all {selectedService === 'seedream'
							? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 text-purple-800 dark:text-purple-200'
							: 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
						on:click={() => (selectedService = 'seedream')}
						disabled={!seedreamConfig?.enabled}
					>
						<div class="text-center">
							<div class="text-sm font-medium">即梦3.0</div>
							<div class="text-xs text-gray-500 mt-1">
								{seedreamConfig?.enabled ? '已启用' : '未启用'}
							</div>
						</div>
					</button>
				</div>
			</div>

			<!-- 积分消耗提示 -->
			<div class="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
				<div class="text-xs text-gray-600 dark:text-gray-400">
					当前服务: <span class="font-medium"
						>{selectedService === 'midjourney' ? 'MidJourney' : '即梦3.0'}</span
					>
				</div>
				<div class="text-xs text-gray-600 dark:text-gray-400">
					消耗积分: <span class="font-medium text-blue-600 dark:text-blue-400">
						{#if selectedService === 'midjourney' && midJourneyConfig}
							{#if selectedMode === 'fast'}
								{midJourneyConfig.fast_credits || 10}{$creditName}
							{:else if selectedMode === 'relax'}
								{midJourneyConfig.relax_credits || 5}{$creditName}
							{:else if selectedMode === 'turbo'}
								{midJourneyConfig.turbo_credits || 15}{$creditName}
							{:else}
								10{$creditName}
							{/if}
						{:else if selectedService === 'seedream' && seedreamConfig}
							{seedreamConfig.credits_per_generation || 1}{$creditName}
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
					<label class="block text-sm font-medium mb-2">图像描述</label>
					<textarea
						id="prompt-input"
						bind:value={prompt}
						placeholder="描述你想要生成的图像..."
						class="w-full h-24 p-3 border border-gray-200 dark:border-gray-700 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						maxlength="2000"
					></textarea>
					<div class="text-xs text-gray-500 mt-1">{prompt.length}/2000</div>
				</div>

				<!-- MidJourney 特有参数 -->
				{#if selectedService === 'midjourney'}
					<!-- 生成模式 -->
					<div>
						<label class="block text-sm font-medium mb-2">生成模式</label>
						<select
							bind:value={selectedMode}
							class="w-full p-2 border border-gray-200 dark:border-gray-700 rounded-lg"
						>
							<option value="fast"
								>Fast (快速, {midJourneyConfig?.fast_credits || 10}{$creditName})</option
							>
							<option value="relax"
								>Relax (经济, {midJourneyConfig?.relax_credits || 5}{$creditName})</option
							>
							<option value="turbo"
								>Turbo (极速, {midJourneyConfig?.turbo_credits || 15}{$creditName})</option
							>
						</select>
					</div>

					<!-- 图像比例 -->
					<div>
						<label class="block text-sm font-medium mb-2">图像比例</label>
						<select
							bind:value={imageSize}
							class="w-full p-2 border border-gray-200 dark:border-gray-700 rounded-lg"
						>
							{#each Object.entries(ASPECT_RATIOS) as [label, value]}
								<option {value}>{label}</option>
							{/each}
						</select>
					</div>

					<!-- 负面提示词 -->
					<div>
						<label class="block text-sm font-medium mb-2">负面提示词 (可选)</label>
						<textarea
							bind:value={negativePrompt}
							placeholder="描述你不希望出现在图像中的内容..."
							class="w-full h-16 p-3 border border-gray-200 dark:border-gray-700 rounded-lg resize-none"
							maxlength="1000"
						></textarea>
					</div>

					<!-- 高级选项 -->
					<div>
						<button
							type="button"
							class="flex items-center justify-between w-full text-sm font-medium py-2"
							on:click={() => (showAdvancedOptions = !showAdvancedOptions)}
						>
							<span>高级选项</span>
							<svg
								class="w-4 h-4 transition-transform {showAdvancedOptions ? 'rotate-180' : ''}"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 9l-7 7-7-7"
								/>
							</svg>
						</button>

						{#if showAdvancedOptions}
							<div class="space-y-3 pt-2">
								<!-- 混乱程度 -->
								<div>
									<label class="block text-xs font-medium mb-1">混乱程度 (0-100)</label>
									<input
										type="number"
										bind:value={chaos}
										min="0"
										max="100"
										class="w-full p-2 text-sm border border-gray-200 dark:border-gray-700 rounded"
										placeholder="留空使用默认值"
									/>
								</div>

								<!-- 风格化程度 -->
								<div>
									<label class="block text-xs font-medium mb-1">风格化程度 (0-1000)</label>
									<input
										type="number"
										bind:value={stylize}
										min="0"
										max="1000"
										class="w-full p-2 text-sm border border-gray-200 dark:border-gray-700 rounded"
										placeholder="留空使用默认值"
									/>
								</div>

								<!-- 种子值 -->
								<div>
									<label class="block text-xs font-medium mb-1">种子值</label>
									<input
										type="number"
										bind:value={seed}
										min="0"
										max="4294967295"
										class="w-full p-2 text-sm border border-gray-200 dark:border-gray-700 rounded"
										placeholder="留空随机生成"
									/>
								</div>

								<!-- 版本选择 -->
								<div>
									<label class="block text-xs font-medium mb-1">模型版本</label>
									<select
										bind:value={selectedVersion}
										class="w-full p-2 text-sm border border-gray-200 dark:border-gray-700 rounded"
									>
										<option value={null}>默认版本</option>
										{#each Object.entries(MJ_VERSIONS) as [label, value]}
											<option {value}>{label}</option>
										{/each}
									</select>
								</div>

								<!-- 图像质量 -->
								<div>
									<label class="block text-xs font-medium mb-1">图像质量 ({quality})</label>
									<input
										type="range"
										bind:value={quality}
										min="0.25"
										max="2"
										step="0.25"
										class="w-full"
									/>
									<div class="flex justify-between text-xs text-gray-500">
										<span>0.25</span>
										<span>2.0</span>
									</div>
								</div>

								<!-- 奇异程度 -->
								<div>
									<label class="block text-xs font-medium mb-1">奇异程度 (0-3000)</label>
									<input
										type="number"
										bind:value={weird}
										min="0"
										max="3000"
										class="w-full p-2 text-sm border border-gray-200 dark:border-gray-700 rounded"
										placeholder="留空使用默认值"
									/>
								</div>

								<!-- 平铺模式 -->
								<div class="flex items-center space-x-2">
									<input type="checkbox" bind:checked={tileMode} id="tile-mode" class="rounded" />
									<label for="tile-mode" class="text-xs font-medium">平铺模式</label>
								</div>
							</div>
						{/if}
					</div>
				{/if}

				<!-- 即梦3.0 特有参数 -->
				{#if selectedService === 'seedream'}
					<!-- 图像尺寸 -->
					<div>
						<label class="block text-sm font-medium mb-2">图像尺寸</label>
						<div class="space-y-2">
							<div class="flex items-center space-x-2">
								<input
									type="radio"
									bind:group={useCustomSize}
									value={false}
									id="preset-size"
									class="rounded"
								/>
								<label for="preset-size" class="text-sm">预设尺寸</label>
							</div>
							{#if !useCustomSize}
								<select
									bind:value={selectedSize}
									class="w-full p-2 border border-gray-200 dark:border-gray-700 rounded-lg"
								>
									{#each Object.keys(RECOMMENDED_SIZES) as sizeLabel}
										<option value={sizeLabel}>{sizeLabel}</option>
									{/each}
								</select>
							{/if}

							<div class="flex items-center space-x-2">
								<input
									type="radio"
									bind:group={useCustomSize}
									value={true}
									id="custom-size"
									class="rounded"
								/>
								<label for="custom-size" class="text-sm">自定义尺寸</label>
							</div>
							{#if useCustomSize}
								<div class="grid grid-cols-2 gap-2">
									<div>
										<label class="block text-xs font-medium mb-1">宽度</label>
										<input
											type="number"
											bind:value={customWidth}
											min="512"
											max="2048"
											class="w-full p-2 text-sm border border-gray-200 dark:border-gray-700 rounded"
										/>
									</div>
									<div>
										<label class="block text-xs font-medium mb-1">高度</label>
										<input
											type="number"
											bind:value={customHeight}
											min="512"
											max="2048"
											class="w-full p-2 text-sm border border-gray-200 dark:border-gray-700 rounded"
										/>
									</div>
								</div>
							{/if}
						</div>
					</div>

					<!-- 文本影响程度 -->
					<div>
						<label class="block text-sm font-medium mb-2">文本影响程度 ({scale})</label>
						<input type="range" bind:value={scale} min="1" max="10" step="0.1" class="w-full" />
						<div class="flex justify-between text-xs text-gray-500">
							<span>1.0</span>
							<span>10.0</span>
						</div>
					</div>

					<!-- 种子值 -->
					<div>
						<label class="block text-sm font-medium mb-2">种子值</label>
						<input
							type="number"
							bind:value={seedreamSeed}
							min="-1"
							max="2147483647"
							class="w-full p-2 border border-gray-200 dark:border-gray-700 rounded-lg"
							placeholder="-1 表示随机"
						/>
						<div class="text-xs text-gray-500 mt-1">-1 表示随机，其他值可产生可重复的结果</div>
					</div>

					<!-- 文本扩写 -->
					<div class="flex items-center space-x-2">
						<input type="checkbox" bind:checked={usePreLlm} id="use-pre-llm" class="rounded" />
						<label for="use-pre-llm" class="text-sm font-medium">启用文本扩写</label>
					</div>
					<div class="text-xs text-gray-500">适合较短的提示词，自动扩展和优化描述</div>

					<!-- 水印设置 -->
					<div>
						<div class="flex items-center space-x-2 mb-2">
							<input
								type="checkbox"
								bind:checked={addWatermark}
								id="add-watermark"
								class="rounded"
							/>
							<label for="add-watermark" class="text-sm font-medium">添加水印</label>
						</div>

						{#if addWatermark}
							<div class="space-y-2 pl-6">
								<div>
									<label class="block text-xs font-medium mb-1">水印位置</label>
									<select
										bind:value={watermarkPosition}
										class="w-full p-2 text-sm border border-gray-200 dark:border-gray-700 rounded"
									>
										<option value={0}>右下角</option>
										<option value={1}>左下角</option>
										<option value={2}>左上角</option>
										<option value={3}>右上角</option>
									</select>
								</div>
								<div>
									<label class="block text-xs font-medium mb-1">水印语言</label>
									<select
										bind:value={watermarkLanguage}
										class="w-full p-2 text-sm border border-gray-200 dark:border-gray-700 rounded"
									>
										<option value={0}>中文 (AI生成)</option>
										<option value={1}>英文 (Generated by AI)</option>
									</select>
								</div>
								<div>
									<label class="block text-xs font-medium mb-1">不透明度 ({watermarkOpacity})</label
									>
									<input
										type="range"
										bind:value={watermarkOpacity}
										min="0"
										max="1"
										step="0.1"
										class="w-full"
									/>
								</div>
								<div>
									<label class="block text-xs font-medium mb-1">自定义水印文字 (可选)</label>
									<input
										type="text"
										bind:value={watermarkText}
										class="w-full p-2 text-sm border border-gray-200 dark:border-gray-700 rounded"
										placeholder="留空使用默认水印"
									/>
								</div>
							</div>
						{/if}
					</div>
				{/if}

				<!-- 参考图片 (仅MidJourney) -->
				{#if selectedService === 'midjourney'}
					<div>
						<label class="block text-sm font-medium mb-2">参考图片 (可选)</label>

						<!-- 普通参考图 -->
						<div class="mb-3">
							<div class="flex items-center justify-between mb-2">
								<span class="text-xs font-medium">普通参考图 ({referenceImages.length}/5)</span>
								<input
									type="file"
									multiple
									accept="image/*"
									bind:this={fileInputRef}
									on:change={(e) => handleImageUpload(e, false)}
									class="hidden"
								/>
								<button
									type="button"
									on:click={() => fileInputRef?.click()}
									disabled={referenceImages.length >= 5}
									class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200 disabled:opacity-50"
								>
									添加图片
								</button>
							</div>
							{#if referenceImages.length > 0}
								<div class="grid grid-cols-3 gap-2">
									{#each referenceImages as img, i}
										<div class="relative group">
											<img
												src={`data:image/jpeg;base64,${img.base64}`}
												alt={img.filename}
												class="w-full h-16 object-cover rounded border"
											/>
											<button
												type="button"
												on:click={() => removeReferenceImage(i, false)}
												class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity"
											>
												×
											</button>
										</div>
									{/each}
								</div>
							{/if}
						</div>

						<!-- 风格参考图 -->
						<div>
							<div class="flex items-center justify-between mb-2">
								<span class="text-xs font-medium">风格参考图 ({styleReferenceImages.length}/5)</span
								>
								<input
									type="file"
									multiple
									accept="image/*"
									bind:this={styleFileInputRef}
									on:change={(e) => handleImageUpload(e, true)}
									class="hidden"
								/>
								<button
									type="button"
									on:click={() => styleFileInputRef?.click()}
									disabled={styleReferenceImages.length >= 5}
									class="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded hover:bg-purple-200 disabled:opacity-50"
								>
									添加风格图
								</button>
							</div>
							{#if styleReferenceImages.length > 0}
								<div class="grid grid-cols-3 gap-2">
									{#each styleReferenceImages as img, i}
										<div class="relative group">
											<img
												src={`data:image/jpeg;base64,${img.base64}`}
												alt={img.filename}
												class="w-full h-16 object-cover rounded border"
											/>
											<button
												type="button"
												on:click={() => removeReferenceImage(i, true)}
												class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity"
											>
												×
											</button>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- 生成按钮 -->
				<button
					on:click={generateImage}
					disabled={generating ||
						!prompt.trim() ||
						(selectedService === 'midjourney' && !midJourneyConfig) ||
						(selectedService === 'seedream' && !seedreamConfig) ||
						(selectedService === 'midjourney' &&
							midJourneyConfig &&
							userCredits <
								(selectedMode === 'fast'
									? midJourneyConfig.fast_credits || 10
									: selectedMode === 'relax'
										? midJourneyConfig.relax_credits || 5
										: selectedMode === 'turbo'
											? midJourneyConfig.turbo_credits || 15
											: 10)) ||
						(selectedService === 'seedream' &&
							seedreamConfig &&
							userCredits < (seedreamConfig.credits_per_generation || 1))}
					class="w-full py-3 bg-gradient-to-r from-pink-500 to-purple-600 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:from-pink-600 hover:to-purple-700 transition-all flex items-center justify-center space-x-2"
				>
					{#if generating}
						<Spinner className="w-4 h-4" />
						<span>生成中...</span>
					{:else}
						<span
							>生成图像 ({#if selectedService === 'midjourney' && midJourneyConfig}
								{#if selectedMode === 'fast'}
									{midJourneyConfig.fast_credits || 10}{$creditName}
								{:else if selectedMode === 'relax'}
									{midJourneyConfig.relax_credits || 5}{$creditName}
								{:else if selectedMode === 'turbo'}
									{midJourneyConfig.turbo_credits || 15}{$creditName}
								{:else}
									10{$creditName}
								{/if}
							{:else if selectedService === 'seedream' && seedreamConfig}
								{seedreamConfig.credits_per_generation || 1}{$creditName}
							{:else}
								配置加载中...
							{/if})</span
						>
					{/if}
				</button>
			</div>
		</div>

		<!-- 右侧图像展示区域 -->
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
							placeholder="搜索图像历史..."
							class="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg"
						/>
					</div>
					<div class="text-sm text-gray-500">
						共 {filteredImages.length} 张图像
					</div>
				</div>
			</div>

			<!-- 图像网格 -->
			<div class="flex-1 p-4 overflow-y-auto">
				{#if !loaded}
					<div class="flex items-center justify-center h-64">
						<Spinner className="w-8 h-8" />
					</div>
				{:else if filteredImages.length === 0}
					<div class="flex flex-col items-center justify-center h-64 text-gray-500">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 24 24"
							fill="currentColor"
							class="w-16 h-16 mb-4 text-gray-300"
						>
							<path
								d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
							/>
						</svg>
						<p class="text-lg font-medium mb-2">还没有生成任何图像</p>
						<p class="text-sm">在左侧面板中输入描述，开始创建你的第一张AI图像</p>
					</div>
				{:else}
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
						{#each filteredImages as image (image.id)}
							<div
								class="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
							>
								<!-- 图像 -->
								<div class="relative aspect-square">
									{#if image.status === 'generating'}
										<div
											class="w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center"
										>
											<div class="text-center">
												<Spinner className="w-8 h-8 mx-auto mb-2" />
												<div class="text-sm text-gray-600 dark:text-gray-400">
													{image.message}
												</div>
												{#if image.progress > 0}
													<div class="text-xs text-gray-500 mt-1">
														进度: {image.progress}%
													</div>
												{/if}
											</div>
										</div>
									{:else if image.status === 'failed'}
										<div
											class="w-full h-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center"
										>
											<div class="text-center text-red-600 dark:text-red-400">
												<svg
													xmlns="http://www.w3.org/2000/svg"
													viewBox="0 0 24 24"
													fill="currentColor"
													class="w-8 h-8 mx-auto mb-2"
												>
													<path
														fill-rule="evenodd"
														d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z"
														clip-rule="evenodd"
													/>
												</svg>
												<div class="text-sm">生成失败</div>
												<div class="text-xs mt-1">{image.message}</div>
											</div>
										</div>
									{:else if image.image}
										<img
											src={image.image}
											alt={image.prompt}
											class="w-full h-full object-cover cursor-pointer hover:opacity-90 transition-opacity"
											on:click={() => openImageModal(image)}
										/>
									{:else}
										<div
											class="w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center"
										>
											<div class="text-gray-500">无图像</div>
										</div>
									{/if}

									<!-- 服务标识 -->
									<div class="absolute top-2 left-2">
										<span
											class="px-2 py-1 text-xs font-medium rounded-full {image.service ===
											'MidJourney'
												? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-200'
												: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-200'}"
										>
											{image.service}
										</span>
									</div>

									<!-- 操作按钮 -->
									{#if image.status === 'completed' && image.image}
										<div
											class="absolute top-2 right-2 flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity"
										>
											<button
												on:click|stopPropagation={() =>
													downloadImage(image.image, `${image.service}_${image.id}.jpg`)}
												class="p-1.5 bg-black/60 text-white rounded-full hover:bg-black/80 transition-colors"
												title="下载图像"
											>
												<svg
													xmlns="http://www.w3.org/2000/svg"
													viewBox="0 0 20 20"
													fill="currentColor"
													class="w-4 h-4"
												>
													<path
														d="M10.75 2.75a.75.75 0 00-1.5 0v8.614L6.295 8.235a.75.75 0 10-1.09 1.03l4.25 4.5a.75.75 0 001.09 0l4.25-4.5a.75.75 0 00-1.09-1.03L10.75 11.364V2.75z"
													/>
													<path
														d="M3.5 12.75a.75.75 0 00-1.5 0v2.5A2.75 2.75 0 004.75 18h10.5A2.75 2.75 0 0018 15.25v-2.5a.75.75 0 00-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5z"
													/>
												</svg>
											</button>
										</div>
									{:else if image.status === 'failed'}
										<div
											class="absolute top-2 right-2 flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity"
										>
											<button
												on:click|stopPropagation={() => deleteFailedTask(image)}
												class="p-1.5 bg-red-600/80 text-white rounded-full hover:bg-red-700/90 transition-colors"
												title="删除失败任务"
											>
												<svg
													xmlns="http://www.w3.org/2000/svg"
													viewBox="0 0 20 20"
													fill="currentColor"
													class="w-4 h-4"
												>
													<path
														fill-rule="evenodd"
														d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z"
														clip-rule="evenodd"
													/>
												</svg>
											</button>
										</div>
									{/if}
								</div>

								<!-- 图像信息 -->
								<div class="p-4">
									<div class="text-sm text-gray-900 dark:text-gray-100 mb-2 line-clamp-2">
										{image.prompt}
									</div>
									<div class="flex items-center justify-between text-xs text-gray-500 mb-2">
										<span>{image.model}</span>
										<span>{image.timestamp.toLocaleString('zh-CN')}</span>
									</div>

									<!-- 操作按钮 -->
									{#if image.status === 'completed'}
										<div class="flex space-x-2">
											<button
												on:click={() => copyPrompt(image.prompt)}
												class="flex-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
											>
												复制提示词
											</button>
											<button
												on:click={() => regenerateWithPrompt(image.prompt)}
												class="flex-1 px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800/40 transition-colors"
											>
												重新生成
											</button>
										</div>
									{:else if image.status === 'failed'}
										<div class="flex space-x-2">
											<button
												on:click={() => copyPrompt(image.prompt)}
												class="flex-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
											>
												复制提示词
											</button>
											<button
												on:click={() => regenerateWithPrompt(image.prompt)}
												class="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800/40 transition-colors"
											>
												重新生成
											</button>
											<button
												on:click={() => deleteFailedTask(image)}
												class="px-2 py-1 text-xs bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded hover:bg-red-200 dark:hover:bg-red-800/40 transition-colors"
											>
												删除任务
											</button>
										</div>
									{/if}

									<!-- MidJourney动作按钮 -->
									{#if image.service === 'MidJourney' && image.actions && image.actions.length > 0 && image.status === 'completed'}
										<div class="mt-2 grid grid-cols-4 gap-1">
											{#each image.actions as action}
												<button
													on:click={() => executeAction(image, action)}
													disabled={executingAction && selectedImageForAction === image.id}
													class="px-1 py-1 text-xs bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded hover:bg-green-200 dark:hover:bg-green-800/40 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
												>
													{#if executingAction && selectedImageForAction === image.id}
														<Spinner className="w-3 h-3 mx-auto" />
													{:else}
														{action.label}
													{/if}
												</button>
											{/each}
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
</div>

<!-- 图片预览模态框 -->
{#if showImageModal && previewImage}
	<div
		class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
		on:click={() => (showImageModal = false)}
	>
		<div
			class="max-w-4xl max-h-full bg-white dark:bg-gray-800 rounded-lg overflow-hidden"
			on:click|stopPropagation
		>
			<div class="p-4 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center justify-between">
					<div class="flex items-center space-x-3">
						<span
							class="px-2 py-1 text-xs font-medium rounded-full {previewImage.service ===
							'MidJourney'
								? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-200'
								: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-200'}"
						>
							{previewImage.service}
						</span>
						<span class="text-sm text-gray-600 dark:text-gray-400">{previewImage.model}</span>
					</div>
					<button
						on:click={() => (showImageModal = false)}
						class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							class="w-5 h-5"
						>
							<path
								d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
							/>
						</svg>
					</button>
				</div>
			</div>
			<div class="p-4">
				<img
					src={previewImage.image}
					alt={previewImage.prompt}
					class="w-full h-auto max-h-[60vh] object-contain rounded"
				/>
				<div class="mt-4">
					<div class="text-sm text-gray-900 dark:text-gray-100 mb-2">
						{previewImage.prompt}
					</div>
					<div class="text-xs text-gray-500 space-y-1">
						<div>生成时间: {previewImage.timestamp.toLocaleString('zh-CN')}</div>
						{#if previewImage.seed}
							<div>种子值: {previewImage.seed}</div>
						{/if}
						{#if previewImage.width && previewImage.height}
							<div>尺寸: {previewImage.width}×{previewImage.height}</div>
						{/if}
						{#if previewImage.scale}
							<div>文本影响: {previewImage.scale}</div>
						{/if}
					</div>
					<div class="mt-4 flex space-x-2">
						<button
							on:click={() =>
								downloadImage(previewImage.image, `${previewImage.service}_${previewImage.id}.jpg`)}
							class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
						>
							下载图像
						</button>
						<button
							on:click={() => copyPrompt(previewImage.prompt)}
							class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
						>
							复制提示词
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}
