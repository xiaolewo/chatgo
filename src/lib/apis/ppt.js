import { WEBUI_API_BASE_URL } from '$lib/constants';

/**
 * PPT生成相关API
 * 基于即梦PPT开放API实现
 */

// API基础配置
const PPT_API_BASE = '/api/v1/ppt';

// 任务状态常量
export const TASK_STATUS = {
	PENDING: 'pending',
	PROCESSING: 'processing',
	COMPLETED: 'completed',
	FAILED: 'failed'
};

// 生成类型常量
export const GENERATION_TYPES = {
	TOPIC: 1, // 智能生成（主题、要求）
	FILE: 2, // 上传文件生成
	MINDMAP: 3, // 上传思维导图生成
	WORD: 4, // 通过word精准转ppt
	URL: 5, // 通过网页链接生成
	TEXT: 6, // 粘贴文本内容生成
	MARKDOWN: 7 // Markdown大纲生成
};

// 篇幅长度
export const LENGTHS = {
	SHORT: 'short', // 10-15页
	MEDIUM: 'medium', // 20-30页
	LONG: 'long' // 25-35页
};

/**
 * 获取PPT配置
 */
export const getPptConfig = async (token) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/config`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			error = err.message ?? err.detail ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 更新PPT配置
 */
export const updatePptConfig = async (token, config) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/config`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(config)
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			error = err.message ?? err.detail ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 获取模板过滤选项
 */
export const getTemplateOptions = async (token) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/template/options`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			error = err.message ?? err.detail ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 分页查询模板
 */
export const getTemplates = async (token, params = {}) => {
	const defaultParams = {
		page: 1,
		size: 10,
		filters: {
			type: 1, // 1-系统模板, 4-用户自定义模板
			category: null,
			style: null,
			themeColor: null
		}
	};

	const requestParams = { ...defaultParams, ...params };

	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/templates`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(requestParams)
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			error = err.message ?? err.detail ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 创建PPT生成任务
 */
export const createPptTask = async (token, type, content = '', files = []) => {
	const formData = new FormData();
	formData.append('type', type);

	if (content) {
		formData.append('content', content);
	}

	// 添加文件
	if (files && files.length > 0) {
		files.forEach((file, index) => {
			formData.append('file', file);
		});
	}

	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/v2/createTask`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`
		},
		body: formData
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			if (typeof err === 'object' && err !== null) {
				error = err.detail || err.message || JSON.stringify(err);
			} else if (typeof err === 'string') {
				error = err;
			} else {
				error = 'An unknown error occurred';
			}
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 获取生成选项
 */
export const getGenerationOptions = async (token) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/v2/options`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			error = err.message ?? err.detail ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 生成PPT大纲内容
 */
export const generateContent = async (token, taskId, options = {}) => {
	const defaultOptions = {
		stream: true,
		length: 'medium',
		scene: null,
		audience: null,
		lang: null,
		prompt: null
	};

	const requestOptions = {
		id: taskId,
		...defaultOptions,
		...options
	};

	console.log('generateContent请求参数:', requestOptions);

	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/v2/generateContent`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(requestOptions)
	})
		.then(async (res) => {
			console.log('generateContent HTTP响应:', {
				status: res.status,
				statusText: res.statusText,
				ok: res.ok
			});

			if (!res.ok) {
				const errorData = await res.json();
				console.error('generateContent HTTP错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			console.error('generateContent请求失败:', {
				error: err,
				message: err.message,
				name: err.name,
				stack: err.stack
			});
			error = err.message || err.detail || `网络请求失败: ${err.toString()}`;
			return null;
		});

	if (error) {
		console.error('generateContent最终错误:', error);
		throw new Error(error);
	}

	console.log('generateContent成功响应:', res);
	return res;
};

/**
 * 生成PPT
 */
export const generatePpt = async (token, taskId, templateId, markdown) => {
	const params = {
		id: taskId,
		templateId,
		markdown
	};

	console.log('generatePpt请求参数:', params);

	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/v2/generatePptx`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(params)
	})
		.then(async (res) => {
			console.log('generatePpt HTTP响应:', {
				status: res.status,
				statusText: res.statusText,
				ok: res.ok
			});

			if (!res.ok) {
				const errorData = await res.json();
				console.error('generatePpt HTTP错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				console.error('处理后的错误消息:', errorMessage);
				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			console.error('generatePpt请求失败:', {
				error: err,
				message: err.message,
				name: err.name,
				stack: err.stack
			});
			// 确保错误信息是字符串
			if (typeof err === 'object' && err.message) {
				error = err.message;
			} else if (typeof err === 'string') {
				error = err;
			} else {
				error = '生成PPT请求失败';
			}
			return null;
		});

	if (error) {
		console.error('generatePpt最终错误:', error);
		throw new Error(error);
	}

	console.log('generatePpt成功响应:', res);
	return res;
};

/**
 * 获取用户PPT列表
 */
export const getUserPpts = async (token, page = 1, size = 10) => {
	const params = { page, size };

	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/listPptx`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(params)
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			error = err.message ?? err.detail ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 加载PPT数据
 */
export const loadPpt = async (token, pptId) => {
	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/loadPptx?id=${pptId}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			error = err.message ?? err.detail ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 修改PPT大纲内容
 */
export const updateContent = async (token, taskId, markdown, question = null, stream = true) => {
	const params = {
		id: taskId,
		stream,
		markdown,
		question
	};

	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/v2/updateContent`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(params)
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			error = err.message ?? err.detail ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 加载PPT大纲内容
 */
export const loadPptMarkdown = async (token, pptId, format = 'tree') => {
	const params = { id: pptId, format };

	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/loadPptxMarkdown`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(params)
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			error = err.message ?? err.detail ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 下载智能动画PPT
 */
export const downloadPptWithAnimation = async (token, pptId, animationType = 1) => {
	let error = null;

	try {
		const response = await fetch(
			`${WEBUI_API_BASE_URL}/ppt/downloadWithAnimation?type=${animationType}&id=${pptId}`,
			{
				method: 'GET',
				headers: {
					Authorization: `Bearer ${token}`
				}
			}
		);

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		// 直接下载文件
		const blob = await response.blob();
		const link = document.createElement('a');
		link.href = window.URL.createObjectURL(blob);
		link.download = `ppt_with_animation_${pptId}.pptx`;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		window.URL.revokeObjectURL(link.href);

		return { success: true };
	} catch (err) {
		error = err.message || 'Download failed';
	}

	if (error) {
		throw new Error(error);
	}
};

/**
 * 下载PPT
 */
export const downloadPpt = async (token, pptId, refresh = false) => {
	const params = { id: pptId, refresh };

	let error = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/ppt/downloadPptx`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(params)
	})
		.then(async (res) => {
			if (!res.ok) {
				const errorData = await res.json();
				console.error('API错误响应:', errorData);

				// 处理不同格式的错误信息
				let errorMessage;
				if (errorData.detail) {
					if (Array.isArray(errorData.detail)) {
						// FastAPI validation error format
						errorMessage = errorData.detail
							.map((err) => `${err.loc?.join('.')}: ${err.msg}`)
							.join(', ');
					} else {
						errorMessage = errorData.detail;
					}
				} else if (errorData.message) {
					errorMessage = errorData.message;
				} else {
					errorMessage = JSON.stringify(errorData);
				}

				throw new Error(errorMessage || `HTTP ${res.status}`);
			}
			return res.json();
		})
		.catch((err) => {
			error = err.message ?? err.detail ?? 'An error occurred';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	// 如果有文件URL，直接下载
	if (res.data?.fileUrl) {
		const link = document.createElement('a');
		link.href = res.data.fileUrl;
		link.download = res.data.name || 'presentation.pptx';
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
	}

	return res;
};

/**
 * 验证PPT连接
 */
export const verifyPptConnection = async (apiUrl, apiKey) => {
	let error = null;

	// 这里可以调用一个简单的API来测试连接
	const res = await fetch(`${apiUrl}/api/ppt/v2/options`, {
		method: 'GET',
		headers: {
			'Api-Key': apiKey
		}
	})
		.then(async (res) => {
			if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
			return res.json();
		})
		.catch((err) => {
			error = err.message || 'Connection failed';
			return null;
		});

	if (error) {
		throw new Error(error);
	}

	return res;
};

/**
 * 获取任务状态文本
 */
export const getStatusText = (status) => {
	const statusMap = {
		[TASK_STATUS.PENDING]: '等待中',
		[TASK_STATUS.PROCESSING]: '处理中',
		[TASK_STATUS.COMPLETED]: '已完成',
		[TASK_STATUS.FAILED]: '失败'
	};
	return statusMap[status] || '未知状态';
};

/**
 * 获取任务状态颜色
 */
export const getStatusColor = (status) => {
	const colorMap = {
		[TASK_STATUS.PENDING]: 'text-yellow-600',
		[TASK_STATUS.PROCESSING]: 'text-blue-600',
		[TASK_STATUS.COMPLETED]: 'text-green-600',
		[TASK_STATUS.FAILED]: 'text-red-600'
	};
	return colorMap[status] || 'text-gray-600';
};

/**
 * 获取生成类型标签
 */
export const getGenerationTypeLabel = (type) => {
	const typeMap = {
		[GENERATION_TYPES.TOPIC]: '智能生成',
		[GENERATION_TYPES.FILE]: '文件生成',
		[GENERATION_TYPES.MINDMAP]: '思维导图',
		[GENERATION_TYPES.WORD]: 'Word转换',
		[GENERATION_TYPES.URL]: '网页生成',
		[GENERATION_TYPES.TEXT]: '文本生成',
		[GENERATION_TYPES.MARKDOWN]: 'Markdown'
	};
	return typeMap[type] || '未知类型';
};
