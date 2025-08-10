/**
 * MidJourney API Client
 * 提供与后端MidJourney服务的接口通信
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

const MIDJOURNEY_API_BASE_URL = `${WEBUI_API_BASE_URL}/midjourney`;

/**
 * 获取MidJourney配置
 */
export const getMidJourneyConfig = async (token) => {
	try {
		const res = await fetch(`${MIDJOURNEY_API_BASE_URL}/config`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			throw new Error(`HTTP ${res.status}: ${res.statusText}`);
		}

		return await res.json();
	} catch (error) {
		console.error('获取MidJourney配置失败:', error);
		throw error;
	}
};

/**
 * 更新MidJourney配置
 */
export const updateMidJourneyConfig = async (token, config) => {
	try {
		const res = await fetch(`${MIDJOURNEY_API_BASE_URL}/config`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(config)
		});

		if (!res.ok) {
			throw new Error(`HTTP ${res.status}: ${res.statusText}`);
		}

		return await res.json();
	} catch (error) {
		console.error('更新MidJourney配置失败:', error);
		throw error;
	}
};

/**
 * 获取用户积分余额
 */
export const getUserCredits = async (token) => {
	try {
		const res = await fetch(`${MIDJOURNEY_API_BASE_URL}/credits`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			throw new Error(`HTTP ${res.status}: ${res.statusText}`);
		}

		return await res.json();
	} catch (error) {
		console.error('获取用户积分余额失败:', error);
		throw error;
	}
};

/**
 * 执行MidJourney动作 (U1-U4, V1-V4, Reroll)
 */
export const executeAction = async (token, taskId, actionRequest) => {
	try {
		const res = await fetch(`${MIDJOURNEY_API_BASE_URL}/action/${taskId}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(actionRequest)
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({}));
			throw new Error(errorData.detail || `HTTP ${res.status}: ${res.statusText}`);
		}

		return await res.json();
	} catch (error) {
		console.error('执行MidJourney动作失败:', error);
		throw error;
	}
};

/**
 * 提交图像生成任务
 */
export const generateImage = async (token, request) => {
	try {
		const res = await fetch(`${MIDJOURNEY_API_BASE_URL}/generate`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(request)
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({}));
			throw new Error(errorData.detail || `HTTP ${res.status}: ${res.statusText}`);
		}

		return await res.json();
	} catch (error) {
		console.error('提交图像生成任务失败:', error);
		throw error;
	}
};

/**
 * 获取任务状态
 */
export const getTaskStatus = async (token, taskId) => {
	try {
		const res = await fetch(`${MIDJOURNEY_API_BASE_URL}/task/${taskId}`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({}));
			throw new Error(errorData.detail || `HTTP ${res.status}: ${res.statusText}`);
		}

		return await res.json();
	} catch (error) {
		console.error('获取任务状态失败:', error);
		throw error;
	}
};

/**
 * 获取用户任务列表
 */
export const getUserTasks = async (token) => {
	try {
		const res = await fetch(`${MIDJOURNEY_API_BASE_URL}/tasks`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({}));
			throw new Error(errorData.detail || `HTTP ${res.status}: ${res.statusText}`);
		}

		return await res.json();
	} catch (error) {
		console.error('获取用户任务列表失败:', error);
		throw error;
	}
};

/**
 * 取消任务
 */
export const cancelTask = async (token, taskId) => {
	try {
		const res = await fetch(`${MIDJOURNEY_API_BASE_URL}/task/${taskId}`, {
			method: 'DELETE',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		});

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({}));
			throw new Error(errorData.detail || `HTTP ${res.status}: ${res.statusText}`);
		}

		return await res.json();
	} catch (error) {
		console.error('取消任务失败:', error);
		throw error;
	}
};

/**
 * 轮询任务状态直到完成
 */
export const pollTaskStatus = async (token, taskId, onUpdate = null) => {
	const maxPolls = 60; // 最多轮询60次
	const pollInterval = 5000; // 5秒间隔
	let pollCount = 0;

	return new Promise((resolve, reject) => {
		const poll = async () => {
			try {
				pollCount++;
				const status = await getTaskStatus(token, taskId);

				// 调用更新回调
				if (onUpdate) {
					onUpdate(status);
				}

				// 检查任务是否完成
				if (status.status === 'completed') {
					resolve(status);
					return;
				}

				if (status.status === 'failed' || status.status === 'cancelled') {
					reject(new Error(status.message || '任务失败'));
					return;
				}

				// 检查轮询次数
				if (pollCount >= maxPolls) {
					reject(new Error('任务超时'));
					return;
				}

				// 继续轮询
				setTimeout(poll, pollInterval);
			} catch (error) {
				reject(error);
			}
		};

		poll();
	});
};

/**
 * 完整的图像生成流程（提交+轮询）
 */
export const generateImageWithPolling = async (token, request, onUpdate = null) => {
	try {
		// 1. 构建请求对象
		const validatedRequest = buildGenerateRequest(request);

		// 2. 提交任务
		const submitResponse = await generateImage(token, validatedRequest);
		const taskId = submitResponse.task_id;

		// 3. 轮询状态直到完成
		const finalStatus = await pollTaskStatus(token, taskId, onUpdate);

		return {
			task_id: taskId,
			...finalStatus
		};
	} catch (error) {
		console.error('图像生成流程失败:', error);
		throw error;
	}
};

/**
 * 完整的动作执行流程（提交+轮询）
 */
export const executeActionWithPolling = async (token, taskId, actionButton, onUpdate = null) => {
	try {
		// 1. 构建动作请求
		const actionRequest = parseActionButton(actionButton);

		// 2. 执行动作
		const submitResponse = await executeAction(token, taskId, actionRequest);
		const newTaskId = submitResponse.task_id;

		// 3. 轮询状态直到完成
		const finalStatus = await pollTaskStatus(token, newTaskId, onUpdate);

		return {
			task_id: newTaskId,
			parent_task_id: taskId,
			action_type: actionRequest.action_type,
			...finalStatus
		};
	} catch (error) {
		console.error('动作执行流程失败:', error);
		throw error;
	}
};

// 任务状态常量
export const TASK_STATUS = {
	SUBMITTED: 'submitted',
	PROCESSING: 'processing',
	COMPLETED: 'completed',
	FAILED: 'failed',
	CANCELLED: 'cancelled'
};

// 生成模式常量
export const GENERATION_MODE = {
	FAST: 'fast',
	RELAX: 'relax',
	TURBO: 'turbo'
};

// 图像比例常量
export const ASPECT_RATIOS = {
	'1:1': '1:1',
	'16:9': '16:9',
	'9:16': '9:16',
	'3:2': '3:2',
	'2:3': '2:3',
	'4:3': '4:3',
	'3:4': '3:4'
};

// MidJourney和Niji版本常量
export const MJ_VERSIONS = {
	// MidJourney 写实版本
	'MidJourney v5.2': '5.2',
	'MidJourney v6': '6',
	'MidJourney v6.1': '6.1',
	'MidJourney v7': '7',
	// Niji 动漫版本
	'Niji v5': 'niji 5',
	'Niji v6': 'niji 6'
};

// 动作类型常量
export const ACTION_TYPES = {
	UPSCALE: 'upscale',
	VARIATION: 'variation',
	REROLL: 'reroll',
	LOW_VARIATION: 'low_variation',
	HIGH_VARIATION: 'high_variation'
};

// 参考图片类型常量
export const REFERENCE_TYPES = {
	REFERENCE: 'reference',
	STYLE: 'style'
};

/**
 * 将文件转换为Base64编码
 */
export const fileToBase64 = (file) => {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.readAsDataURL(file);
		reader.onload = () => {
			// 移除data:image/...;base64,前缀
			const base64 = reader.result.split(',')[1];
			resolve(base64);
		};
		reader.onerror = (error) => reject(error);
	});
};

/**
 * 验证高级参数
 */
export const validateAdvancedParams = (params) => {
	const errors = [];

	if (params.chaos !== undefined && (params.chaos < 0 || params.chaos > 100)) {
		errors.push('混乱程度必须在0-100之间');
	}

	if (params.stylize !== undefined && (params.stylize < 0 || params.stylize > 1000)) {
		errors.push('风格化程度必须在0-1000之间');
	}

	if (params.seed !== undefined && (params.seed < 0 || params.seed > 4294967295)) {
		errors.push('种子值必须在0-4294967295之间');
	}

	if (params.quality !== undefined && (params.quality < 0.25 || params.quality > 2.0)) {
		errors.push('图像质量必须在0.25-2.0之间');
	}

	if (params.weird !== undefined && (params.weird < 0 || params.weird > 3000)) {
		errors.push('奇异程度必须在0-3000之间');
	}

	if (params.version && !Object.values(MJ_VERSIONS).includes(params.version)) {
		errors.push('不支持的MidJourney版本');
	}

	return errors;
};

/**
 * 构建完整的请求对象
 */
export const buildGenerateRequest = ({
	prompt,
	mode = 'fast',
	aspect_ratio = '1:1',
	negative_prompt = null,
	reference_images = [],
	advanced_params = null
}) => {
	// 验证必需参数
	if (!prompt || prompt.trim().length < 3) {
		throw new Error('图像描述至少需要3个字符');
	}

	if (prompt.length > 2000) {
		throw new Error('图像描述不能超过2000个字符');
	}

	// 验证参考图片数量
	if (reference_images.length > 5) {
		throw new Error('最多只能上传5张参考图片');
	}

	// 验证高级参数
	if (advanced_params) {
		const paramErrors = validateAdvancedParams(advanced_params);
		if (paramErrors.length > 0) {
			throw new Error(paramErrors.join(', '));
		}
	}

	return {
		prompt: prompt.trim(),
		mode,
		aspect_ratio,
		negative_prompt: negative_prompt ? negative_prompt.trim() : null,
		reference_images,
		advanced_params
	};
};

/**
 * 解析动作按钮生成动作请求
 */
export const parseActionButton = (button) => {
	const { label, custom_id, type } = button;

	// 解析按钮索引（如果适用）
	let button_index = null;
	if (type === 'upscale' || type === 'variation') {
		const match = label.match(/(U|V)(\d+)/);
		if (match) {
			button_index = parseInt(match[2]) - 1; // 转换为0-based索引
		}
	}

	return {
		action_type: type,
		button_index,
		custom_id
	};
};
