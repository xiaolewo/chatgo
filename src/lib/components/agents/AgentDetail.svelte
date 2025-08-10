<script>
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		getAgentAppById,
		submitAgentForm,
		toggleFavoriteApp,
		executeAgent
	} from '$lib/apis/agents';
	import { user } from '$lib/stores';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import FormRenderer from './FormRenderer.svelte';
	import { marked } from 'marked';
	// 移除 date-fns 依赖，使用简单的日期格式化

	// 配置marked选项
	marked.setOptions({
		gfm: true,
		breaks: true,
		headerIds: false,
		mangle: false
	});

	const i18n = getContext('i18n');

	// 从路由参数获取应用ID
	export let appId = $page.params.id;

	let app = null;
	let loading = false;
	let submitting = false;
	let formData = {};
	let formErrors = {};
	let isFavorited = false;
	let submission = null;
	let showResponse = false;
	let streamingResponse = '';
	let isStreaming = false;
	let streamController = null;

	// 历史记录相关状态
	let showHistory = false;
	let history = [];
	let selectedHistoryItem = null;

	onMount(async () => {
		await loadApp();
		await loadHistory();
	});

	const loadApp = async () => {
		if (!appId) {
			toast.error('应用ID无效');
			goto('/agents');
			return;
		}

		loading = true;

		try {
			// 模拟应用数据
			const mockApps = {
				'app-1': {
					id: 'app-1',
					display_name: '文档总结助手',
					description: '帮助您快速总结长篇文档内容，提取关键信息',
					detailed_description:
						'这是一个强大的文档总结工具，可以帮助您快速处理和分析各种类型的文档。无论是学术论文、商业报告还是技术文档，都能为您提供准确的摘要和关键信息提取。',
					category: 'productivity',
					icon: '📄',
					favorite_count: 15,
					usage_count: 120,
					created_at: Date.now(),
					status: 'active',
					form_config: {
						fields: [
							{
								type: 'file',
								name: 'document',
								label: '上传文档',
								required: true,
								allowed_types: ['.pdf', '.doc', '.docx', '.txt']
							},
							{
								type: 'select',
								name: 'summary_length',
								label: '总结长度',
								required: true,
								options: [
									{ value: 'short', label: '简短摘要' },
									{ value: 'medium', label: '中等长度' },
									{ value: 'detailed', label: '详细总结' }
								],
								default_value: 'medium'
							},
							{
								type: 'text',
								name: 'focus_areas',
								label: '重点关注领域（可选）',
								placeholder: '例如：技术细节、商业策略等',
								required: false
							}
						]
					}
				},
				'app-2': {
					id: 'app-2',
					display_name: '创意写作工具',
					description: '激发创意灵感，协助您创作小说、诗歌等文学作品',
					detailed_description:
						'专为创意写作设计的AI助手，能够帮助作家和创作者突破写作瓶颈，提供情节灵感、角色设定建议，以及风格化的文本生成。',
					category: 'creative',
					icon: '✍️',
					favorite_count: 28,
					usage_count: 85,
					created_at: Date.now(),
					status: 'active',
					form_config: {
						fields: [
							{
								type: 'select',
								name: 'writing_type',
								label: '写作类型',
								required: true,
								options: [
									{ value: 'novel', label: '小说' },
									{ value: 'poetry', label: '诗歌' },
									{ value: 'script', label: '剧本' },
									{ value: 'essay', label: '散文' }
								]
							},
							{
								type: 'text',
								name: 'theme',
								label: '主题或关键词',
								required: true,
								placeholder: '例如：爱情、冒险、科幻...'
							},
							{
								type: 'select',
								name: 'style',
								label: '写作风格',
								required: true,
								options: [
									{ value: 'modern', label: '现代风格' },
									{ value: 'classical', label: '古典风格' },
									{ value: 'humorous', label: '幽默风格' },
									{ value: 'serious', label: '严肃风格' }
								]
							},
							{
								type: 'number',
								name: 'word_count',
								label: '目标字数',
								required: true,
								min: 100,
								max: 5000,
								default_value: 500
							}
						]
					}
				},
				'app-3': {
					id: 'app-3',
					display_name: '数据分析师',
					description: '分析数据趋势，生成可视化图表和深度分析报告',
					detailed_description:
						'专业的数据分析工具，能够处理各种格式的数据文件，提供统计分析、趋势预测和可视化报告。适用于商业分析、市场研究和学术研究等场景。',
					category: 'analysis',
					icon: '📊',
					favorite_count: 42,
					usage_count: 200,
					created_at: Date.now(),
					status: 'active',
					form_config: {
						fields: [
							{
								type: 'file',
								name: 'data_file',
								label: '数据文件',
								required: true,
								allowed_types: ['.csv', '.xlsx', '.json']
							},
							{
								type: 'select',
								name: 'analysis_type',
								label: '分析类型',
								required: true,
								options: [
									{ value: 'descriptive', label: '描述性分析' },
									{ value: 'predictive', label: '预测分析' },
									{ value: 'correlation', label: '相关性分析' },
									{ value: 'trend', label: '趋势分析' }
								]
							},
							{
								type: 'checkbox',
								name: 'output_formats',
								label: '输出格式',
								required: true,
								options: [
									{ value: 'report', label: '分析报告' },
									{ value: 'charts', label: '可视化图表' },
									{ value: 'summary', label: '数据摘要' }
								],
								default_value: ['report']
							}
						]
					}
				},
				'app-4': {
					id: 'app-4',
					display_name: '教案生成助手',
					description: '根据学科、阶段、教材等信息，智能生成专业的教案内容',
					detailed_description:
						'专业的智能教案生成工具，为教育工作者提供个性化的教案设计服务。支持多学科、多阶段、多版本教材，能够根据具体的课题和课时要求，生成符合教学规范的完整教案，包括教学目标、重点难点、教学过程和板书设计等。',
					category: 'productivity',
					icon: '📚',
					favorite_count: 35,
					usage_count: 168,
					created_at: Date.now(),
					status: 'active',
					form_config: {
						fields: [
							{
								type: 'select',
								name: 'subject',
								label: '学科',
								required: true,
								options: [
									{ value: 'chinese', label: '语文' },
									{ value: 'math', label: '数学' },
									{ value: 'english', label: '英语' }
								],
								default_value: 'chinese'
							},
							{
								type: 'select',
								name: 'stage',
								label: '阶段',
								required: true,
								options: [
									{ value: 'primary', label: '小学' },
									{ value: 'middle', label: '初中' },
									{ value: 'high', label: '高中' }
								],
								default_value: 'primary'
							},
							{
								type: 'select',
								name: 'textbook',
								label: '教材',
								required: true,
								options: [
									{ value: 'renjiao', label: '人教版' },
									{ value: 'sujiao', label: '苏教版' },
									{ value: 'beijing_normal', label: '北师大版' },
									{ value: 'xishi', label: '西师版' }
								],
								default_value: 'renjiao'
							},
							{
								type: 'select',
								name: 'volume',
								label: '册别',
								required: true,
								options: [
									{ value: 'grade1_vol1', label: '一年级上册' },
									{ value: 'grade1_vol2', label: '一年级下册' },
									{ value: 'grade2_vol1', label: '二年级上册' },
									{ value: 'grade2_vol2', label: '二年级下册' },
									{ value: 'grade3_vol1', label: '三年级上册' },
									{ value: 'grade3_vol2', label: '三年级下册' },
									{ value: 'grade4_vol1', label: '四年级上册' },
									{ value: 'grade4_vol2', label: '四年级下册' },
									{ value: 'grade5_vol1', label: '五年级上册' },
									{ value: 'grade5_vol2', label: '五年级下册' },
									{ value: 'grade6_vol1', label: '六年级上册' },
									{ value: 'grade6_vol2', label: '六年级下册' }
								],
								default_value: 'grade1_vol1'
							},
							{
								type: 'text',
								name: 'topic',
								label: '课题',
								required: true,
								placeholder: '请输入具体的课题名称，如：分数的初步认识',
								max_length: 50
							},
							{
								type: 'select',
								name: 'hours',
								label: '总课时',
								required: true,
								options: [
									{ value: '1', label: '1课时' },
									{ value: '2', label: '2课时' },
									{ value: '3', label: '3课时' },
									{ value: '4', label: '4课时' },
									{ value: '5', label: '5课时' }
								],
								default_value: '1'
							},
							{
								type: 'file',
								name: 'template',
								label: '教案模板文件（可选）',
								required: false,
								allowed_types: ['.docx', '.doc', '.pdf'],
								max_size: '5MB'
							},
							{
								type: 'file',
								name: 'references',
								label: '教案参考资料（可选）',
								required: false,
								allowed_types: ['.docx', '.doc', '.pdf', '.pptx', '.ppt', '.txt'],
								max_size: '50MB',
								multiple: true
							}
						]
					}
				}
			};

			const mockApp = mockApps[appId];
			if (mockApp) {
				app = mockApp;
				isFavorited = ['app-2'].includes(appId); // 模拟app-2被收藏

				// 初始化表单默认值
				initializeFormData();
			} else {
				toast.error('应用不存在或已被删除');
				goto('/agents');
			}
		} catch (error) {
			console.error('Failed to load app:', error);
			toast.error('加载应用失败');
			goto('/agents');
		} finally {
			loading = false;
		}
	};

	const initializeFormData = () => {
		if (!app || !app.form_config) return;

		const data = {};
		app.form_config.fields?.forEach((field) => {
			if (field.default_value !== undefined) {
				data[field.name] = field.default_value;
			} else {
				// 设置默认值
				switch (field.type) {
					case 'text':
					case 'textarea':
						data[field.name] = '';
						break;
					case 'number':
						data[field.name] = field.min || 0;
						break;
					case 'checkbox':
						data[field.name] = [];
						break;
					case 'switch':
						data[field.name] = false;
						break;
					case 'select':
					case 'radio':
						data[field.name] = field.options?.[0]?.value || '';
						break;
					case 'file':
						data[field.name] = null;
						break;
					case 'date':
						data[field.name] = '';
						break;
				}
			}
		});

		formData = data;
		formErrors = {};
	};

	// 历史记录管理函数
	const loadHistory = async () => {
		try {
			const storageKey = `agent_history_${appId}_${$user?.id || 'anonymous'}`;
			const savedHistory = localStorage.getItem(storageKey);
			if (savedHistory) {
				history = JSON.parse(savedHistory);
				// 按时间倒序排列，最新的在前面
				history.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
			}
		} catch (error) {
			console.warn('Failed to load history:', error);
			history = [];
		}
	};

	const saveHistoryItem = async (historyItem) => {
		try {
			const storageKey = `agent_history_${appId}_${$user?.id || 'anonymous'}`;

			// 添加到历史记录
			history = [historyItem, ...history];

			// 限制历史记录数量（保留最近50条）
			if (history.length > 50) {
				history = history.slice(0, 50);
			}

			// 保存到localStorage
			localStorage.setItem(storageKey, JSON.stringify(history));
		} catch (error) {
			console.warn('Failed to save history item:', error);
		}
	};

	const deleteHistoryItem = async (itemId) => {
		try {
			const storageKey = `agent_history_${appId}_${$user?.id || 'anonymous'}`;
			history = history.filter((item) => item.id !== itemId);
			localStorage.setItem(storageKey, JSON.stringify(history));

			// 如果当前选中的历史记录被删除，清除选择
			if (selectedHistoryItem?.id === itemId) {
				selectedHistoryItem = null;
			}

			toast.success('历史记录已删除');
		} catch (error) {
			console.warn('Failed to delete history item:', error);
			toast.error('删除失败');
		}
	};

	const clearHistory = async () => {
		try {
			const storageKey = `agent_history_${appId}_${$user?.id || 'anonymous'}`;
			history = [];
			selectedHistoryItem = null;
			localStorage.removeItem(storageKey);
			toast.success('历史记录已清空');
		} catch (error) {
			console.warn('Failed to clear history:', error);
			toast.error('清空失败');
		}
	};

	const viewHistoryItem = (item) => {
		selectedHistoryItem = item;
		showHistory = false;
		showResponse = true;
		streamingResponse = item.ai_response;

		// 创建一个模拟的submission对象来显示历史记录
		submission = {
			submission_id: item.submission_id,
			status: 'completed',
			ai_response: item.ai_response,
			model_used: item.model_used,
			cost_consumed: item.cost_consumed,
			created_at: new Date(item.created_at).getTime(),
			form_data: item.form_data
		};
	};

	const handleFormSubmit = async (event) => {
		event.preventDefault();

		if (!validateForm()) {
			toast.error('请检查表单填写');
			return;
		}

		submitting = true;
		isStreaming = false;
		streamingResponse = '';

		try {
			// 创建处理中的提交记录
			const processingSubmission = {
				submission_id: 'sub_' + Date.now(),
				status: 'processing',
				created_at: Date.now(),
				form_data: formData
			};

			submission = processingSubmission;
			showResponse = true;
			toast.success('表单已提交，正在处理中...');

			// 调用真实的AI API (流式响应)
			const result = await executeAgent($user?.token || '', appId, formData);

			if (result.success && result.stream) {
				// 开始流式处理
				isStreaming = true;
				streamController = result.controller;

				// 更新提交状态为流式处理中
				submission = {
					...processingSubmission,
					status: 'streaming',
					model_used: result.model,
					started_at: Date.now()
				};

				// 处理流式响应
				await handleStreamResponse(result.stream, result.model);
			} else if (result.success && result.data) {
				// 非流式响应（fallback情况）
				submission = {
					...processingSubmission,
					status: 'completed',
					ai_response: result.data.response,
					model_used: result.data.model,
					usage: result.data.usage,
					completed_at: Date.now(),
					cost_consumed: 120
				};
				streamingResponse = result.data.response;

				// 保存到历史记录
				const historyItem = {
					id: 'hist_' + Date.now(),
					submission_id: submission.submission_id,
					form_data: submission.form_data,
					ai_response: result.data.response,
					model_used: result.data.model,
					cost_consumed: 120,
					created_at: new Date().toISOString(),
					app_name: app?.display_name || '智能体应用'
				};
				await saveHistoryItem(historyItem);

				toast.success('AI处理完成');
			} else {
				// 处理失败
				submission = {
					...processingSubmission,
					status: 'failed',
					error_message: result.error,
					completed_at: Date.now()
				};
				toast.error(result.error || 'AI处理失败');
			}
		} catch (error) {
			console.error('Failed to submit form:', error);

			// 创建失败的提交记录
			submission = {
				submission_id: submission?.submission_id || 'sub_' + Date.now(),
				status: 'failed',
				error_message: error.message || '网络连接失败，请检查您的网络设置',
				created_at: submission?.created_at || Date.now(),
				completed_at: Date.now(),
				form_data: formData
			};

			isStreaming = false;
			toast.error('提交失败：' + (error.message || '请重试'));
		} finally {
			submitting = false;
		}
	};

	// 处理流式响应
	const handleStreamResponse = async (response, model) => {
		const reader = response.body.getReader();
		const decoder = new TextDecoder();
		let buffer = '';

		try {
			while (true) {
				const { done, value } = await reader.read();

				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (line.trim() === '') continue;
					if (line.startsWith('data: ')) {
						const data = line.slice(6);
						if (data.trim() === '[DONE]') {
							// 流结束
							isStreaming = false;
							submission = {
								...submission,
								status: 'completed',
								ai_response: streamingResponse,
								completed_at: Date.now(),
								cost_consumed: 120
							};

							// 保存到历史记录
							const historyItem = {
								id: 'hist_' + Date.now(),
								submission_id: submission.submission_id,
								form_data: submission.form_data,
								ai_response: streamingResponse,
								model_used: submission.model_used,
								cost_consumed: 120,
								created_at: new Date().toISOString(),
								app_name: app?.display_name || '智能体应用'
							};
							await saveHistoryItem(historyItem);

							toast.success('AI处理完成');
							return;
						}

						try {
							const parsed = JSON.parse(data);
							if (parsed.choices && parsed.choices[0]?.delta?.content) {
								streamingResponse += parsed.choices[0].delta.content;
								// 触发响应式更新
								streamingResponse = streamingResponse;
							}
						} catch (e) {
							console.warn('Failed to parse streaming data:', data);
						}
					}
				}
			}
		} catch (error) {
			console.error('Streaming error:', error);
			isStreaming = false;
			submission = {
				...submission,
				status: 'failed',
				error_message: '流式传输中断：' + error.message,
				completed_at: Date.now()
			};
			toast.error('AI响应中断，请重试');
		} finally {
			reader.releaseLock();
		}
	};

	const validateForm = () => {
		if (!app || !app.form_config) return false;

		const errors = {};
		let hasErrors = false;

		app.form_config.fields?.forEach((field) => {
			if (field.required) {
				const value = formData[field.name];
				if (!value || (Array.isArray(value) && value.length === 0)) {
					errors[field.name] = '此字段为必填项';
					hasErrors = true;
				}
			}
		});

		formErrors = errors;
		return !hasErrors;
	};

	const pollForResponse = async (submissionId) => {
		const maxAttempts = 60; // 最多轮询60次 (5分钟)
		let attempts = 0;

		const poll = async () => {
			if (attempts >= maxAttempts) {
				toast.error('处理超时，请稍后查看结果');
				return;
			}

			try {
				const response = await fetch(`/api/v1/agents/submissions/${submissionId}`, {
					headers: {
						Authorization: `Bearer ${localStorage.token}`
					}
				});

				if (response.ok) {
					const result = await response.json();

					if (result.status === 'completed') {
						submission = result;
						toast.success('处理完成');
						return;
					} else if (result.status === 'failed') {
						toast.error('处理失败：' + (result.error_message || '未知错误'));
						return;
					}
				}

				attempts++;
				setTimeout(poll, 5000); // 5秒后重试
			} catch (error) {
				attempts++;
				setTimeout(poll, 5000);
			}
		};

		setTimeout(poll, 2000); // 2秒后开始轮询
	};

	const handleToggleFavorite = async () => {
		try {
			// 模拟切换收藏状态
			if (isFavorited) {
				isFavorited = false;
				app.favorite_count = Math.max((app.favorite_count || 0) - 1, 0);
				toast.success('已移除收藏');
			} else {
				isFavorited = true;
				app.favorite_count = (app.favorite_count || 0) + 1;
				toast.success('已添加到收藏');
			}

			// 触发响应式更新
			app = app;
		} catch (error) {
			console.error('Failed to toggle favorite:', error);
			toast.error('收藏状态更新失败');
		}
	};

	const handleReset = () => {
		// 如果正在流式传输，取消它
		if (isStreaming && streamController) {
			streamController.abort();
		}

		initializeFormData();
		formErrors = {};
		showResponse = false;
		submission = null;
		streamingResponse = '';
		isStreaming = false;
		streamController = null;
	};

	const handleNewSubmission = () => {
		// 如果正在流式传输，取消它
		if (isStreaming && streamController) {
			streamController.abort();
		}

		showResponse = false;
		showHistory = false;
		submission = null;
		selectedHistoryItem = null;
		formErrors = {};
		streamingResponse = '';
		isStreaming = false;
		streamController = null;
	};

	const handleStopGeneration = () => {
		if (isStreaming && streamController) {
			streamController.abort();
			isStreaming = false;
			submission = {
				...submission,
				status: 'cancelled',
				ai_response: streamingResponse,
				completed_at: Date.now()
			};
			toast.info('AI生成已停止');
		}
	};

	const formatCreatedTime = (timestamp) => {
		try {
			const date = new Date(timestamp);
			const now = new Date();
			const diffInMs = now - date;
			const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

			if (diffInDays === 0) return '今天创建';
			if (diffInDays === 1) return '昨天创建';
			if (diffInDays < 7) return `${diffInDays}天前创建`;
			if (diffInDays < 30) return `${Math.floor(diffInDays / 7)}周前创建`;
			return `${Math.floor(diffInDays / 30)}个月前创建`;
		} catch {
			return '';
		}
	};

	// 获取分类显示信息
	const getCategoryInfo = (category) => {
		const categoryMap = {
			general: { name: '通用', color: '#6b7280', bg: '#f3f4f6' },
			productivity: { name: '效率', color: '#059669', bg: '#d1fae5' },
			creative: { name: '创意', color: '#dc2626', bg: '#fee2e2' },
			analysis: { name: '分析', color: '#2563eb', bg: '#dbeafe' }
		};
		return categoryMap[category] || { name: category, color: '#6b7280', bg: '#f3f4f6' };
	};

	// 获取字段友好标签
	const getFieldLabel = (fieldKey) => {
		const labelMap = {
			subject: '学科',
			stage: '阶段',
			textbook: '教材',
			volume: '册别',
			topic: '课题',
			hours: '课时',
			template: '模板文件',
			references: '参考资料',
			writing_type: '写作类型',
			theme: '主题',
			style: '风格',
			word_count: '字数',
			summary_length: '总结长度',
			focus_areas: '重点领域',
			analysis_type: '分析类型',
			output_formats: '输出格式',
			document: '文档',
			data_file: '数据文件'
		};
		return labelMap[fieldKey] || fieldKey;
	};

	$: categoryInfo = app ? getCategoryInfo(app.category) : null;
</script>

<div class="fixed inset-0 z-50 bg-white dark:bg-gray-950 overflow-y-auto">
	{#if loading}
		<div class="flex flex-col items-center justify-center min-h-[50vh] gap-4">
			<Spinner />
			<p class="text-gray-600 dark:text-gray-400">加载中...</p>
		</div>
	{:else if app}
		<!-- 应用头部信息 -->
		<div
			class="bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10"
		>
			<div class="max-w-4xl mx-auto p-6">
				<div class="flex flex-col lg:flex-row items-start lg:items-center gap-6">
					<div class="flex items-center gap-4 flex-1">
						<button
							class="flex items-center gap-2 px-3 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
							on:click={() => window.history.back()}
							title="返回"
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M15 19l-7-7 7-7"
								/>
							</svg>
							<span class="hidden sm:inline">返回</span>
						</button>
						<div
							class="w-16 h-16 text-4xl flex items-center justify-center bg-gray-100 dark:bg-gray-800 rounded-xl"
						>
							{app.icon || '🤖'}
						</div>
						<div class="flex-1 min-w-0">
							<h1 class="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mb-2">
								{app.display_name}
							</h1>
							<div class="flex flex-wrap items-center gap-3 mb-2">
								{#if categoryInfo}
									<span
										class="px-3 py-1 text-sm font-medium rounded-full"
										style="color: {categoryInfo.color}; background-color: {categoryInfo.bg};"
									>
										{categoryInfo.name}
									</span>
								{/if}
								<span class="text-sm text-gray-500 dark:text-gray-400">
									{formatCreatedTime(app.created_at)}
								</span>
							</div>
							<div
								class="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400"
							>
								<span class="flex items-center gap-1">
									<span>👥</span>
									{app.usage_count || 0} 次使用
								</span>
								<span class="flex items-center gap-1">
									<span>⭐</span>
									{app.favorite_count || 0} 收藏
								</span>
								{#if app.cost_per_use}
									<span class="flex items-center gap-1 text-green-600">
										<span>💰</span>
										{app.cost_per_use} 积分/次
									</span>
								{/if}
							</div>
						</div>
					</div>

					<div class="flex items-center gap-3">
						<button
							class="p-3 rounded-full transition-colors {isFavorited
								? 'bg-red-50 hover:bg-red-100 text-red-600'
								: 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'}"
							on:click={handleToggleFavorite}
							title={isFavorited ? '取消收藏' : '收藏'}
						>
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none">
								<path
									d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
									fill={isFavorited ? 'currentColor' : 'none'}
									stroke="currentColor"
									stroke-width="2"
								/>
							</svg>
						</button>

						<button
							class="p-3 rounded-full transition-colors relative {showHistory
								? 'bg-blue-50 hover:bg-blue-100 text-blue-600'
								: 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'}"
							title="生成历史"
							on:click={() => (showHistory = !showHistory)}
						>
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none">
								<path
									d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
								/>
							</svg>
							{#if history.length > 0}
								<span
									class="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center"
								>
									{history.length > 99 ? '99+' : history.length}
								</span>
							{/if}
						</button>

						<button
							class="p-3 rounded-full bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
							title="分享"
						>
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none">
								<path
									d="M18 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2c0 .18.02.36.07.53L10.9 9.81C10.44 9.31 9.78 9 9 9c-1.1 0-2 .9-2 2s.9 2 2 2c.78 0 1.44-.31 1.9-.81l5.17 3.28c-.05.17-.07.35-.07.53 0 1.1.9 2 2 2s2-.9 2-2-.9-2-2-2c-.78 0-1.44.31-1.9.81l-5.17-3.28C16.02 11.36 16 11.18 16 11s-.02-.36-.07-.53l5.17-3.28C21.56 7.69 22.22 8 23 8z"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
								/>
							</svg>
						</button>
					</div>
				</div>
			</div>
		</div>

		<!-- 主要内容区域 -->
		<div class="max-w-4xl mx-auto p-6">
			<!-- 应用描述 -->
			{#if app.description}
				<div
					class="bg-white dark:bg-gray-900 rounded-xl p-6 mb-6 border border-gray-200 dark:border-gray-700"
				>
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">应用介绍</h2>
					<p class="text-gray-700 dark:text-gray-300 leading-relaxed">{app.description}</p>
					{#if app.detailed_description}
						<p class="text-gray-600 dark:text-gray-400 mt-3 leading-relaxed">
							{app.detailed_description}
						</p>
					{/if}
				</div>
			{/if}

			{#if showHistory}
				<!-- 历史记录区域 -->
				<div
					class="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-700"
				>
					<div class="flex items-center justify-between mb-6">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">生成历史</h2>
						<div class="flex items-center gap-2">
							{#if history.length > 0}
								<button
									class="px-4 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
									on:click={clearHistory}
								>
									清空历史
								</button>
							{/if}
							<button
								class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
								on:click={() => (showHistory = false)}
							>
								关闭
							</button>
						</div>
					</div>

					{#if history.length === 0}
						<div class="text-center py-12">
							<div class="text-4xl mb-4">📜</div>
							<p class="text-gray-500 dark:text-gray-400">暂无生成历史</p>
							<p class="text-sm text-gray-400 dark:text-gray-500 mt-2">
								使用智能体生成内容后，历史记录将显示在这里
							</p>
						</div>
					{:else}
						<div class="space-y-4 max-h-96 overflow-y-auto">
							{#each history as item (item.id)}
								<div
									class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
								>
									<div class="flex items-start justify-between gap-4">
										<div class="flex-1 min-w-0">
											<div class="flex items-center gap-2 mb-2">
												<span class="text-sm font-medium text-gray-900 dark:text-white">
													{new Date(item.created_at).toLocaleDateString('zh-CN', {
														year: 'numeric',
														month: 'short',
														day: 'numeric',
														hour: '2-digit',
														minute: '2-digit'
													})}
												</span>
												{#if item.model_used}
													<span
														class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full"
													>
														{item.model_used}
													</span>
												{/if}
												{#if item.cost_consumed}
													<span
														class="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded-full"
													>
														{item.cost_consumed} 积分
													</span>
												{/if}
											</div>
											<div class="text-sm text-gray-600 dark:text-gray-400 mb-3">
												{#if item.form_data}
													{#each Object.entries(item.form_data) as [key, value]}
														{#if value && value !== '' && key !== 'template' && key !== 'references'}
															<span class="inline-block mr-4 mb-1">
																<strong class="text-gray-700 dark:text-gray-300"
																	>{getFieldLabel(key)}:</strong
																>
																<span class="ml-1"
																	>{Array.isArray(value)
																		? value.join(', ')
																		: String(value).slice(0, 30)}{String(value).length > 30
																		? '...'
																		: ''}</span
																>
															</span>
														{/if}
													{/each}
													{#if item.form_data.template}
														<span class="inline-block mr-4 mb-1">
															<strong class="text-gray-700 dark:text-gray-300">模板文件:</strong>
															<span class="ml-1 text-blue-600">已上传</span>
														</span>
													{/if}
													{#if item.form_data.references}
														<span class="inline-block mr-4 mb-1">
															<strong class="text-gray-700 dark:text-gray-300">参考资料:</strong>
															<span class="ml-1 text-blue-600">已上传</span>
														</span>
													{/if}
												{/if}
											</div>
											<div class="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
												{item.ai_response.slice(0, 150)}{item.ai_response.length > 150 ? '...' : ''}
											</div>
										</div>
										<div class="flex items-center gap-2">
											<button
												class="px-3 py-1 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
												on:click={() => viewHistoryItem(item)}
											>
												查看
											</button>
											<button
												class="px-3 py-1 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
												on:click={() => deleteHistoryItem(item.id)}
											>
												删除
											</button>
										</div>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{:else if !showResponse}
				<!-- 表单区域 -->
				<div
					class="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-700"
				>
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">填写信息</h2>
					<form on:submit={handleFormSubmit} class="space-y-6">
						<FormRenderer
							config={app.form_config}
							bind:data={formData}
							bind:errors={formErrors}
							readonly={submitting}
						/>

						<div
							class="flex flex-col sm:flex-row gap-3 pt-6 border-t border-gray-200 dark:border-gray-700"
						>
							<button
								type="button"
								class="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
								on:click={handleReset}
								disabled={submitting}
							>
								重置
							</button>
							<button
								type="submit"
								class="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 flex-1"
								disabled={submitting}
							>
								{#if submitting}
									<Spinner className="w-4 h-4" />
									提交中...
								{:else}
									提交
								{/if}
							</button>
						</div>
					</form>
				</div>
			{:else}
				<!-- 响应结果区域 -->
				<div
					class="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-700"
				>
					<div
						class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6"
					>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
							{selectedHistoryItem ? '历史记录详情' : 'AI 响应结果'}
						</h2>
						<div class="flex items-center gap-2">
							{#if selectedHistoryItem}
								<button
									class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
									on:click={() => {
										selectedHistoryItem = null;
										showHistory = true;
										showResponse = false;
									}}
								>
									返回历史
								</button>
								<button
									class="px-4 py-2 border border-red-300 dark:border-red-600 text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 rounded-lg transition-colors"
									on:click={() => deleteHistoryItem(selectedHistoryItem.id)}
								>
									删除此记录
								</button>
							{:else if isStreaming}
								<button
									class="px-4 py-2 border border-red-300 dark:border-red-600 text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 rounded-lg transition-colors"
									on:click={handleStopGeneration}
								>
									停止生成
								</button>
							{:else}
								<button
									class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
									on:click={handleNewSubmission}
								>
									重新提交
								</button>
							{/if}
						</div>
					</div>

					{#if submission}
						<div class="space-y-4">
							{#if submission.status === 'processing'}
								<div class="flex flex-col items-center justify-center py-12 text-center">
									<Spinner className="mb-4" />
									<p class="text-gray-600 dark:text-gray-400">正在处理中，请稍候...</p>
								</div>
							{:else if submission.status === 'streaming' || isStreaming}
								<div
									class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6"
								>
									<div class="flex items-center gap-2 mb-4">
										<Spinner className="w-4 h-4" />
										<span class="text-sm text-blue-700 dark:text-blue-300">AI正在生成中...</span>
									</div>
									<div class="prose dark:prose-invert max-w-none">
										{@html marked(streamingResponse || '')}
									</div>
									{#if streamingResponse && streamingResponse.endsWith('|')}
										<div class="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1"></div>
									{/if}
								</div>
							{:else if submission.status === 'completed'}
								<div
									class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6"
								>
									<div class="prose dark:prose-invert max-w-none">
										{@html marked(submission.ai_response || streamingResponse || '')}
									</div>
									{#if submission.cost_consumed}
										<div class="mt-4 pt-4 border-t border-green-200 dark:border-green-800">
											<span
												class="inline-flex items-center gap-2 text-sm text-green-700 dark:text-green-300"
											>
												<span>💰</span>
												消耗 {submission.cost_consumed} 积分
											</span>
										</div>
									{/if}
								</div>
							{:else if submission.status === 'cancelled'}
								<div
									class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6"
								>
									<div class="flex items-center gap-2 mb-4">
										<span class="text-2xl">⚠️</span>
										<span class="font-medium text-yellow-800 dark:text-yellow-200">生成已停止</span>
									</div>
									<div class="prose dark:prose-invert max-w-none">
										{@html marked(streamingResponse || '生成被用户停止')}
									</div>
								</div>
							{:else if submission.status === 'failed'}
								<div
									class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center"
								>
									<div class="text-4xl mb-4">❌</div>
									<p class="text-red-800 dark:text-red-200">
										处理失败: {submission.error_message || '未知错误'}
									</p>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{:else}
		<div class="flex flex-col items-center justify-center min-h-[60vh] gap-4 text-center p-6">
			<div class="text-6xl mb-4">🚫</div>
			<h2 class="text-2xl font-bold text-gray-900 dark:text-white">应用不存在</h2>
			<p class="text-gray-600 dark:text-gray-400 mb-6">请检查应用链接是否正确</p>
			<button
				class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
				on:click={() => goto('/agents')}
			>
				返回广场
			</button>
		</div>
	{/if}
</div>

<style>
	/* Markdown渲染样式 */
	:global(.prose) {
		color: inherit;
		max-width: none;
	}

	:global(.prose h1, .prose h2, .prose h3, .prose h4, .prose h5, .prose h6) {
		color: inherit;
		margin-top: 1.5rem;
		margin-bottom: 0.75rem;
		font-weight: 600;
	}

	:global(.prose h1) {
		font-size: 1.5rem;
	}
	:global(.prose h2) {
		font-size: 1.3rem;
	}
	:global(.prose h3) {
		font-size: 1.1rem;
	}

	:global(.prose p) {
		margin-bottom: 1rem;
		line-height: 1.6;
	}

	:global(.prose ul, .prose ol) {
		margin: 1rem 0;
		padding-left: 1.5rem;
	}

	:global(.prose li) {
		margin: 0.5rem 0;
	}

	:global(.prose strong) {
		font-weight: 600;
		color: inherit;
	}

	:global(.prose em) {
		font-style: italic;
		color: inherit;
	}

	:global(.prose code) {
		background: rgba(156, 163, 175, 0.1);
		padding: 0.2rem 0.4rem;
		border-radius: 0.25rem;
		font-size: 0.875rem;
		font-family:
			ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'DejaVu Sans Mono',
			monospace;
	}

	:global(.prose pre) {
		background: rgba(156, 163, 175, 0.1);
		padding: 1rem;
		border-radius: 0.5rem;
		overflow-x: auto;
		margin: 1rem 0;
	}

	:global(.prose pre code) {
		background: none;
		padding: 0;
	}

	:global(.prose blockquote) {
		border-left: 4px solid rgba(156, 163, 175, 0.3);
		padding-left: 1rem;
		margin: 1rem 0;
		font-style: italic;
		color: rgba(156, 163, 175, 0.8);
	}

	:global(.prose table) {
		width: 100%;
		border-collapse: collapse;
		margin: 1rem 0;
	}

	:global(.prose th, .prose td) {
		border: 1px solid rgba(156, 163, 175, 0.3);
		padding: 0.5rem;
		text-align: left;
	}

	:global(.prose th) {
		background: rgba(156, 163, 175, 0.1);
		font-weight: 600;
	}

	/* Dark mode adjustments */
	:global(.dark .prose code) {
		background: rgba(75, 85, 99, 0.3);
	}

	:global(.dark .prose pre) {
		background: rgba(75, 85, 99, 0.3);
	}

	:global(.dark .prose th, .dark .prose td) {
		border-color: rgba(75, 85, 99, 0.5);
	}

	:global(.dark .prose th) {
		background: rgba(75, 85, 99, 0.3);
	}

	/* 历史记录列表样式 */
	.line-clamp-3 {
		overflow: hidden;
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 3;
		line-clamp: 3;
	}
</style>
