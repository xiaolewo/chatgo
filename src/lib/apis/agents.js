/**
 * Agent Marketplace API Functions
 * 智能体广场API接口
 */

import { WEBUI_BASE_URL } from '$lib/constants.ts';

const API_BASE_URL = '/api/v1/agents';

// 错误处理工具函数
const handleApiError = async (response) => {
	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
		throw new Error(error.detail || `HTTP ${response.status}`);
	}
	return response.json();
};

// 构建请求头
const getHeaders = (token) => ({
	'Content-Type': 'application/json',
	Authorization: `Bearer ${token}`
});

// 获取智能体应用列表
export const getAgentApps = async (token, params = {}) => {
	const queryParams = new URLSearchParams();

	if (params.category) queryParams.append('category', params.category);
	if (params.search) queryParams.append('search', params.search);
	if (params.page) queryParams.append('page', params.page);
	if (params.limit) queryParams.append('limit', params.limit);
	if (params.status) queryParams.append('status', params.status);

	const response = await fetch(`${API_BASE_URL}?${queryParams}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 根据ID获取智能体应用详情
export const getAgentAppById = async (token, appId) => {
	const response = await fetch(`${API_BASE_URL}/${appId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 创建智能体应用（管理员）
export const createAgentApp = async (token, appData) => {
	const response = await fetch(API_BASE_URL, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(appData)
	});

	return handleApiError(response);
};

// 更新智能体应用（管理员）
export const updateAgentApp = async (token, appId, appData) => {
	const response = await fetch(`${API_BASE_URL}/${appId}`, {
		method: 'PUT',
		headers: getHeaders(token),
		body: JSON.stringify(appData)
	});

	return handleApiError(response);
};

// 删除智能体应用（管理员）
export const deleteAgentApp = async (token, appId) => {
	const response = await fetch(`${API_BASE_URL}/${appId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 提交表单到智能体应用
export const submitAgentForm = async (token, appId, formData, files = null) => {
	const formDataObj = new FormData();
	formDataObj.append('form_data', JSON.stringify(formData));

	if (files && files.length > 0) {
		files.forEach((file, index) => {
			formDataObj.append(`files`, file);
		});
	}

	const response = await fetch(`${API_BASE_URL}/${appId}/submit`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
			// 不设置Content-Type，让浏览器自动设置multipart/form-data
		},
		body: formDataObj
	});

	return handleApiError(response);
};

// 获取应用统计信息
export const getAgentAppStats = async (token, appId) => {
	const response = await fetch(`${API_BASE_URL}/${appId}/stats`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 切换收藏状态
export const toggleFavoriteApp = async (token, appId) => {
	const response = await fetch(`${API_BASE_URL}/${appId}/favorite`, {
		method: 'POST',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 获取用户收藏的应用
export const getUserFavoriteApps = async (token) => {
	const response = await fetch(`${API_BASE_URL}/favorites`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 获取分类列表
export const getAppCategories = async (token) => {
	const response = await fetch(`${API_BASE_URL}/categories`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 创建分类（管理员）
export const createAppCategory = async (token, categoryData) => {
	const response = await fetch(`${API_BASE_URL}/categories`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(categoryData)
	});

	return handleApiError(response);
};

// 更新分类（管理员）
export const updateAppCategory = async (token, categoryId, categoryData) => {
	const response = await fetch(`${API_BASE_URL}/categories/${categoryId}`, {
		method: 'PUT',
		headers: getHeaders(token),
		body: JSON.stringify(categoryData)
	});

	return handleApiError(response);
};

// 删除分类（管理员）
export const deleteAppCategory = async (token, categoryId) => {
	const response = await fetch(`${API_BASE_URL}/categories/${categoryId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 获取提交记录列表
export const getSubmissions = async (token, params = {}) => {
	const queryParams = new URLSearchParams();

	if (params.app_id) queryParams.append('app_id', params.app_id);
	if (params.user_id) queryParams.append('user_id', params.user_id);
	if (params.status) queryParams.append('status', params.status);
	if (params.page) queryParams.append('page', params.page);
	if (params.limit) queryParams.append('limit', params.limit);

	const response = await fetch(`${API_BASE_URL}/submissions?${queryParams}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 根据ID获取提交记录详情
export const getSubmissionById = async (token, submissionId) => {
	const response = await fetch(`${API_BASE_URL}/submissions/${submissionId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 删除提交记录
export const deleteSubmission = async (token, submissionId) => {
	const response = await fetch(`${API_BASE_URL}/submissions/${submissionId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 获取应用模板列表
export const getAppTemplates = async (token, params = {}) => {
	const queryParams = new URLSearchParams();

	if (params.category) queryParams.append('category', params.category);
	if (params.search) queryParams.append('search', params.search);
	if (params.public_only) queryParams.append('public_only', params.public_only);
	if (params.page) queryParams.append('page', params.page);
	if (params.limit) queryParams.append('limit', params.limit);

	const response = await fetch(`${API_BASE_URL}/templates?${queryParams}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 根据ID获取应用模板详情
export const getAppTemplateById = async (token, templateId) => {
	const response = await fetch(`${API_BASE_URL}/templates/${templateId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 创建应用模板
export const createAppTemplate = async (token, templateData) => {
	const response = await fetch(`${API_BASE_URL}/templates`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(templateData)
	});

	return handleApiError(response);
};

// 使用模板创建应用
export const createAppFromTemplate = async (token, templateId, appData) => {
	const response = await fetch(`${API_BASE_URL}/templates/${templateId}/use`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(appData)
	});

	return handleApiError(response);
};

// 上传文件
export const uploadFile = async (token, file, category = 'agent_files') => {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('category', category);

	const response = await fetch('/api/v1/files/upload', {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
		},
		body: formData
	});

	return handleApiError(response);
};

// 批量上传文件
export const uploadFiles = async (token, files, category = 'agent_files') => {
	const formData = new FormData();

	files.forEach((file, index) => {
		formData.append(`files`, file);
	});
	formData.append('category', category);

	const response = await fetch('/api/v1/files/upload/batch', {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
		},
		body: formData
	});

	return handleApiError(response);
};

// 删除文件
export const deleteFile = async (token, fileId) => {
	const response = await fetch(`/api/v1/files/${fileId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 验证表单数据
export const validateFormData = async (token, appId, formData) => {
	const response = await fetch(`${API_BASE_URL}/${appId}/validate`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify({ form_data: formData })
	});

	return handleApiError(response);
};

// 执行智能体 - 调用真实AI API
export const executeAgent = async (token, appId, formData) => {
	try {
		// 导入所需的API函数
		const { chatCompletion } = await import('./openai/index.ts');
		const { getModels } = await import('./models/index.ts');

		// 获取系统可用模型
		let availableModels = [];
		try {
			const modelsResponse = await getModels(token);
			availableModels = modelsResponse?.data || modelsResponse || [];
			console.log('Available models:', availableModels);
		} catch (error) {
			console.warn('Failed to fetch models:', error);
		}

		// 选择可用的模型（优先选择GPT系列，其次选择第一个可用模型）
		const getAvailableModel = () => {
			if (!availableModels.length) {
				console.warn('No models available, using fallback response');
				return null; // 使用null标记没有可用模型
			}

			// 优先选择GPT-4相关模型
			let preferredModel = availableModels.find(
				(m) => m.id.toLowerCase().includes('gpt-4') || m.name?.toLowerCase().includes('gpt-4')
			);

			// 如果没有GPT-4，选择GPT-3.5相关模型
			if (!preferredModel) {
				preferredModel = availableModels.find(
					(m) =>
						m.id.toLowerCase().includes('gpt-3.5') ||
						m.id.toLowerCase().includes('gpt3.5') ||
						m.name?.toLowerCase().includes('gpt-3.5')
				);
			}

			// 如果都没有，选择第一个可用模型
			if (!preferredModel) {
				preferredModel = availableModels[0];
			}

			return preferredModel.id || preferredModel.name || preferredModel;
		};

		// 获取智能体配置
		const selectedModel = getAvailableModel();
		console.log('Selected model for agent:', selectedModel);

		// 如果没有可用模型，返回友好的提示消息
		if (!selectedModel) {
			const fallbackResponses = {
				'app-1':
					'抱歉，当前系统尚未配置AI模型。请联系系统管理员在OpenWebUI管理界面中配置OpenAI或其他AI模型后再试。\n\n配置步骤：\n1. 进入管理员设置\n2. 配置OpenAI API或其他AI服务\n3. 确认模型可用后重新尝试',
				'app-2':
					'抱歉，创意写作功能需要AI模型支持。请联系系统管理员配置AI模型。\n\n建议配置GPT-4或其他大语言模型以获得最佳创作效果。',
				'app-3': '抱歉，数据分析功能需要AI模型支持。请联系系统管理员在系统中配置相应的AI模型。',
				'app-4':
					'抱歉，教案生成功能需要AI模型支持。请联系系统管理员配置AI模型。\n\n推荐使用GPT-4或Claude等高性能模型以确保教案质量。'
			};

			return {
				success: true,
				data: {
					response: fallbackResponses[appId] || '系统尚未配置AI模型，请联系管理员配置后使用。',
					model: '系统提示',
					usage: {},
					created_at: new Date().toISOString()
				}
			};
		}

		const agentConfigs = {
			'app-1': {
				model: selectedModel,
				system_prompt:
					'你是一个专业的文档总结助手，擅长快速提取文档的关键信息。请根据用户上传的文档内容，提供准确、简洁的总结。',
				temperature: 0.7,
				max_tokens: 2000
			},
			'app-2': {
				model: selectedModel,
				system_prompt:
					'你是一个富有创意的写作助手，能够根据用户的要求创作小说、诗歌等文学作品。请发挥想象力，创作优美、生动的内容。',
				temperature: 0.8,
				max_tokens: 3000
			},
			'app-3': {
				model: selectedModel,
				system_prompt:
					'你是一个专业的数据分析师，能够分析数据趋势并生成深度分析报告。请提供准确、专业的数据分析结果。',
				temperature: 0.3,
				max_tokens: 4000
			},
			'app-4': {
				model: selectedModel,
				system_prompt: `你是一位资深的教育专家和教案设计师，拥有丰富的教学经验和深厚的学科知识。

任务职责：
1. 根据用户提供的学科、阶段、教材、册别、课题和课时信息，生成专业的教案
2. 结合教育教学理论，设计符合学生认知规律的教学活动
3. 提供清晰的教学目标、重点难点、教学过程和教学反思

教案结构要求：
一、教学目标
- 知识与技能目标
- 过程与方法目标  
- 情感态度价值观目标

二、教学重点难点
- 教学重点：[具体列出]
- 教学难点：[具体列出]

三、教学准备
- 教师准备：[教具、课件等]
- 学生准备：[学具、预习等]

四、教学过程
- 导入环节（5-10分钟）
- 新课讲授（20-30分钟）
- 练习巩固（10-15分钟）
- 小结作业（5分钟）

五、板书设计
[简洁明了的板书布局]

六、教学反思
[预设可能的问题和改进方向]

设计原则：
- 符合课程标准要求
- 体现学科核心素养
- 适应学生年龄特点
- 注重启发式教学
- 关注个体差异
- 融入现代教学技术

如果用户上传了模板文件或参考资料，请仔细分析并结合这些材料进行教案设计。`,
				temperature: 0.3,
				max_tokens: 4000
			}
		};

		const config = agentConfigs[appId];
		if (!config) {
			throw new Error('智能体配置不存在');
		}

		// 构建用户输入消息
		let userMessage = '请根据以下信息生成内容：\n\n';

		// 根据不同智能体构建不同的消息格式
		if (appId === 'app-4') {
			// 教案生成助手
			const subjectLabels = {
				chinese: '语文',
				math: '数学',
				english: '英语'
			};
			const stageLabels = {
				primary: '小学',
				middle: '初中',
				high: '高中'
			};
			const textbookLabels = {
				renjiao: '人教版',
				sujiao: '苏教版',
				beijing_normal: '北师大版',
				xishi: '西师版'
			};

			userMessage += `学科：${subjectLabels[formData.subject] || formData.subject}\n`;
			userMessage += `阶段：${stageLabels[formData.stage] || formData.stage}\n`;
			userMessage += `教材：${textbookLabels[formData.textbook] || formData.textbook}\n`;
			userMessage += `册别：${formData.volume}\n`;
			userMessage += `课题：${formData.topic}\n`;
			userMessage += `总课时：${formData.hours}课时\n`;

			if (formData.template) {
				userMessage += `\n已上传教案模板文件，请参考模板结构进行设计。\n`;
			}
			if (formData.references) {
				userMessage += `已上传参考资料，请结合参考资料内容进行教案设计。\n`;
			}
		} else {
			// 其他智能体的通用消息构建
			Object.entries(formData).forEach(([key, value]) => {
				if (value && value !== '') {
					userMessage += `${key}: ${value}\n`;
				}
			});
		}

		// 构建聊天消息
		const messages = [
			{
				role: 'system',
				content: config.system_prompt
			},
			{
				role: 'user',
				content: userMessage
			}
		];

		// 构建API请求体
		const requestBody = {
			model: config.model,
			messages: messages,
			temperature: config.temperature,
			max_tokens: config.max_tokens,
			stream: true // 启用流式输出
		};

		// 调用 OpenAI API (使用默认URL) - 流式响应
		const [response, controller] = await chatCompletion(token, requestBody);

		if (!response || !response.ok) {
			let errorMessage = 'AI服务暂时不可用，请稍后重试';
			try {
				const errorData = await response.json();
				console.log('API Error Response:', errorData);
				errorMessage = errorData.error?.message || errorData.detail || errorMessage;
			} catch (e) {
				console.log('Failed to parse error response:', e);
				errorMessage = `HTTP ${response?.status}: ${response?.statusText || 'Unknown error'}`;
			}
			throw new Error(errorMessage);
		}

		// 返回流式响应对象
		return {
			success: true,
			stream: response,
			controller: controller,
			model: config.model,
			created_at: new Date().toISOString()
		};
	} catch (error) {
		console.error('Execute agent error:', error);

		// 返回错误信息
		return {
			success: false,
			error: error.message || '智能体执行失败，请稍后重试'
		};
	}
};

// 预览AI响应（不保存提交记录）
export const previewAgentResponse = async (token, appId, formData, files = null) => {
	const formDataObj = new FormData();
	formDataObj.append('form_data', JSON.stringify(formData));
	formDataObj.append('preview_mode', 'true');

	if (files && files.length > 0) {
		files.forEach((file, index) => {
			formDataObj.append(`files`, file);
		});
	}

	const response = await fetch(`${API_BASE_URL}/${appId}/preview`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
		},
		body: formDataObj
	});

	return handleApiError(response);
};

// 搜索应用
export const searchApps = async (token, query, filters = {}) => {
	const queryParams = new URLSearchParams();
	queryParams.append('q', query);

	if (filters.category) queryParams.append('category', filters.category);
	if (filters.tags) queryParams.append('tags', filters.tags.join(','));
	if (filters.min_rating) queryParams.append('min_rating', filters.min_rating);
	if (filters.sort_by) queryParams.append('sort_by', filters.sort_by);
	if (filters.sort_order) queryParams.append('sort_order', filters.sort_order);
	if (filters.page) queryParams.append('page', filters.page);
	if (filters.limit) queryParams.append('limit', filters.limit);

	const response = await fetch(`${API_BASE_URL}/search?${queryParams}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 获取推荐应用
export const getRecommendedApps = async (token, params = {}) => {
	const queryParams = new URLSearchParams();

	if (params.based_on) queryParams.append('based_on', params.based_on); // usage, favorites, similar
	if (params.limit) queryParams.append('limit', params.limit);
	if (params.exclude) queryParams.append('exclude', params.exclude.join(','));

	const response = await fetch(`${API_BASE_URL}/recommendations?${queryParams}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 获取热门应用
export const getPopularApps = async (token, params = {}) => {
	const queryParams = new URLSearchParams();

	if (params.time_range) queryParams.append('time_range', params.time_range); // day, week, month, all
	if (params.category) queryParams.append('category', params.category);
	if (params.limit) queryParams.append('limit', params.limit);

	const response = await fetch(`${API_BASE_URL}/popular?${queryParams}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 获取用户的使用历史
export const getUserAppHistory = async (token, params = {}) => {
	const queryParams = new URLSearchParams();

	if (params.page) queryParams.append('page', params.page);
	if (params.limit) queryParams.append('limit', params.limit);
	if (params.app_id) queryParams.append('app_id', params.app_id);

	const response = await fetch(`${API_BASE_URL}/history?${queryParams}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 导出应用配置
export const exportAppConfig = async (token, appId) => {
	const response = await fetch(`${API_BASE_URL}/${appId}/export`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	if (!response.ok) {
		throw new Error(`HTTP ${response.status}`);
	}

	return response.blob();
};

// 导入应用配置
export const importAppConfig = async (token, configFile) => {
	const formData = new FormData();
	formData.append('config_file', configFile);

	const response = await fetch(`${API_BASE_URL}/import`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
		},
		body: formData
	});

	return handleApiError(response);
};

// 应用评价相关API
export const rateApp = async (token, appId, rating, comment = '') => {
	const response = await fetch(`${API_BASE_URL}/${appId}/rate`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify({ rating, comment })
	});

	return handleApiError(response);
};

export const getAppRatings = async (token, appId, params = {}) => {
	const queryParams = new URLSearchParams();

	if (params.page) queryParams.append('page', params.page);
	if (params.limit) queryParams.append('limit', params.limit);

	const response = await fetch(`${API_BASE_URL}/${appId}/ratings?${queryParams}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

// 管理员专用API
export const getAdminStats = async (token) => {
	const response = await fetch(`${API_BASE_URL}/admin/stats`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

export const getAdminAppList = async (token, params = {}) => {
	const queryParams = new URLSearchParams();

	if (params.status) queryParams.append('status', params.status);
	if (params.category) queryParams.append('category', params.category);
	if (params.search) queryParams.append('search', params.search);
	if (params.sort_by) queryParams.append('sort_by', params.sort_by);
	if (params.sort_order) queryParams.append('sort_order', params.sort_order);
	if (params.page) queryParams.append('page', params.page);
	if (params.limit) queryParams.append('limit', params.limit);

	const response = await fetch(`${API_BASE_URL}/admin/apps?${queryParams}`, {
		method: 'GET',
		headers: getHeaders(token)
	});

	return handleApiError(response);
};

export const batchUpdateAppStatus = async (token, appIds, status) => {
	const response = await fetch(`${API_BASE_URL}/admin/batch-update`, {
		method: 'PUT',
		headers: getHeaders(token),
		body: JSON.stringify({ app_ids: appIds, status })
	});

	return handleApiError(response);
};

// 工具函数
export const formatFileSize = (bytes) => {
	if (bytes === 0) return '0 B';
	const k = 1024;
	const sizes = ['B', 'KB', 'MB', 'GB'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));
	return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

export const validateFileType = (fileName, allowedTypes) => {
	if (!allowedTypes || allowedTypes.length === 0) return true;
	const fileExt = '.' + fileName.split('.').pop().toLowerCase();
	return allowedTypes.includes(fileExt);
};

export const generateUniqueId = () => {
	return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// 默认导出所有API函数
export default {
	// 应用相关
	getAgentApps,
	getAgentAppById,
	createAgentApp,
	updateAgentApp,
	deleteAgentApp,

	// 表单和提交
	submitAgentForm,
	validateFormData,
	previewAgentResponse,

	// 统计和收藏
	getAgentAppStats,
	toggleFavoriteApp,
	getUserFavoriteApps,

	// 分类管理
	getAppCategories,
	createAppCategory,
	updateAppCategory,
	deleteAppCategory,

	// 提交记录
	getSubmissions,
	getSubmissionById,
	deleteSubmission,

	// 模板系统
	getAppTemplates,
	getAppTemplateById,
	createAppTemplate,
	createAppFromTemplate,

	// 文件处理
	uploadFile,
	uploadFiles,
	deleteFile,

	// 搜索和推荐
	searchApps,
	getRecommendedApps,
	getPopularApps,
	getUserAppHistory,

	// 导入导出
	exportAppConfig,
	importAppConfig,

	// 评价系统
	rateApp,
	getAppRatings,

	// 管理员功能
	getAdminStats,
	getAdminAppList,
	batchUpdateAppStatus,

	// 智能体执行
	executeAgent,

	// 工具函数
	formatFileSize,
	validateFileType,
	generateUniqueId
};
