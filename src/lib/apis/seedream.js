/**
 * 即梦3.0 (Seedream 3.0) API Client
 * 提供与后端即梦3.0服务的接口通信
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

const SEEDREAM_API_BASE_URL = `${WEBUI_API_BASE_URL}/seedream`;

/**
 * 获取即梦3.0配置
 */
export const getSeedreamConfig = async (token) => {
	try {
		const res = await fetch(`${SEEDREAM_API_BASE_URL}/config`, {
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
		console.error('获取即梦3.0配置失败:', error);
		throw error;
	}
};

/**
 * 更新即梦3.0配置
 */
export const updateSeedreamConfig = async (token, config) => {
	try {
		const res = await fetch(`${SEEDREAM_API_BASE_URL}/config`, {
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
		console.error('更新即梦3.0配置失败:', error);
		throw error;
	}
};

/**
 * 验证即梦3.0连接
 */
export const verifySeedreamConnection = async (token) => {
	try {
		const res = await fetch(`${SEEDREAM_API_BASE_URL}/verify`, {
			method: 'POST',
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
		console.error('验证即梦3.0连接失败:', error);
		throw error;
	}
};

/**
 * 获取用户积分余额
 */
export const getUserCredits = async (token) => {
	try {
		const res = await fetch(`${SEEDREAM_API_BASE_URL}/credits`, {
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
 * 生成图像（同步接口）
 */
export const generateImage = async (token, request) => {
	try {
		const res = await fetch(`${SEEDREAM_API_BASE_URL}/generate`, {
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
		console.error('即梦3.0图像生成失败:', error);
		throw error;
	}
};

/**
 * 获取任务状态
 */
export const getTaskStatus = async (token, taskId) => {
	try {
		const res = await fetch(`${SEEDREAM_API_BASE_URL}/task/${taskId}`, {
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
		console.error('获取即梦3.0任务状态失败:', error);
		throw error;
	}
};

/**
 * 获取用户任务列表
 */
export const getUserTasks = async (token) => {
	try {
		const res = await fetch(`${SEEDREAM_API_BASE_URL}/tasks`, {
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
		console.error('获取即梦3.0任务列表失败:', error);
		throw error;
	}
};

/**
 * 删除任务
 */
export const deleteTask = async (token, taskId) => {
	try {
		const res = await fetch(`${SEEDREAM_API_BASE_URL}/task/${taskId}`, {
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
		console.error('删除即梦3.0任务失败:', error);
		throw error;
	}
};

// 即梦3.0服务状态常量
export const TASK_STATUS = {
	SUBMITTED: 'submitted',
	PROCESSING: 'processing',
	COMPLETED: 'completed',
	FAILED: 'failed'
};

// 水印位置常量
export const LOGO_POSITIONS = {
	BOTTOM_RIGHT: 0,
	BOTTOM_LEFT: 1,
	TOP_LEFT: 2,
	TOP_RIGHT: 3
};

// 水印语言常量
export const LOGO_LANGUAGES = {
	CHINESE: 0,
	ENGLISH: 1
};

// 推荐的图像尺寸（基于文档建议的1.3K分辨率）
export const RECOMMENDED_SIZES = {
	'1:1 正方形': { width: 1328, height: 1328 },
	'4:3 横向': { width: 1472, height: 1104 },
	'3:2 横向': { width: 1584, height: 1056 },
	'16:9 宽屏': { width: 1664, height: 936 },
	'21:9 超宽': { width: 2016, height: 864 },
	'3:4 竖向': { width: 1104, height: 1472 },
	'2:3 竖向': { width: 1056, height: 1584 },
	'9:16 竖屏': { width: 936, height: 1664 }
};

/**
 * 验证生成参数
 */
export const validateGenerateParams = (params) => {
	const errors = [];

	// 验证提示词
	if (!params.prompt || params.prompt.trim().length < 3) {
		errors.push('图像描述至少需要3个字符');
	}

	if (params.prompt && params.prompt.length > 2000) {
		errors.push('图像描述不能超过2000个字符');
	}

	// 验证尺寸
	if (params.width && (params.width < 512 || params.width > 2048)) {
		errors.push('图像宽度必须在512-2048之间');
	}

	if (params.height && (params.height < 512 || params.height > 2048)) {
		errors.push('图像高度必须在512-2048之间');
	}

	// 验证scale参数
	if (params.scale && (params.scale < 1.0 || params.scale > 10.0)) {
		errors.push('文本影响程度必须在1.0-10.0之间');
	}

	// 验证种子值
	if (params.seed && params.seed !== -1 && (params.seed < 0 || params.seed > 2147483647)) {
		errors.push('种子值必须在0-2147483647之间，或使用-1表示随机');
	}

	return errors;
};

/**
 * 构建完整的生成请求
 */
export const buildGenerateRequest = ({
	prompt,
	use_pre_llm = false,
	seed = -1,
	scale = 2.5,
	width = 1328,
	height = 1328,
	return_url = true,
	logo_info = null
}) => {
	// 验证参数
	const errors = validateGenerateParams({ prompt, width, height, scale, seed });
	if (errors.length > 0) {
		throw new Error(errors.join(', '));
	}

	const request = {
		prompt: prompt.trim(),
		use_pre_llm,
		seed,
		scale,
		width,
		height,
		return_url
	};

	// 添加水印信息（如果提供）
	if (logo_info) {
		request.logo_info = logo_info;
	}

	return request;
};

/**
 * 获取推荐的图像尺寸名称
 */
export const getSizeLabel = (width, height) => {
	for (const [label, size] of Object.entries(RECOMMENDED_SIZES)) {
		if (size.width === width && size.height === height) {
			return label;
		}
	}
	return `${width}×${height}`;
};

/**
 * 计算图像比例
 */
export const calculateAspectRatio = (width, height) => {
	const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
	const divisor = gcd(width, height);
	return `${width / divisor}:${height / divisor}`;
};

/**
 * 格式化时间
 */
export const formatTimestamp = (timestamp) => {
	if (!timestamp) return '-';
	return new Date(timestamp * 1000).toLocaleString('zh-CN');
};

/**
 * 格式化处理时间
 */
export const formatTimeElapsed = (timeElapsed) => {
	if (!timeElapsed) return '-';
	const match = timeElapsed.match(/([\d.]+)s/);
	if (match) {
		const seconds = parseFloat(match[1]);
		return seconds >= 1 ? `${seconds.toFixed(1)}秒` : `${(seconds * 1000).toFixed(0)}毫秒`;
	}
	return timeElapsed;
};

/**
 * 获取状态显示文本
 */
export const getStatusText = (status) => {
	const statusMap = {
		[TASK_STATUS.SUBMITTED]: '已提交',
		[TASK_STATUS.PROCESSING]: '处理中',
		[TASK_STATUS.COMPLETED]: '已完成',
		[TASK_STATUS.FAILED]: '失败'
	};
	return statusMap[status] || status;
};

/**
 * 获取状态颜色类
 */
export const getStatusColor = (status) => {
	const colorMap = {
		[TASK_STATUS.SUBMITTED]: 'text-blue-600',
		[TASK_STATUS.PROCESSING]: 'text-yellow-600',
		[TASK_STATUS.COMPLETED]: 'text-green-600',
		[TASK_STATUS.FAILED]: 'text-red-600'
	};
	return colorMap[status] || 'text-gray-600';
};
