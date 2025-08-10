/**
 * 即梦 (JiMeng) 视频生成 API Client
 * 提供与后端即梦服务的接口通信
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

const JIMENG_API_BASE_URL = `${WEBUI_API_BASE_URL}/jimeng`;

// 任务状态常量
export const TASK_STATUS = {
	NOT_START: 'NOT_START',
	SUBMITTED: 'SUBMITTED',
	QUEUED: 'QUEUED',
	IN_PROGRESS: 'IN_PROGRESS',
	FAILURE: 'FAILURE',
	SUCCESS: 'SUCCESS'
};

// 视频时长选项
export const DURATIONS = [
	{ value: 5, label: '5秒', description: '短视频' },
	{ value: 10, label: '10秒', description: '中等时长' }
];

// 画面比例常量
export const ASPECT_RATIOS = [
	{ value: '1:1', label: '1:1 (方形)', description: '适合社交媒体' },
	{ value: '21:9', label: '21:9 (超宽屏)', description: '电影画幅' },
	{ value: '16:9', label: '16:9 (横屏)', description: '常用于影视内容' },
	{ value: '9:16', label: '9:16 (竖屏)', description: '适合手机观看' },
	{ value: '4:3', label: '4:3 (标准)', description: '传统电视比例' },
	{ value: '3:4', label: '3:4 (竖屏标准)', description: '竖屏传统比例' }
];

/**
 * 获取即梦配置
 */
export const getJimengConfig = async (token) => {
	try {
		const res = await fetch(`${JIMENG_API_BASE_URL}/config`, {
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
		console.error('获取即梦配置失败:', error);
		throw error;
	}
};

/**
 * 更新即梦配置
 */
export const updateJimengConfig = async (token, config) => {
	try {
		const res = await fetch(`${JIMENG_API_BASE_URL}/config`, {
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
		console.error('更新即梦配置失败:', error);
		throw error;
	}
};

/**
 * 验证即梦连接
 */
export const verifyJimengConnection = async (token) => {
	try {
		const res = await fetch(`${JIMENG_API_BASE_URL}/verify`, {
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
		console.error('验证即梦连接失败:', error);
		throw error;
	}
};

/**
 * 生成视频
 */
export const generateVideo = async (token, params) => {
	try {
		const res = await fetch(`${JIMENG_API_BASE_URL}/generate`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			body: JSON.stringify(params)
		});

		if (!res.ok) {
			const errorText = await res.text();
			console.error('即梦API请求失败:', res.status, res.statusText, errorText);
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
		const res = await fetch(`${JIMENG_API_BASE_URL}/task/${taskId}`, {
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
		const res = await fetch(`${JIMENG_API_BASE_URL}/tasks`, {
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
		const res = await fetch(`${JIMENG_API_BASE_URL}/task/${taskId}`, {
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
		const res = await fetch(`${JIMENG_API_BASE_URL}/credits`, {
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
		prompt: formData.prompt,
		duration: formData.duration || 5,
		aspect_ratio: formData.aspect_ratio || '16:9',
		cfg_scale: formData.cfg_scale || 0.5
	};

	// 可选参数
	if (formData.image_url && formData.image_url.trim()) {
		request.image_url = formData.image_url;
	}

	return request;
};

/**
 * 获取时长显示标签
 */
export const getDurationLabel = (duration, config = null, creditName = '积分') => {
	if (duration === 5) {
		const credits = config?.credits_5s || 5;
		return `5秒 (${credits}${creditName})`;
	} else if (duration === 10) {
		const credits = config?.credits_10s || 10;
		return `10秒 (${credits}${creditName})`;
	}
	return `${duration}秒`;
};

/**
 * 获取任务状态显示文本
 */
export const getStatusText = (status) => {
	switch (status) {
		case TASK_STATUS.NOT_START:
			return '未开始';
		case TASK_STATUS.SUBMITTED:
			return '已提交';
		case TASK_STATUS.QUEUED:
			return '排队中';
		case TASK_STATUS.IN_PROGRESS:
			return '生成中';
		case TASK_STATUS.SUCCESS:
			return '已完成';
		case TASK_STATUS.FAILURE:
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
		case TASK_STATUS.NOT_START:
		case TASK_STATUS.SUBMITTED:
			return 'text-blue-600 bg-blue-50';
		case TASK_STATUS.QUEUED:
		case TASK_STATUS.IN_PROGRESS:
			return 'text-yellow-600 bg-yellow-50';
		case TASK_STATUS.SUCCESS:
			return 'text-green-600 bg-green-50';
		case TASK_STATUS.FAILURE:
			return 'text-red-600 bg-red-50';
		default:
			return 'text-gray-600 bg-gray-50';
	}
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
export const downloadVideo = async (videoUrl, filename = 'jimeng-video.mp4') => {
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
