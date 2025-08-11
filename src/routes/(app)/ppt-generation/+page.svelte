<script>
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user, creditName, showSidebar, mobile, WEBUI_NAME } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';
	import {
		getTemplateOptions,
		getTemplates,
		createPptTask,
		generateContent,
		generatePpt,
		getUserPpts,
		downloadPpt as downloadPptApi,
		GENERATION_TYPES
	} from '$lib/apis/ppt.js';

	const i18n = getContext('i18n');

	// PPT 生成状态
	let loading = false;
	let generating = false;
	let taskList = [];
	let userCredits = 0;
	let pptEnabled = false;
	let pptConfig = null;
	let creditsPerPpt = 10; // 每次PPT生成消耗的积分

	// PPT 生成表单数据
	let generationType = 'topic'; // 'topic', 'file', 'markdown', 'url'
	let topicInput = '';
	let fileInput = null;
	let markdownInput = '';
	let urlInput = '';
	let language = 'zh';
	let scene = '通用场景';
	let audience = '大众';
	let templateId = '';

	// 模板相关
	let templates = [];
	let templateFilters = {
		category: '',
		style: '',
		themeColor: ''
	};
	let templateOptions = {
		category: [],
		style: [],
		themeColor: []
	};

	// 任务和历史
	let searchTerm = '';
	let selectedTask = null;

	// 生成选项
	const generationTypes = [
		{ value: 'topic', label: '智能生成', description: '输入主题或要求，AI智能生成PPT' },
		{ value: 'file', label: '文件生成', description: '上传文档文件生成PPT' },
		{ value: 'markdown', label: 'Markdown生成', description: '输入Markdown大纲生成PPT' },
		{ value: 'url', label: '网页生成', description: '输入网页链接生成PPT' }
	];

	const languages = [
		{ value: 'zh', label: '简体中文' },
		{ value: 'zh-Hant', label: '繁体中文' },
		{ value: 'en', label: 'English' },
		{ value: 'ja', label: '日本語' },
		{ value: 'ko', label: '한국어' }
	];

	const scenes = [
		'通用场景',
		'教学课件',
		'工作总结',
		'工作计划',
		'项目汇报',
		'解决方案',
		'研究报告',
		'会议材料',
		'产品介绍',
		'公司介绍',
		'商业计划书',
		'科普宣传',
		'公众演讲'
	];

	const audiences = ['大众', '学生', '老师', '上级领导', '下属', '面试官', '同事'];

	// 加载模板选项
	const loadTemplateOptions = async () => {
		try {
			const response = await getTemplateOptions($user.token);
			if (response && response.data) {
				templateOptions = response.data;
			}
		} catch (error) {
			console.error('加载模板选项失败:', error);
			// 使用默认选项作为后备
			templateOptions = {
				category: [
					{ name: '全部', value: '' },
					{ name: '年终总结', value: '年终总结' },
					{ name: '教育培训', value: '教育培训' },
					{ name: '商业计划书', value: '商业计划书' }
				],
				style: [
					{ name: '全部', value: '' },
					{ name: '扁平简约', value: '扁平简约' },
					{ name: '商务科技', value: '商务科技' },
					{ name: '文艺清新', value: '文艺清新' }
				],
				themeColor: [
					{ name: '全部', value: '' },
					{ name: '蓝色', value: '#589AFD' },
					{ name: '绿色', value: '#61D328' },
					{ name: '红色', value: '#E05757' }
				]
			};
		}
	};

	// 加载模板列表
	const loadTemplates = async () => {
		try {
			const response = await getTemplates($user.token, {
				page: 1,
				size: 50,
				filters: {
					type: 1, // 系统模板
					category: templateFilters.category,
					style: templateFilters.style,
					themeColor: templateFilters.themeColor
				}
			});

			if (response && response.data) {
				templates = response.data;
			}
		} catch (error) {
			console.error('加载模板列表失败:', error);
			// 使用默认模板作为后备
			templates = [
				{
					id: 'template_1',
					coverUrl: '', // 空URL会触发占位符显示
					category: '商业计划书',
					style: '商务科技',
					themeColor: '#589AFD',
					subject: '商业计划书模板',
					num: 20
				},
				{
					id: 'template_2',
					coverUrl: '', // 空URL会触发占位符显示
					category: '教育培训',
					style: '扁平简约',
					themeColor: '#61D328',
					subject: '教育培训模板',
					num: 15
				}
			];
		}
	};

	// 根据生成类型获取任务类型
	const getTaskTypeByGeneration = (genType) => {
		switch (genType) {
			case 'topic':
				return GENERATION_TYPES.TOPIC;
			case 'file':
				return GENERATION_TYPES.FILE;
			case 'markdown':
				return GENERATION_TYPES.MARKDOWN;
			case 'url':
				return GENERATION_TYPES.URL;
			default:
				return GENERATION_TYPES.TOPIC;
		}
	};

	// 构建带token的图片URL
	const buildImageUrlWithToken = (imageUrl) => {
		if (!imageUrl || !imageUrl.trim()) {
			return '';
		}

		if (!pptConfig?.api_key) {
			return imageUrl;
		}

		// 如果URL已经有参数，用&连接，否则用?连接
		const separator = imageUrl.includes('?') ? '&' : '?';
		return `${imageUrl}${separator}token=${encodeURIComponent(pptConfig.api_key)}`;
	};

	// 获取用户积分信息
	const loadUserCredits = async () => {
		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/credit/status`, {
				headers: {
					Authorization: `Bearer ${$user.token}`
				}
			});

			if (response.ok) {
				const creditData = await response.json();
				userCredits = parseFloat(creditData.credit || 0);
				console.log('用户积分已加载:', userCredits);
			} else {
				console.warn('获取用户积分失败:', response.status);
				userCredits = 0;
			}
		} catch (error) {
			console.error('获取用户积分异常:', error);
			userCredits = 0;
		}
	};

	// 生成PPT
	const generatePptTask = async () => {
		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		if (!pptEnabled) {
			toast.error('PPT功能未启用，请联系管理员配置');
			return;
		}

		if (!templateId) {
			toast.error('请选择一个模板');
			return;
		}

		console.log('生成PPT前的检查:', {
			templateId,
			generationType,
			pptEnabled,
			userToken: !!$user?.token
		});

		// 验证输入
		switch (generationType) {
			case 'topic':
				if (!topicInput.trim()) {
					toast.error('请输入主题或要求');
					return;
				}
				break;
			case 'file':
				if (!fileInput) {
					toast.error('请选择文件');
					return;
				}
				break;
			case 'markdown':
				if (!markdownInput.trim()) {
					toast.error('请输入Markdown内容');
					return;
				}
				break;
			case 'url':
				if (!urlInput.trim()) {
					toast.error('请输入网页链接');
					return;
				}
				break;
		}

		generating = true;
		try {
			// 步骤1：创建任务
			const taskType = getTaskTypeByGeneration(generationType);
			const content = getContentByType();
			const files = generationType === 'file' && fileInput ? [fileInput] : [];

			const taskResponse = await createPptTask($user.token, taskType, content, files);
			console.log('创建任务成功，响应:', taskResponse);

			// 即梦PPT API使用code=0表示成功，不是200
			if (taskResponse.code !== 0) {
				const errorMsg = taskResponse?.message || '创建任务失败';
				console.error('创建任务失败:', { taskResponse, errorMsg, code: taskResponse.code });
				throw new Error(errorMsg);
			}

			const taskId = taskResponse.data.id;
			console.log('获取到任务ID:', taskId);
			toast.success('任务创建成功，正在生成大纲内容...');

			// 步骤2：生成大纲内容
			const contentOptions = {
				stream: false, // 简化为非流式
				length: 'medium',
				scene: scene,
				audience: audience,
				lang: language
			};

			const contentResponse = await generateContent($user.token, taskId, contentOptions);
			console.log('生成内容完整响应:', contentResponse);

			if (!contentResponse || contentResponse.code !== 0) {
				throw new Error(contentResponse?.message || '生成内容失败');
			}

			console.log('内容响应数据:', contentResponse.data);
			const markdown =
				contentResponse.data?.markdown || contentResponse.data?.content || contentResponse.data;
			console.log('提取的markdown内容:', {
				markdown: typeof markdown === 'string' ? markdown.slice(0, 200) + '...' : markdown,
				length: markdown?.length,
				type: typeof markdown
			});

			// 确保markdown是字符串格式
			let markdownText;
			if (typeof markdown === 'string') {
				markdownText = markdown;
			} else if (typeof markdown === 'object' && markdown !== null) {
				// 如果是对象，尝试转换为JSON字符串或提取text字段
				markdownText = markdown.text || markdown.markdown || JSON.stringify(markdown, null, 2);
			} else {
				markdownText = String(markdown || '');
			}

			if (!markdownText || markdownText.length === 0) {
				console.error('Markdown内容为空:', { contentResponse, markdown, markdownText });
				throw new Error('生成的大纲内容为空，无法创建PPT');
			}

			toast.success('大纲内容生成完成，正在生成PPT...');

			// 步骤3：生成PPT
			console.log('准备生成PPT:', {
				taskId,
				templateId,
				markdownText: markdownText.slice(0, 100) + '...',
				markdownLength: markdownText.length
			});
			const pptResponse = await generatePpt($user.token, taskId, templateId, markdownText);
			console.log('PPT生成响应:', pptResponse);

			if (!pptResponse || pptResponse.code !== 0) {
				throw new Error(pptResponse?.message || '生成PPT失败');
			}

			// 智能提取PPT ID，尝试多种可能的字段名
			const pptId =
				pptResponse.data?.id ||
				pptResponse.data?.pptId ||
				pptResponse.data?.ppt_id ||
				pptResponse.data?.taskId ||
				pptResponse.id ||
				taskId; // 使用任务ID作为最后备选

			console.log('提取的PPT ID:', {
				pptId,
				responseData: pptResponse.data,
				fullResponse: pptResponse,
				taskId
			});

			// 确保至少有一个有效的ID用于下载
			const finalPptId = pptId || taskId;
			console.log('最终使用的PPT ID:', finalPptId);

			// 创建任务对象并添加到列表
			const newTask = {
				id: taskId,
				pptId: finalPptId,
				taskId: taskId, // 保留任务ID作为备选
				type: generationType,
				content: content,
				templateId,
				status: 'completed',
				createTime: new Date().toISOString(),
				subject: topicInput || markdownInput || urlInput || fileInput?.name || 'PPT生成任务',
				markdown: markdownText
			};

			console.log('创建的任务对象:', newTask);

			taskList = [newTask, ...taskList];
			toast.success('PPT生成完成！可以在右侧任务列表中下载。');

			// 重置表单
			resetForm();
		} catch (error) {
			console.error('生成PPT失败:', error);
			const errorMessage = error instanceof Error ? error.message : '生成PPT失败';
			toast.error('生成PPT失败: ' + errorMessage);
		} finally {
			generating = false;
		}
	};

	// 根据类型获取内容
	const getContentByType = () => {
		switch (generationType) {
			case 'topic':
				return topicInput;
			case 'markdown':
				return markdownInput;
			case 'url':
				return urlInput;
			case 'file':
				return fileInput?.name || '';
			default:
				return '';
		}
	};

	// 重置表单
	const resetForm = () => {
		topicInput = '';
		markdownInput = '';
		urlInput = '';
		fileInput = null;
		if (document.getElementById('file-input')) {
			document.getElementById('file-input').value = '';
		}
	};

	// 删除任务
	const deleteTask = async (taskId) => {
		try {
			// 从本地列表中删除（PPT服务器上的数据保持不变）
			taskList = taskList.filter((task) => task.id !== taskId);
			toast.success('任务已从列表中移除');
		} catch (error) {
			console.error('删除任务失败:', error);
			toast.error('删除任务失败');
		}
	};

	// 下载PPT
	const downloadPptFile = async (task) => {
		try {
			console.log('准备下载PPT，任务对象:', task);

			// 尝试多种ID字段
			const downloadId = task.pptId || task.id || task.taskId;
			console.log('可用的下载ID:', {
				pptId: task.pptId,
				id: task.id,
				taskId: task.taskId,
				finalId: downloadId
			});

			if (!downloadId) {
				console.error('所有PPT ID都缺失:', { task });
				toast.error('PPT ID不存在，请重新生成PPT');
				return;
			}

			toast.info('正在准备下载...');
			console.log('调用下载API，使用ID:', downloadId);

			try {
				const response = await downloadPptApi($user.token, downloadId);
				console.log('下载API响应:', response);

				if (response && response.code === 0) {
					toast.success('PPT下载成功');
				} else {
					throw new Error(response?.message || '下载失败');
				}
			} catch (downloadError) {
				console.error('下载失败，尝试备用方案:', downloadError);

				// 如果使用pptId失败，尝试使用任务ID
				if (task.pptId && task.id && task.pptId !== task.id) {
					console.log('尝试使用任务ID下载:', task.id);
					const backupResponse = await downloadPptApi($user.token, task.id);

					if (backupResponse && backupResponse.code === 0) {
						toast.success('PPT下载成功');
						return;
					}
				}

				throw downloadError;
			}
		} catch (error) {
			console.error('下载PPT失败:', error);
			toast.error('下载PPT失败: ' + error.message);
		}
	};

	// 检查PPT功能状态并加载配置
	const checkPptStatus = async () => {
		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/ppt/status`, {
				headers: {
					Authorization: `Bearer ${$user.token}`
				}
			});

			if (response.status === 401) {
				toast.error('请先登录');
				return false;
			}

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			const status = await response.json();

			// 保存API密钥用于图片URL，并获取积分消耗信息
			if (status.api_key) {
				pptConfig = { api_key: status.api_key };
				console.log('PPT API密钥已获取，用于模板图片访问');
			}

			// 尝试获取更完整的配置信息（包括积分消耗）
			try {
				const configResponse = await fetch(`${WEBUI_API_BASE_URL}/ppt/config`, {
					headers: {
						Authorization: `Bearer ${$user.token}`
					}
				});

				if (configResponse.ok) {
					const configData = await configResponse.json();
					if (configData.credits_per_ppt) {
						creditsPerPpt = configData.credits_per_ppt;
						console.log('PPT积分消耗已获取:', creditsPerPpt);
					}
				}
			} catch (err) {
				console.warn('获取PPT完整配置失败，使用默认积分消耗:', err);
				// 使用默认值，不影响主要功能
			}

			if (!status.enabled) {
				toast.error('PPT功能未启用，请联系管理员配置');
				return false;
			}

			if (status.status !== 'online') {
				toast.warning(`PPT服务状态: ${status.message}`);
			}

			return true;
		} catch (error) {
			console.error('检查PPT状态失败:', error);
			// 如果是网络错误或解析错误，显示友好的错误信息
			if (error.message.includes('SyntaxError') || error.message.includes('JSON')) {
				toast.error('PPT服务响应格式错误');
			} else {
				toast.error('无法连接到PPT服务');
			}
			return false;
		}
	};

	// 加载用户历史任务
	const loadUserTasks = async () => {
		try {
			const response = await getUserPpts($user.token, 1, 20);
			if (response && response.code === 0 && response.data) {
				// 转换为本地任务格式，确保有完整的ID信息
				taskList = response.data.map((ppt) => {
					const taskId = ppt.taskId || ppt.id;
					const pptId = ppt.id || ppt.pptId || taskId;

					return {
						id: taskId,
						pptId: pptId,
						taskId: taskId, // 备选ID
						type: 'topic', // 默认类型
						content: '',
						templateId: ppt.templateId || '',
						status: 'completed',
						createTime: ppt.createTime,
						subject: ppt.name || ppt.title || 'PPT'
					};
				});

				console.log('加载的历史任务:', taskList);
			}
		} catch (error) {
			console.error('加载用户任务失败:', error);
			// 不显示错误，使用空列表
		}
	};

	onMount(async () => {
		if (!$user?.token) {
			toast.error('请先登录');
			return;
		}

		const isEnabled = await checkPptStatus();
		pptEnabled = isEnabled;
		if (isEnabled) {
			await Promise.all([
				loadTemplateOptions(),
				loadTemplates(),
				loadUserTasks(),
				loadUserCredits()
			]);
		}
	});
</script>

<svelte:head>
	<title>PPT生成 | {`${$WEBUI_NAME}`}</title>
</svelte:head>

<div class="flex flex-col h-screen bg-white dark:bg-gray-900 overflow-hidden">
	<!-- 头部 -->
	<div
		class="flex flex-col sm:flex-row items-start sm:items-center justify-between px-3 sm:px-6 py-3 sm:py-4 border-b border-gray-200 dark:border-gray-700 space-y-2 sm:space-y-0"
	>
		<div class="flex items-center space-x-3">
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

			<div
				class="w-8 h-8 bg-orange-100 dark:bg-orange-900 rounded-lg flex items-center justify-center"
			>
				<svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 19v-6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2zm0 0V9a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v10m-6 0a2 2 0 0 0 2 2h2a2 2 0 0 0-2-2m0 0V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-2a2 2 0 0 1 2-2z"
					/>
				</svg>
			</div>
			<h1 class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">PPT生成</h1>
		</div>

		<div
			class="flex flex-col sm:flex-row items-start sm:items-center space-y-1 sm:space-y-0 sm:space-x-3 text-xs sm:text-sm text-gray-600 dark:text-gray-400 w-full sm:w-auto"
		>
			<div class="flex items-center space-x-1">
				<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
					<path
						d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4zM18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z"
					/>
				</svg>
				<span>{$creditName}余额: {userCredits.toFixed(2)}</span>
			</div>
			<div class="flex items-center space-x-1 text-orange-600 dark:text-orange-400">
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 19v-6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2zm0 0V9a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v10m-6 0a2 2 0 0 0 2 2h2a2 2 0 0 0-2-2m0 0V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-2a2 2 0 0 1 2-2z"
					/>
				</svg>
				<span>生成消耗: {creditsPerPpt}{$creditName}</span>
			</div>
		</div>
	</div>

	{#if !pptEnabled}
		<!-- PPT功能未启用提示 -->
		<div class="flex-1 flex items-center justify-center">
			<div class="text-center">
				<div
					class="w-16 h-16 bg-orange-100 dark:bg-orange-900 rounded-full flex items-center justify-center mx-auto mb-4"
				>
					<svg
						class="w-8 h-8 text-orange-600"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5z"
						/>
					</svg>
				</div>
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">PPT功能未启用</h3>
				<p class="text-gray-600 dark:text-gray-400 mb-4">请联系管理员在设置中配置PPT服务</p>
				<div class="text-sm text-gray-500 dark:text-gray-500">
					管理员可在"设置 > PPT配置"中配置API密钥和服务地址
				</div>
			</div>
		</div>
	{:else}
		<div class="flex flex-col lg:flex-row flex-1 overflow-auto lg:overflow-hidden min-h-0">
			<!-- 主内容区 -->
			<div class="flex-1 flex flex-col min-h-0 overflow-auto lg:overflow-hidden">
				<!-- 生成表单 -->
				<div class="p-3 sm:p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
					<div class="max-w-4xl mx-auto space-y-4 sm:space-y-6">
						<!-- 生成类型选择 -->
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
								生成方式
							</label>
							<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
								{#each generationTypes as type}
									<div
										class="relative cursor-pointer rounded-lg border p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors {generationType ===
										type.value
											? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
											: 'border-gray-200 dark:border-gray-700'}"
										on:click={() => (generationType = type.value)}
									>
										<div class="flex items-center space-x-3">
											<input
												type="radio"
												bind:group={generationType}
												value={type.value}
												class="text-blue-600"
											/>
											<div>
												<div class="text-sm font-medium text-gray-900 dark:text-white">
													{type.label}
												</div>
												<div class="text-xs text-gray-500 dark:text-gray-400">
													{type.description}
												</div>
											</div>
										</div>
									</div>
								{/each}
							</div>
						</div>

						<!-- 输入区域 -->
						<div>
							{#if generationType === 'topic'}
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									主题或要求
								</label>
								<textarea
									bind:value={topicInput}
									placeholder="请描述您想要生成的PPT主题和具体要求..."
									class="w-full h-24 sm:h-32 px-3 py-2 text-sm sm:text-base border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
								></textarea>
							{:else if generationType === 'file'}
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									上传文件
								</label>
								<input
									id="file-input"
									type="file"
									accept=".doc,.docx,.pdf,.ppt,.pptx,.txt,.md,.xls,.xlsx"
									on:change={(e) => (fileInput = e.target.files[0])}
									class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
								/>
								<div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
									支持格式: doc, docx, pdf, ppt, pptx, txt, md, xls, xlsx (最大50MB)
								</div>
							{:else if generationType === 'markdown'}
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Markdown大纲
								</label>
								<textarea
									bind:value={markdownInput}
									placeholder="# 主题&#10;## 章节1&#10;### 页面标题&#10;- 内容要点"
									class="w-full h-24 sm:h-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-xs sm:text-sm"
								></textarea>
							{:else if generationType === 'url'}
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									网页链接
								</label>
								<input
									bind:value={urlInput}
									type="url"
									placeholder="https://example.com/article"
									class="w-full px-3 py-2 text-sm sm:text-base border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								/>
							{/if}
						</div>

						<!-- 生成参数 -->
						<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									语言
								</label>
								<select
									bind:value={language}
									class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
								>
									{#each languages as lang}
										<option value={lang.value}>{lang.label}</option>
									{/each}
								</select>
							</div>

							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									演示场景
								</label>
								<select
									bind:value={scene}
									class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
								>
									{#each scenes as sceneOption}
										<option value={sceneOption}>{sceneOption}</option>
									{/each}
								</select>
							</div>

							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									目标受众
								</label>
								<select
									bind:value={audience}
									class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
								>
									{#each audiences as audienceOption}
										<option value={audienceOption}>{audienceOption}</option>
									{/each}
								</select>
							</div>
						</div>
					</div>
				</div>

				<!-- 模板选择 -->
				<div
					class="flex-1 p-3 sm:p-6 overflow-y-auto min-h-0 lg:min-h-0"
					style="min-height: 400px;"
				>
					<div class="max-w-4xl mx-auto">
						<div
							class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 space-y-3 sm:space-y-0"
						>
							<h2 class="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
								选择模板
							</h2>

							<!-- 模板筛选 -->
							<div
								class="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-3 w-full sm:w-auto"
							>
								<select
									bind:value={templateFilters.category}
									class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
								>
									{#each templateOptions.category as option}
										<option value={option.value}>{option.name}</option>
									{/each}
								</select>
								<select
									bind:value={templateFilters.style}
									class="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
								>
									{#each templateOptions.style as option}
										<option value={option.value}>{option.name}</option>
									{/each}
								</select>
							</div>
						</div>

						<!-- 模板网格 -->
						<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
							{#each templates as template}
								<div
									class="relative group cursor-pointer rounded-lg border overflow-hidden hover:shadow-lg transition-shadow {templateId ===
									template.id
										? 'border-blue-500 ring-2 ring-blue-200 dark:ring-blue-800'
										: 'border-gray-200 dark:border-gray-700'}"
									on:click={() => (templateId = template.id)}
								>
									<div class="aspect-video bg-gray-200 dark:bg-gray-700 relative overflow-hidden">
										{#if template.coverUrl && template.coverUrl.trim()}
											<img
												src={buildImageUrlWithToken(template.coverUrl)}
												alt={template.subject}
												class="w-full h-full object-cover"
												on:error={(e) => {
													e.target.style.display = 'none';
													e.target.parentElement.querySelector(
														'.fallback-placeholder'
													).style.display = 'flex';
												}}
											/>
										{/if}
										<!-- 图片加载失败或无URL时的占位符 -->
										<div
											class="fallback-placeholder w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-600 dark:to-gray-700 text-gray-500 dark:text-gray-400"
											style="display: {template.coverUrl && template.coverUrl.trim()
												? 'none'
												: 'flex'};"
										>
											<svg
												class="w-12 h-12 mb-2"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 00-2-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2 2z"
												/>
											</svg>
											<div class="text-xs text-center">
												<div class="font-medium">{template.category}</div>
												<div class="opacity-75">{template.style}</div>
											</div>
										</div>
									</div>
									<div class="p-3">
										<div class="font-medium text-sm text-gray-900 dark:text-white mb-1">
											{template.subject}
										</div>
										<div class="text-xs text-gray-500 dark:text-gray-400 space-x-2">
											<span>{template.category}</span>
											<span>•</span>
											<span>{template.num}页</span>
										</div>
									</div>
									{#if templateId === template.id}
										<div class="absolute inset-0 bg-blue-500/10 flex items-center justify-center">
											<div
												class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center"
											>
												<svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
													<path
														fill-rule="evenodd"
														d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
														clip-rule="evenodd"
													/>
												</svg>
											</div>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				</div>

				<!-- 底部生成按钮 -->
				<div
					class="p-3 sm:p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex-shrink-0"
				>
					<div class="max-w-4xl mx-auto flex justify-center">
						<button
							on:click={generatePptTask}
							disabled={generating || !templateId}
							class="w-full sm:w-auto px-6 sm:px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors flex items-center justify-center space-x-2 text-sm sm:text-base"
						>
							{#if generating}
								<Spinner className="w-4 h-4" />
								<span>生成中...</span>
							{:else}
								<Plus className="w-4 h-4" />
								<span>生成PPT (消耗{creditsPerPpt}{$creditName})</span>
							{/if}
						</button>
					</div>
				</div>
			</div>

			<!-- 右侧任务列表 -->
			<div
				class="w-full lg:w-80 border-t lg:border-t-0 lg:border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex flex-col max-h-80 lg:max-h-none"
			>
				<div class="p-3 sm:p-4 border-b border-gray-200 dark:border-gray-700">
					<div class="flex items-center justify-between mb-3">
						<h2 class="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
							生成历史
						</h2>
						<div class="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
							{taskList.length} 个任务
						</div>
					</div>

					<!-- 搜索框 -->
					<div class="relative">
						<Search
							className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
						/>
						<input
							bind:value={searchTerm}
							placeholder="搜索任务..."
							class="w-full pl-9 pr-3 py-2 text-xs sm:text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						/>
					</div>
				</div>

				<div class="flex-1 overflow-y-auto">
					{#each taskList as task (task.id)}
						<div
							class="p-2 sm:p-3 border-b border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
						>
							<div
								class="flex flex-col sm:flex-row sm:items-start justify-between space-y-2 sm:space-y-0"
							>
								<div class="flex-1 min-w-0">
									<div
										class="font-medium text-xs sm:text-sm text-gray-900 dark:text-white truncate"
									>
										{task.subject}
									</div>
									<div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
										{new Date(task.createTime).toLocaleString()}
									</div>
									<div class="flex items-center mt-2 space-x-2">
										<div
											class="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full"
										>
											{task.status === 'processing'
												? '处理中'
												: task.status === 'completed'
													? '已完成'
													: task.status === 'failed'
														? '失败'
														: '等待中'}
										</div>
									</div>
								</div>
								<div class="flex items-center space-x-1 sm:ml-2 self-start sm:self-center">
									{#if task.status === 'completed'}
										<button
											on:click={() => downloadPptFile(task)}
											class="p-2 sm:p-1 text-green-600 hover:bg-green-100 dark:hover:bg-green-900 rounded touch-manipulation"
											title="下载PPT"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2z"
												/>
											</svg>
										</button>
									{/if}
									<button
										on:click={() => deleteTask(task.id)}
										class="p-2 sm:p-1 text-red-600 hover:bg-red-100 dark:hover:bg-red-900 rounded touch-manipulation"
										title="删除任务"
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
											/>
										</svg>
									</button>
								</div>
							</div>
						</div>
					{:else}
						<div
							class="flex flex-col items-center justify-center h-32 text-gray-500 dark:text-gray-400"
						>
							<svg class="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 19v-6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2zm0 0V9a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v10m-6 0a2 2 0 0 0 2 2h2a2 2 0 0 0-2-2m0 0V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-2a2 2 0 0 1 2-2z"
								/>
							</svg>
							<p class="text-sm">暂无PPT生成任务</p>
						</div>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	/* Mobile touch scrolling improvements */
	@media (max-width: 1023px) {
		.overflow-auto,
		.overflow-y-auto {
			-webkit-overflow-scrolling: touch;
			scroll-behavior: smooth;
		}

		/* Ensure proper touch scrolling on mobile */
		* {
			touch-action: manipulation;
		}

		/* Allow scroll in specific areas */
		[class*='overflow-auto'],
		[class*='overflow-y-auto'] {
			touch-action: auto;
		}

		/* Mobile layout adjustments */
		.flex-col.flex-1 {
			height: 100vh;
			max-height: 100vh;
		}

		/* Template selection area - make it much larger on mobile */
		.flex-1[style*='min-height: 400px'] {
			min-height: 60vh !important;
			flex-grow: 2 !important;
		}

		/* Form area - make it smaller on mobile */
		.flex-shrink-0 {
			flex-shrink: 0 !important;
		}

		/* Template grid specific mobile fixes */
		.grid.grid-cols-1 {
			height: auto !important;
			min-height: auto !important;
		}

		/* Right sidebar adjustments */
		.max-h-96 {
			max-height: 40vh !important;
		}
	}

	/* Desktop layout fixes */
	@media (min-width: 1024px) {
		.lg\\:overflow-hidden {
			overflow: hidden !important;
		}

		/* Reset mobile styles for desktop */
		.flex-1[style*='min-height: 400px'] {
			min-height: 0 !important;
			flex-grow: 1 !important;
		}
	}
</style>
