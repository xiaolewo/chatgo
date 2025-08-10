/**
 * 可灵 (Kling) 视频生成 API Client
 * 提供与后端可灵服务的接口通信
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

const KLING_API_BASE_URL = `${WEBUI_API_BASE_URL}/kling`;

// 任务状态常量
export const TASK_STATUS = {
	SUBMITTED: 'submitted',
	PROCESSING: 'processing',
	SUCCEED: 'succeed',
	FAILED: 'failed'
};

// 模型版本常量
export const KLING_MODELS = [
	{ value: 'kling-v1', label: 'Kling V1', description: '基础版本' },
	{ value: 'kling-v1-6', label: 'Kling V1.6', description: '增强版本' },
	{ value: 'kling-v2-master', label: 'Kling V2 Master', description: '专业版本' },
	{ value: 'kling-v2-1-master', label: 'Kling V2.1 Master', description: '最新版本' }
];

// 生成模式常量
export const GENERATION_MODES = [
	{ value: 'std', label: '标准模式', description: '性价比高，基础质量' },
	{ value: 'pro', label: '专家模式', description: '高品质，生成质量更佳' }
];

// 画面比例常量
export const ASPECT_RATIOS = [
	{ value: '16:9', label: '16:9 (横屏)', description: '常用于影视内容' },
	{ value: '9:16', label: '9:16 (竖屏)', description: '适合手机观看' },
	{ value: '1:1', label: '1:1 (方形)', description: '适合社交媒体' }
];

// 视频时长常量
export const DURATIONS = [
	{ value: '5', label: '5秒', description: '短视频' },
	{ value: '10', label: '10秒', description: '中等时长' }
];

// 运镜类型常量
export const CAMERA_TYPES = [
	{ value: 'simple', label: '简单运镜', description: '六选一基础运镜' },
	{ value: 'down_back', label: '下移拉远', description: '镜头下压并后退' },
	{ value: 'forward_up', label: '推进上移', description: '镜头前进并上仰' },
	{ value: 'right_turn_forward', label: '右旋推进', description: '先右旋转后前进' },
	{ value: 'left_turn_forward', label: '左旋推进', description: '先左旋并前进' }
];

// 运镜配置选项（用于simple类型）
export const CAMERA_CONFIG_OPTIONS = [
	{ key: 'horizontal', label: '水平运镜', range: [-10, 10], description: '控制左右平移' },
	{ key: 'vertical', label: '垂直运镜', range: [-10, 10], description: '控制上下平移' },
	{ key: 'pan', label: '水平摇镜', range: [-10, 10], description: '控制左右旋转' },
	{ key: 'tilt', label: '垂直摇镜', range: [-10, 10], description: '控制上下旋转' },
	{ key: 'roll', label: '旋转运镜', range: [-10, 10], description: '控制滚动旋转' },
	{ key: 'zoom', label: '变焦', range: [-10, 10], description: '控制镜头远近' }
];

/**
 * 获取可灵配置
 */
export const getKlingConfig = async (token) => {
	try {
		const res = await fetch(`${KLING_API_BASE_URL}/config`, {
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
		console.error('获取可灵配置失败:', error);
		throw error;
	}
};

/**
 * 更新可灵配置
 */
export const updateKlingConfig = async (token, config) => {
	try {
		const res = await fetch(`${KLING_API_BASE_URL}/config`, {
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
		console.error('更新可灵配置失败:', error);
		throw error;
	}
};

/**
 * 验证可灵连接
 */
export const verifyKlingConnection = async (token) => {
	try {
		const res = await fetch(`${KLING_API_BASE_URL}/verify`, {
			method: 'POST',
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
		console.error('验证可灵连接失败:', error);
		throw error;
	}
};

/**
 * 生成视频
 */
export const generateVideo = async (token, params) => {
	try {
		const res = await fetch(`${KLING_API_BASE_URL}/generate`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(params)
		});

		if (!res.ok) {
			const errorText = await res.text();
			console.error('可灵API请求失败:', res.status, res.statusText, errorText);
			throw new Error(`HTTP ${res.status}: ${res.statusText} - ${errorText}`);
		}

		return await res.json();
	} catch (error) {
		console.error('生成视频失败:', error);
		throw error;
	}
};

/**
 * 获取任务状态
 */
export const getTaskStatus = async (token, taskId) => {
	try {
		const res = await fetch(`${KLING_API_BASE_URL}/task/${taskId}`, {
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
		console.error('获取任务状态失败:', error);
		throw error;
	}
};

/**
 * 获取用户任务列表
 */
export const getUserTasks = async (token) => {
	try {
		const res = await fetch(`${KLING_API_BASE_URL}/tasks`, {
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
		console.error('获取用户任务列表失败:', error);
		throw error;
	}
};

/**
 * 删除任务
 */
export const deleteTask = async (token, taskId) => {
	try {
		const res = await fetch(`${KLING_API_BASE_URL}/task/${taskId}`, {
			method: 'DELETE',
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
		console.error('删除任务失败:', error);
		throw error;
	}
};

/**
 * 获取用户积分
 */
export const getUserCredits = async (token) => {
	try {
		const res = await fetch(`${KLING_API_BASE_URL}/credits`, {
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
		console.error('获取用户积分失败:', error);
		throw error;
	}
};

/**
 * 构建生成请求参数
 */
export const buildGenerateRequest = (formData) => {
	const request = {
		model_name: formData.model_name || 'kling-v1',
		prompt: formData.prompt,
		cfg_scale: formData.cfg_scale || 0.5,
		mode: formData.mode || 'std',
		aspect_ratio: formData.aspect_ratio || '16:9',
		duration: formData.duration || '5'
	};

	// 可选参数
	if (formData.negative_prompt && formData.negative_prompt.trim()) {
		request.negative_prompt = formData.negative_prompt;
	}

	if (formData.camera_control && formData.camera_control.type) {
		request.camera_control = formData.camera_control;
	}

	if (formData.external_task_id && formData.external_task_id.trim()) {
		request.external_task_id = formData.external_task_id;
	}

	return request;
};

/**
 * 获取模式显示标签
 */
export const getModeLabel = (mode, config = null, creditName = '积分') => {
	if (mode === 'std') {
		const credits = config?.std_credits || 5;
		return `标准模式 (${credits}${creditName})`;
	} else if (mode === 'pro') {
		const credits = config?.pro_credits || 10;
		return `专家模式 (${credits}${creditName})`;
	}
	return mode;
};

/**
 * 获取任务状态显示文本
 */
export const getStatusText = (status) => {
	switch (status) {
		case TASK_STATUS.SUBMITTED:
			return '已提交';
		case TASK_STATUS.PROCESSING:
			return '生成中';
		case TASK_STATUS.SUCCEED:
			return '已完成';
		case TASK_STATUS.FAILED:
			return '生成失败';
		default:
			return '未知状态';
	}
};

/**
 * 获取任务状态颜色
 */
export const getStatusColor = (status) => {
	switch (status) {
		case TASK_STATUS.SUBMITTED:
			return 'text-blue-600 bg-blue-50';
		case TASK_STATUS.PROCESSING:
			return 'text-yellow-600 bg-yellow-50';
		case TASK_STATUS.SUCCEED:
			return 'text-green-600 bg-green-50';
		case TASK_STATUS.FAILED:
			return 'text-red-600 bg-red-50';
		default:
			return 'text-gray-600 bg-gray-50';
	}
};

/**
 * 验证摄像机控制配置
 */
export const validateCameraConfig = (config) => {
	if (!config) return true;

	// 检查是否只有一个参数不为0
	const nonZeroCount = Object.values(config).filter((value) => value !== 0).length;
	return nonZeroCount <= 1;
};

/**
 * 格式化时间显示
 */
export const formatTime = (timestamp) => {
	return new Date(timestamp).toLocaleString('zh-CN');
};

/**
 * 下载视频
 */
export const downloadVideo = async (videoUrl, filename = 'kling-video.mp4') => {
	try {
		const response = await fetch(videoUrl);
		const blob = await response.blob();

		const url = window.URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = filename;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		window.URL.revokeObjectURL(url);
	} catch (error) {
		console.error('下载视频失败:', error);
		throw error;
	}
};
