<script>
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		getAdminAppList,
		createAgentApp,
		updateAgentApp,
		deleteAgentApp,
		getAdminStats
	} from '$lib/apis/agents';
	import { getModels } from '$lib/apis/models';
	import { user, models } from '$lib/stores';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Modal from '$lib/components/common/Modal.svelte';

	const i18n = getContext('i18n');

	let loading = false;
	let apps = [];
	let stats = {};
	let selectedApp = null;
	let showCreateModal = false;
	let showEditModal = false;
	let showDeleteModal = false;
	let showCategoryModal = false;

	// 搜索和过滤
	let searchQuery = '';
	let selectedStatus = '';
	let selectedCategory = '';

	// 分页
	let currentPage = 1;
	let pageSize = 10;
	let totalApps = 0;

	// 表单数据
	let formData = {
		name: '',
		display_name: '',
		description: '',
		category: 'general',
		icon: '🤖',
		form_config: {
			title: '',
			description: '',
			fields: []
		},
		ai_config: {
			model: '',
			system_prompt: '',
			temperature: 0.7,
			max_tokens: 2000
		},
		cost_per_use: 100
	};

	// 智能体分类管理
	let categories = [
		{ value: 'general', label: '通用' },
		{ value: 'productivity', label: '效率' },
		{ value: 'creative', label: '创意' },
		{ value: 'analysis', label: '分析' }
	];
	let newCategoryName = '';
	let newCategoryValue = '';

	// 状态选项
	const statusOptions = [
		{ value: '', label: '全部状态' },
		{ value: 'active', label: '活跃' },
		{ value: 'inactive', label: '禁用' },
		{ value: 'draft', label: '草稿' }
	];

	onMount(async () => {
		loadCategories();
		await loadStats();
		await loadApps();
		await loadSystemModels();
	});

	const loadSystemModels = async () => {
		try {
			// 如果stores中已经有模型数据，直接使用
			if ($models && $models.length > 0) {
				return;
			}

			// 否则从API加载模型
			const systemModels = await getModels(localStorage.token);
			if (systemModels && systemModels.data) {
				models.set(systemModels.data);
			}
		} catch (error) {
			console.warn('Failed to load system models:', error);
			// 如果加载失败，使用一些默认模型作为备选
			models.set([
				{ id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', cost_per_use: 50 },
				{ id: 'gpt-4', name: 'GPT-4', cost_per_use: 200 },
				{ id: 'gpt-4-turbo', name: 'GPT-4 Turbo', cost_per_use: 150 },
				{ id: 'claude-3-sonnet', name: 'Claude 3 Sonnet', cost_per_use: 100 }
			]);
		}
	};

	// 分类管理功能
	function loadCategories() {
		try {
			const savedCategories = localStorage.getItem('agent_categories');
			if (savedCategories) {
				categories = JSON.parse(savedCategories);
			}
		} catch (error) {
			console.warn('Failed to load categories:', error);
		}
	}

	function saveCategories() {
		try {
			localStorage.setItem('agent_categories', JSON.stringify(categories));
		} catch (error) {
			console.warn('Failed to save categories:', error);
		}
	}

	function addCategory() {
		if (!newCategoryName.trim() || !newCategoryValue.trim()) {
			toast.error('请填写分类名称和值');
			return;
		}

		// 检查是否已存在相同的值
		if (categories.some((cat) => cat.value === newCategoryValue)) {
			toast.error('该分类值已存在');
			return;
		}

		categories = [...categories, { value: newCategoryValue, label: newCategoryName }];
		saveCategories();
		newCategoryName = '';
		newCategoryValue = '';
		toast.success('分类添加成功');
	}

	function removeCategory(categoryValue) {
		// 不允许删除默认分类
		const defaultCategories = ['general', 'productivity', 'creative', 'analysis'];
		if (defaultCategories.includes(categoryValue)) {
			toast.error('无法删除默认分类');
			return;
		}

		categories = categories.filter((cat) => cat.value !== categoryValue);
		saveCategories();
		toast.success('分类删除成功');
	}

	// 根据选择的模型自动计算费用
	function updateCostFromModel() {
		const selectedModel = $models.find((model) => model.id === formData.ai_config.model);
		if (selectedModel) {
			// 如果模型有费用配置，使用模型的费用
			if (selectedModel.cost_per_use) {
				formData.cost_per_use = selectedModel.cost_per_use;
			} else if (
				selectedModel.info &&
				selectedModel.info.meta &&
				selectedModel.info.meta.cost_per_use
			) {
				formData.cost_per_use = selectedModel.info.meta.cost_per_use;
			} else {
				// 根据模型ID估算费用
				const modelId = selectedModel.id.toLowerCase();
				if (modelId.includes('gpt-4')) {
					formData.cost_per_use = modelId.includes('turbo') ? 150 : 200;
				} else if (modelId.includes('gpt-3.5')) {
					formData.cost_per_use = 50;
				} else if (modelId.includes('claude-3')) {
					formData.cost_per_use = 100;
				} else if (modelId.includes('gemini')) {
					formData.cost_per_use = 80;
				} else {
					formData.cost_per_use = 100; // 默认费用
				}
			}
		}
	}

	const loadStats = async () => {
		try {
			// 使用模拟数据替代API调用
			stats = {
				total_apps: 4,
				active_apps: 3,
				total_submissions: 58,
				total_users: 15
			};
		} catch (error) {
			console.error('Failed to load stats:', error);
		}
	};

	const loadApps = async () => {
		loading = true;

		try {
			// 尝试从localStorage加载保存的数据
			const savedApps = localStorage.getItem('agent_apps_data');
			if (savedApps) {
				try {
					apps = JSON.parse(savedApps);
					loading = false;
					return;
				} catch (e) {
					console.warn('Failed to parse saved apps data:', e);
				}
			}

			// 使用模拟应用数据
			const mockApps = [
				{
					id: 'app-1',
					name: 'document_summarizer',
					display_name: '文档总结助手',
					description: '帮助您快速总结长篇文档内容，提取关键信息',
					category: 'productivity',
					icon: '📄',
					status: 'active',
					favorite_count: 15,
					usage_count: 120,
					created_at: Math.floor(Date.now() / 1000) - 86400 * 7, // 7天前
					form_config: {
						title: '文档总结',
						description: '上传文档进行AI总结',
						fields: [{ type: 'file', name: 'document', label: '上传文档', required: true }]
					},
					ai_config: {
						model: 'gpt-3.5-turbo',
						system_prompt: '你是一个专业的文档总结助手',
						temperature: 0.7,
						max_tokens: 2000
					},
					cost_per_use: 100
				},
				{
					id: 'app-2',
					name: 'creative_writing',
					display_name: '创意写作工具',
					description: '激发创意灵感，协助您创作小说、诗歌等文学作品',
					category: 'creative',
					icon: '✍️',
					status: 'active',
					favorite_count: 28,
					usage_count: 85,
					created_at: Math.floor(Date.now() / 1000) - 86400 * 3, // 3天前
					form_config: {
						title: '创意写作',
						description: 'AI辅助创意写作',
						fields: [
							{
								type: 'select',
								name: 'type',
								label: '写作类型',
								required: true,
								options: [
									{ value: 'novel', label: '小说' },
									{ value: 'poetry', label: '诗歌' }
								]
							}
						]
					},
					ai_config: {
						model: 'gpt-4',
						system_prompt: '你是一个富有创意的写作助手',
						temperature: 0.8,
						max_tokens: 3000
					},
					cost_per_use: 150
				},
				{
					id: 'app-3',
					name: 'data_analyst',
					display_name: '数据分析师',
					description: '分析数据趋势，生成可视化图表和深度分析报告',
					category: 'analysis',
					icon: '📊',
					status: 'inactive',
					favorite_count: 42,
					usage_count: 200,
					created_at: Math.floor(Date.now() / 1000) - 86400 * 10, // 10天前
					form_config: {
						title: '数据分析',
						description: '上传数据文件进行分析',
						fields: [{ type: 'file', name: 'data', label: '数据文件', required: true }]
					},
					ai_config: {
						model: 'gpt-4',
						system_prompt: '你是一个专业的数据分析师',
						temperature: 0.3,
						max_tokens: 4000
					},
					cost_per_use: 200
				},
				{
					id: 'app-4',
					name: 'lesson_plan_generator',
					display_name: '教案生成助手',
					description: '根据学科、阶段、教材等信息，智能生成专业的教案内容',
					category: 'productivity',
					icon: '📚',
					status: 'active',
					favorite_count: 35,
					usage_count: 168,
					created_at: Math.floor(Date.now() / 1000) - 86400 * 2, // 2天前
					form_config: {
						title: '智能教案生成',
						description: '请填写课程信息，AI将为您生成专业的教案',
						fields: [
							{
								id: 'field_subject',
								type: 'select',
								name: 'subject',
								label: '学科',
								required: true,
								options: [
									{ value: 'chinese', label: '语文' },
									{ value: 'math', label: '数学' },
									{ value: 'english', label: '英语' }
								]
							},
							{
								id: 'field_stage',
								type: 'select',
								name: 'stage',
								label: '阶段',
								required: true,
								options: [
									{ value: 'primary', label: '小学' },
									{ value: 'middle', label: '初中' },
									{ value: 'high', label: '高中' }
								]
							},
							{
								id: 'field_textbook',
								type: 'select',
								name: 'textbook',
								label: '教材',
								required: true,
								options: [
									{ value: 'renjiao', label: '人教版' },
									{ value: 'sujiao', label: '苏教版' },
									{ value: 'beijing_normal', label: '北师大版' },
									{ value: 'xishi', label: '西师版' }
								]
							},
							{
								id: 'field_volume',
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
									{ value: 'grade6_vol2', label: '六年级下册' },
									{ value: 'grade7_vol1', label: '七年级上册' },
									{ value: 'grade7_vol2', label: '七年级下册' },
									{ value: 'grade8_vol1', label: '八年级上册' },
									{ value: 'grade8_vol2', label: '八年级下册' },
									{ value: 'grade9_vol1', label: '九年级上册' },
									{ value: 'grade9_vol2', label: '九年级下册' },
									{ value: 'grade10_vol1', label: '高一上册' },
									{ value: 'grade10_vol2', label: '高一下册' },
									{ value: 'grade11_vol1', label: '高二上册' },
									{ value: 'grade11_vol2', label: '高二下册' },
									{ value: 'grade12_vol1', label: '高三上册' },
									{ value: 'grade12_vol2', label: '高三下册' }
								]
							},
							{
								id: 'field_topic',
								type: 'text',
								name: 'topic',
								label: '课题',
								required: true,
								placeholder: '请输入具体的课题名称',
								validation: { maxLength: 50 }
							},
							{
								id: 'field_hours',
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
								]
							},
							{
								id: 'field_template',
								type: 'file',
								name: 'template',
								label: '教案模板文件',
								required: false,
								validation: {
									maxFiles: 1,
									maxSize: '5MB',
									allowedTypes: ['.docx', '.doc', '.pdf']
								}
							},
							{
								id: 'field_references',
								type: 'file',
								name: 'references',
								label: '教案参考资料',
								required: false,
								validation: {
									maxFiles: 10,
									maxSize: '50MB',
									allowedTypes: ['.docx', '.doc', '.pdf', '.pptx', '.ppt', '.txt']
								}
							}
						]
					},
					ai_config: {
						model: 'gpt-4',
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
					},
					cost_per_use: 120
				}
			];

			// 应用过滤条件
			let filteredApps = mockApps.filter((app) => {
				if (selectedStatus && app.status !== selectedStatus) return false;
				if (selectedCategory && app.category !== selectedCategory) return false;
				if (searchQuery) {
					const query = searchQuery.toLowerCase();
					return (
						app.display_name.toLowerCase().includes(query) ||
						app.description.toLowerCase().includes(query)
					);
				}
				return true;
			});

			// 模拟分页
			const startIndex = (currentPage - 1) * pageSize;
			const endIndex = startIndex + pageSize;

			apps = filteredApps.slice(startIndex, endIndex);
			totalApps = filteredApps.length;
		} catch (error) {
			console.error('Failed to load apps:', error);
			toast.error('加载应用列表失败');
		} finally {
			loading = false;
		}
	};

	const handleSearch = async () => {
		currentPage = 1;
		await loadApps();
	};

	const handlePageChange = async (page) => {
		currentPage = page;
		await loadApps();
	};

	const openCreateModal = () => {
		// 使用第一个可用模型作为默认值
		const defaultModel = $models && $models.length > 0 ? $models[0].id : '';

		formData = {
			name: '',
			display_name: '',
			description: '',
			category: 'general',
			icon: '🤖',
			form_config: {
				title: '',
				description: '',
				fields: []
			},
			ai_config: {
				model: defaultModel,
				system_prompt: '',
				temperature: 0.7,
				max_tokens: 2000
			},
			cost_per_use: 100
		};
		showCreateModal = true;
	};

	const openEditModal = (app) => {
		selectedApp = app;
		formData = {
			name: app.name,
			display_name: app.display_name,
			description: app.description || '',
			category: app.category,
			icon: app.icon || '🤖',
			form_config: app.form_config || { title: '', description: '', fields: [] },
			ai_config: {
				model: app.ai_config?.model || 'gpt-3.5-turbo',
				system_prompt: app.ai_config?.system_prompt || '',
				temperature: app.ai_config?.temperature || 0.7,
				max_tokens: app.ai_config?.max_tokens || 2000
			},
			cost_per_use: app.cost_per_use || 100
		};
		console.log('Edit modal data:', formData); // 调试输出
		showEditModal = true;
	};

	const openDeleteModal = (app) => {
		selectedApp = app;
		showDeleteModal = true;
	};

	const handleCreate = async () => {
		try {
			// 基本验证
			if (!formData.name || !formData.display_name) {
				toast.error('请填写应用名称和显示名称');
				return;
			}

			if (!formData.ai_config.model) {
				toast.error('请选择AI模型');
				return;
			}

			// 模拟创建应用
			console.log('Creating app with data:', formData);
			toast.success('应用创建成功');
			showCreateModal = false;
			await loadApps();
			await loadStats();
		} catch (error) {
			console.error('Failed to create app:', error);
			toast.error('创建应用失败');
		}
	};

	const handleUpdate = async () => {
		try {
			if (!selectedApp) return;

			// 基本验证
			if (!formData.display_name) {
				toast.error('请填写显示名称');
				return;
			}

			if (!formData.ai_config.model) {
				toast.error('请选择AI模型');
				return;
			}

			const updateData = {
				display_name: formData.display_name,
				description: formData.description,
				category: formData.category,
				icon: formData.icon,
				form_config: formData.form_config,
				ai_config: formData.ai_config,
				cost_per_use: formData.cost_per_use
			};

			// 模拟更新应用 - 更新内存中的数据
			console.log('Updating app:', selectedApp.id, 'with data:', updateData);

			// 找到并更新应用数据
			const appIndex = apps.findIndex((app) => app.id === selectedApp.id);
			if (appIndex >= 0) {
				apps[appIndex] = {
					...apps[appIndex],
					...updateData,
					updated_at: Math.floor(Date.now() / 1000)
				};
				// 触发响应式更新
				apps = apps;
			}

			toast.success('应用更新成功');
			showEditModal = false;
			selectedApp = null;
			// 不需要重新 loadApps，因为已经更新了内存中的数据
		} catch (error) {
			console.error('Failed to update app:', error);
			toast.error('更新应用失败');
		}
	};

	const handleDelete = async () => {
		try {
			if (!selectedApp) return;

			// 模拟删除应用
			console.log('Deleting app:', selectedApp.id);
			toast.success('应用删除成功');
			showDeleteModal = false;
			selectedApp = null;
			await loadApps();
			await loadStats();
		} catch (error) {
			console.error('Failed to delete app:', error);
			toast.error('删除应用失败');
		}
	};

	const handleStatusToggle = async (app) => {
		try {
			const newStatus = app.status === 'active' ? 'inactive' : 'active';
			// 模拟状态切换
			console.log('Toggling status for app:', app.id, 'to:', newStatus);
			toast.success(`应用已${newStatus === 'active' ? '启用' : '禁用'}`);
			await loadApps();
		} catch (error) {
			console.error('Failed to toggle status:', error);
			toast.error('状态更新失败');
		}
	};

	// 添加示例表单字段
	const addSampleField = (type) => {
		const sampleFields = {
			text: {
				id: `field_${Date.now()}`,
				type: 'text',
				label: '文本输入',
				required: false,
				placeholder: '请输入文本',
				validation: { maxLength: 100 }
			},
			select: {
				id: `field_${Date.now()}`,
				type: 'select',
				label: '下拉选择',
				required: false,
				options: [
					{ value: 'option1', label: '选项1' },
					{ value: 'option2', label: '选项2' }
				]
			},
			switch: {
				id: `field_${Date.now()}`,
				type: 'switch',
				label: '开关控件',
				required: false,
				defaultValue: false
			},
			file: {
				id: `field_${Date.now()}`,
				type: 'file',
				label: '文件上传',
				required: false,
				validation: {
					maxFiles: 10,
					maxSize: '10MB',
					allowedTypes: ['.png', '.jpg', '.pdf', '.docx']
				}
			}
		};

		if (sampleFields[type]) {
			formData.form_config.fields = [...formData.form_config.fields, sampleFields[type]];
		}
	};

	// 删除字段
	const removeField = (index) => {
		formData.form_config.fields = formData.form_config.fields.filter((_, i) => i !== index);
	};

	$: totalPages = Math.ceil(totalApps / pageSize);
</script>

<div class="agent-admin">
	<!-- 头部统计 -->
	<div class="admin-header">
		<h1 class="admin-title">智能体应用管理</h1>
		<div class="stats-grid">
			<div class="stat-card">
				<div class="stat-value">{stats.total_apps || 0}</div>
				<div class="stat-label">总应用数</div>
			</div>
			<div class="stat-card">
				<div class="stat-value">{stats.active_apps || 0}</div>
				<div class="stat-label">活跃应用</div>
			</div>
			<div class="stat-card">
				<div class="stat-value">{stats.total_submissions || 0}</div>
				<div class="stat-label">总提交数</div>
			</div>
			<div class="stat-card">
				<div class="stat-value">{stats.total_users || 0}</div>
				<div class="stat-label">用户数量</div>
			</div>
		</div>
	</div>

	<!-- 操作栏 -->
	<div class="admin-toolbar">
		<div class="search-filters">
			<input
				type="text"
				class="search-input"
				placeholder="搜索应用..."
				bind:value={searchQuery}
				on:keydown={(e) => e.key === 'Enter' && handleSearch()}
			/>

			<select class="filter-select" bind:value={selectedStatus} on:change={handleSearch}>
				{#each statusOptions as option}
					<option value={option.value}>{option.label}</option>
				{/each}
			</select>

			<select class="filter-select" bind:value={selectedCategory} on:change={handleSearch}>
				<option value="">全部分类</option>
				{#each categories as category}
					<option value={category.value}>{category.label}</option>
				{/each}
			</select>

			<button class="btn btn-secondary" on:click={handleSearch}> 搜索 </button>
		</div>

		<button class="btn btn-primary" on:click={openCreateModal}> 新建应用 </button>
	</div>

	<!-- 应用列表 -->
	<div class="app-list">
		{#if loading}
			<div class="loading-container">
				<Spinner />
				<p>加载中...</p>
			</div>
		{:else if apps.length === 0}
			<div class="empty-state">
				<div class="empty-icon">📱</div>
				<h3>暂无应用</h3>
				<p>点击"新建应用"创建第一个智能体应用</p>
			</div>
		{:else}
			<div class="app-table">
				<table>
					<thead>
						<tr>
							<th>应用信息</th>
							<th>分类</th>
							<th>状态</th>
							<th>使用统计</th>
							<th>创建时间</th>
							<th>操作</th>
						</tr>
					</thead>
					<tbody>
						{#each apps as app}
							<tr>
								<td>
									<div class="app-info">
										<span class="app-icon">{app.icon || '🤖'}</span>
										<div>
											<div class="app-name">{app.display_name}</div>
											<div class="app-id">ID: {app.id}</div>
										</div>
									</div>
								</td>
								<td>
									<span class="category-tag">
										{categories.find((c) => c.value === app.category)?.label || app.category}
									</span>
								</td>
								<td>
									<button
										class="status-toggle {app.status}"
										on:click={() => handleStatusToggle(app)}
									>
										{app.status === 'active' ? '活跃' : app.status === 'inactive' ? '禁用' : '草稿'}
									</button>
								</td>
								<td>
									<div class="usage-stats">
										<div>{app.usage_count || 0} 次使用</div>
										<div>{app.favorite_count || 0} 收藏</div>
									</div>
								</td>
								<td>
									{new Date(app.created_at * 1000).toLocaleDateString('zh-CN')}
								</td>
								<td>
									<div class="action-buttons">
										<button class="btn btn-sm btn-outline" on:click={() => openEditModal(app)}>
											编辑
										</button>
										<button class="btn btn-sm btn-danger" on:click={() => openDeleteModal(app)}>
											删除
										</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- 分页 -->
			{#if totalPages > 1}
				<div class="pagination">
					<button
						class="btn btn-sm"
						disabled={currentPage === 1}
						on:click={() => handlePageChange(currentPage - 1)}
					>
						上一页
					</button>

					<span class="page-info">
						第 {currentPage} 页，共 {totalPages} 页
					</span>

					<button
						class="btn btn-sm"
						disabled={currentPage === totalPages}
						on:click={() => handlePageChange(currentPage + 1)}
					>
						下一页
					</button>
				</div>
			{/if}
		{/if}
	</div>
</div>

<!-- 创建应用模态框 -->
{#if showCreateModal}
	<Modal on:close={() => (showCreateModal = false)} size="lg">
		<div class="modal-content">
			<h2>新建智能体应用</h2>

			<div class="form-grid">
				<div class="form-group">
					<label>应用名称 *</label>
					<input type="text" bind:value={formData.name} placeholder="app_name" tabindex="1" />
				</div>

				<div class="form-group">
					<label>显示名称 *</label>
					<input type="text" bind:value={formData.display_name} placeholder="应用显示名称" />
				</div>

				<div class="form-group">
					<div class="form-label-with-action">
						<label>分类</label>
						<button type="button" class="btn-link" on:click={() => (showCategoryModal = true)}>
							管理分类
						</button>
					</div>
					<select bind:value={formData.category}>
						{#each categories as category}
							<option value={category.value}>{category.label}</option>
						{/each}
					</select>
				</div>

				<div class="form-group">
					<label>图标</label>
					<input type="text" bind:value={formData.icon} placeholder="🤖" />
				</div>

				<div class="form-group full-width">
					<label>应用描述</label>
					<textarea bind:value={formData.description} placeholder="描述应用的功能和用途"></textarea>
				</div>

				<div class="form-group">
					<label>每次使用积分</label>
					<input type="number" bind:value={formData.cost_per_use} min="1" />
					<div class="form-help">建议费用会根据AI模型自动填充，您可以自定义修改</div>
				</div>
			</div>

			<!-- 简化的表单配置 -->
			<div class="form-section">
				<h3>表单配置</h3>
				<div class="form-group">
					<label>表单标题</label>
					<input type="text" bind:value={formData.form_config.title} />
				</div>
				<div class="form-group">
					<label>表单描述</label>
					<textarea bind:value={formData.form_config.description}></textarea>
				</div>

				<div class="fields-section">
					<div class="fields-header">
						<h4>表单字段</h4>
						<div class="field-buttons">
							<button type="button" class="btn btn-sm" on:click={() => addSampleField('text')}
								>+ 文本</button
							>
							<button type="button" class="btn btn-sm" on:click={() => addSampleField('select')}
								>+ 选择</button
							>
							<button type="button" class="btn btn-sm" on:click={() => addSampleField('switch')}
								>+ 开关</button
							>
							<button type="button" class="btn btn-sm" on:click={() => addSampleField('file')}
								>+ 文件</button
							>
						</div>
					</div>

					{#each formData.form_config.fields as field, index}
						<div class="field-item">
							<div class="field-info">
								<span class="field-type">{field.type}</span>
								<span class="field-label">{field.label}</span>
							</div>
							<button
								type="button"
								class="btn btn-sm btn-danger"
								on:click={() => removeField(index)}>删除</button
							>
						</div>
					{/each}
				</div>
			</div>

			<!-- AI配置 -->
			<div class="form-section">
				<h3>AI配置</h3>
				<div class="form-group">
					<label>模型 *</label>
					<select bind:value={formData.ai_config.model} on:change={updateCostFromModel}>
						<option value="">请选择模型</option>
						{#each $models as model}
							<option value={model.id}>{model.name || model.id}</option>
						{/each}
					</select>
					<div class="form-help">选择用于处理用户请求的AI模型</div>
				</div>
				<div class="form-group">
					<label>系统提示</label>
					<textarea
						bind:value={formData.ai_config.system_prompt}
						placeholder="定义AI的角色和行为规则，例如：你是一个专业的文档总结助手，能够帮助用户快速提取文档的关键信息..."
					></textarea>
					<div class="form-help">定义AI的角色、行为规则和回复风格</div>
				</div>
				<div class="form-grid">
					<div class="form-group">
						<label>Temperature</label>
						<input
							type="number"
							bind:value={formData.ai_config.temperature}
							min="0"
							max="2"
							step="0.1"
						/>
						<div class="form-help">控制回复的随机性 (0.0-2.0)</div>
					</div>
					<div class="form-group">
						<label>最大Token数</label>
						<input type="number" bind:value={formData.ai_config.max_tokens} min="1" max="8192" />
						<div class="form-help">限制AI回复的最大长度</div>
					</div>
				</div>
			</div>

			<div class="modal-actions">
				<button class="btn btn-secondary" on:click={() => (showCreateModal = false)}> 取消 </button>
				<button class="btn btn-primary" on:click={handleCreate}> 创建应用 </button>
			</div>
		</div>
	</Modal>
{/if}

<!-- 编辑应用模态框 -->
{#if showEditModal && selectedApp}
	<Modal on:close={() => (showEditModal = false)} size="lg">
		<div class="modal-content">
			<h2>编辑应用 - {selectedApp.display_name}</h2>

			<div class="form-grid">
				<div class="form-group">
					<label>应用名称 *</label>
					<input type="text" bind:value={formData.name} readonly class="readonly" />
					<div class="form-help">应用名称创建后不可修改</div>
				</div>

				<div class="form-group">
					<label>显示名称 *</label>
					<input type="text" bind:value={formData.display_name} placeholder="应用显示名称" />
				</div>

				<div class="form-group">
					<div class="form-label-with-action">
						<label>分类</label>
						<button type="button" class="btn-link" on:click={() => (showCategoryModal = true)}>
							管理分类
						</button>
					</div>
					<select bind:value={formData.category}>
						{#each categories as category}
							<option value={category.value}>{category.label}</option>
						{/each}
					</select>
				</div>

				<div class="form-group">
					<label>图标</label>
					<input type="text" bind:value={formData.icon} placeholder="🤖" />
				</div>

				<div class="form-group full-width">
					<label>应用描述</label>
					<textarea bind:value={formData.description} placeholder="描述应用的功能和用途"></textarea>
				</div>

				<div class="form-group">
					<label>每次使用积分</label>
					<input type="number" bind:value={formData.cost_per_use} min="1" />
					<div class="form-help">建议费用会根据AI模型自动填充，您可以自定义修改</div>
				</div>
			</div>

			<!-- 表单配置 -->
			<div class="form-section">
				<h3>表单配置</h3>
				<div class="form-group">
					<label>表单标题</label>
					<input type="text" bind:value={formData.form_config.title} />
				</div>
				<div class="form-group">
					<label>表单描述</label>
					<textarea bind:value={formData.form_config.description}></textarea>
				</div>

				<div class="fields-section">
					<div class="fields-header">
						<h4>表单字段</h4>
						<div class="field-buttons">
							<button type="button" class="btn btn-sm" on:click={() => addSampleField('text')}
								>+ 文本</button
							>
							<button type="button" class="btn btn-sm" on:click={() => addSampleField('select')}
								>+ 选择</button
							>
							<button type="button" class="btn btn-sm" on:click={() => addSampleField('switch')}
								>+ 开关</button
							>
							<button type="button" class="btn btn-sm" on:click={() => addSampleField('file')}
								>+ 文件</button
							>
						</div>
					</div>

					{#each formData.form_config.fields as field, index}
						<div class="field-item">
							<div class="field-info">
								<span class="field-type">{field.type}</span>
								<span class="field-label">{field.label}</span>
							</div>
							<button
								type="button"
								class="btn btn-sm btn-danger"
								on:click={() => removeField(index)}>删除</button
							>
						</div>
					{/each}
				</div>
			</div>

			<!-- AI配置 -->
			<div class="form-section">
				<h3>AI配置</h3>
				<div class="form-group">
					<label>模型 *</label>
					<select bind:value={formData.ai_config.model} on:change={updateCostFromModel}>
						<option value="">请选择模型</option>
						{#each $models as model}
							<option value={model.id}>{model.name || model.id}</option>
						{/each}
					</select>
					<div class="form-help">选择用于处理用户请求的AI模型</div>
				</div>
				<div class="form-group">
					<label>系统提示</label>
					<textarea
						bind:value={formData.ai_config.system_prompt}
						placeholder="定义AI的角色和行为规则，例如：你是一个专业的文档总结助手，能够帮助用户快速提取文档的关键信息..."
					></textarea>
					<div class="form-help">定义AI的角色、行为规则和回复风格</div>
				</div>
				<div class="form-grid">
					<div class="form-group">
						<label>Temperature</label>
						<input
							type="number"
							bind:value={formData.ai_config.temperature}
							min="0"
							max="2"
							step="0.1"
						/>
						<div class="form-help">控制回复的随机性 (0.0-2.0)</div>
					</div>
					<div class="form-group">
						<label>最大Token数</label>
						<input type="number" bind:value={formData.ai_config.max_tokens} min="1" max="8192" />
						<div class="form-help">限制AI回复的最大长度</div>
					</div>
				</div>
			</div>

			<div class="modal-actions">
				<button class="btn btn-secondary" on:click={() => (showEditModal = false)}> 取消 </button>
				<button class="btn btn-primary" on:click={handleUpdate}> 保存更改 </button>
			</div>
		</div>
	</Modal>
{/if}

<!-- 删除确认模态框 -->
{#if showDeleteModal && selectedApp}
	<Modal on:close={() => (showDeleteModal = false)}>
		<div class="modal-content">
			<h2>确认删除</h2>
			<p>确定要删除应用 "{selectedApp.display_name}" 吗？此操作不可撤销。</p>

			<div class="modal-actions">
				<button class="btn btn-secondary" on:click={() => (showDeleteModal = false)}> 取消 </button>
				<button class="btn btn-danger" on:click={handleDelete}> 确认删除 </button>
			</div>
		</div>
	</Modal>
{/if}

<!-- 分类管理模态框 -->
{#if showCategoryModal}
	<Modal on:close={() => (showCategoryModal = false)}>
		<div class="modal-content">
			<h2>智能体分类管理</h2>

			<div class="category-section">
				<h3>添加新分类</h3>
				<div class="form-grid">
					<div class="form-group">
						<label>分类名称</label>
						<input type="text" bind:value={newCategoryName} placeholder="例如：营销工具" />
					</div>
					<div class="form-group">
						<label>分类值</label>
						<input type="text" bind:value={newCategoryValue} placeholder="例如：marketing" />
					</div>
				</div>
				<button class="btn btn-primary" on:click={addCategory}> 添加分类 </button>
			</div>

			<div class="category-section">
				<h3>现有分类</h3>
				<div class="category-list">
					{#each categories as category}
						<div class="category-item">
							<div class="category-info">
								<span class="category-label">{category.label}</span>
								<span class="category-value">({category.value})</span>
							</div>
							{#if !['general', 'productivity', 'creative', 'analysis'].includes(category.value)}
								<button
									class="btn btn-sm btn-danger"
									on:click={() => removeCategory(category.value)}
								>
									删除
								</button>
							{:else}
								<span class="default-tag">默认</span>
							{/if}
						</div>
					{/each}
				</div>
			</div>

			<div class="modal-actions">
				<button class="btn btn-primary" on:click={() => (showCategoryModal = false)}> 完成 </button>
			</div>
		</div>
	</Modal>
{/if}

<style>
	.agent-admin {
		padding: 1rem;
		max-width: 1400px;
		margin: 0 auto;
	}

	@media (min-width: 640px) {
		.agent-admin {
			padding: 2rem;
		}
	}

	.admin-header {
		margin-bottom: 2rem;
	}

	.admin-title {
		font-size: 2rem;
		font-weight: 700;
		color: #1f2937;
		margin-bottom: 1.5rem;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}

	.stat-card {
		background: white;
		padding: 1.5rem;
		border-radius: 0.75rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		text-align: center;
	}

	.stat-value {
		font-size: 2rem;
		font-weight: 700;
		color: #667eea;
		margin-bottom: 0.5rem;
	}

	.stat-label {
		color: #6b7280;
		font-size: 0.875rem;
	}

	.admin-toolbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.search-filters {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.search-input,
	.filter-select {
		padding: 0.5rem 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 0.875rem;
	}

	.search-input {
		width: 200px;
	}

	.app-list {
		background: white;
		border-radius: 0.75rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		overflow: hidden;
	}

	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 3rem;
		gap: 1rem;
	}

	.empty-state {
		text-align: center;
		padding: 3rem;
	}

	.empty-icon {
		font-size: 3rem;
		margin-bottom: 1rem;
		opacity: 0.6;
	}

	.app-table {
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
	}

	th,
	td {
		padding: 1rem;
		text-align: left;
		border-bottom: 1px solid #e5e7eb;
	}

	th {
		background: #f9fafb;
		font-weight: 600;
		color: #374151;
	}

	.app-info {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.app-icon {
		font-size: 1.5rem;
	}

	.app-name {
		font-weight: 500;
		color: #1f2937;
	}

	.app-id {
		font-size: 0.75rem;
		color: #9ca3af;
	}

	.category-tag {
		display: inline-block;
		padding: 0.25rem 0.5rem;
		background: #e5e7eb;
		color: #374151;
		border-radius: 0.25rem;
		font-size: 0.75rem;
	}

	.status-toggle {
		padding: 0.25rem 0.75rem;
		border-radius: 1rem;
		border: none;
		font-size: 0.75rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.status-toggle.active {
		background: #10b981;
		color: white;
	}

	.status-toggle.inactive {
		background: #f59e0b;
		color: white;
	}

	.status-toggle.draft {
		background: #6b7280;
		color: white;
	}

	.usage-stats {
		font-size: 0.875rem;
		color: #6b7280;
	}

	.action-buttons {
		display: flex;
		gap: 0.5rem;
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 1.5rem;
		border-top: 1px solid #e5e7eb;
	}

	.page-info {
		color: #6b7280;
		font-size: 0.875rem;
	}

	.modal-content {
		width: 100%;
		max-width: 800px;
		max-height: 85vh;
		overflow-y: auto;
		padding: 2rem;
		margin: 2rem auto;
		background: white;
		border-radius: 1rem;
		box-shadow:
			0 20px 25px -5px rgba(0, 0, 0, 0.1),
			0 10px 10px -5px rgba(0, 0, 0, 0.04);
	}

	:global(.dark) .modal-content {
		background: #1f2937;
		color: white;
		box-shadow:
			0 20px 25px -5px rgba(0, 0, 0, 0.3),
			0 10px 10px -5px rgba(0, 0, 0, 0.2);
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.form-group.full-width {
		grid-column: 1 / -1;
	}

	.form-group label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
	}

	.form-group input,
	.form-group select,
	.form-group textarea {
		padding: 0.5rem 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 0.875rem;
	}

	.form-group textarea {
		resize: vertical;
		min-height: 80px;
	}

	.form-help {
		font-size: 0.75rem;
		color: #6b7280;
		margin-top: 0.25rem;
		line-height: 1.4;
	}

	.form-section {
		margin-bottom: 2rem;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid #e5e7eb;
	}

	.form-section:last-child {
		border-bottom: none;
		margin-bottom: 1rem;
	}

	.form-section h3 {
		font-size: 1.25rem;
		font-weight: 600;
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.form-section h4 {
		font-size: 1rem;
		font-weight: 500;
		color: #374151;
		margin-bottom: 0.5rem;
	}

	.fields-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.field-buttons {
		display: flex;
		gap: 0.5rem;
	}

	.field-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background: #f9fafb;
		border-radius: 0.375rem;
		margin-bottom: 0.5rem;
	}

	.field-info {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.field-type {
		background: #667eea;
		color: white;
		padding: 0.125rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.75rem;
	}

	.field-label {
		font-weight: 500;
		color: #374151;
	}

	.modal-actions {
		display: flex;
		gap: 1rem;
		justify-content: flex-end;
		margin-top: 2rem;
		padding-top: 1.5rem;
		border-top: 1px solid #e5e7eb;
	}

	.btn {
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
		border: none;
		text-decoration: none;
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
	}

	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-primary {
		background: #667eea;
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background: #5a67d8;
	}

	.btn-secondary {
		background: #f3f4f6;
		color: #374151;
		border: 1px solid #d1d5db;
	}

	.btn-secondary:hover:not(:disabled) {
		background: #e5e7eb;
	}

	.btn-outline {
		background: transparent;
		color: #667eea;
		border: 1px solid #667eea;
	}

	.btn-outline:hover {
		background: #667eea;
		color: white;
	}

	.btn-danger {
		background: #ef4444;
		color: white;
	}

	.btn-danger:hover:not(:disabled) {
		background: #dc2626;
	}

	.btn-sm {
		padding: 0.375rem 0.75rem;
		font-size: 0.8rem;
	}

	.form-label-with-action {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.btn-link {
		background: transparent;
		border: none;
		color: #667eea;
		font-size: 0.875rem;
		cursor: pointer;
		text-decoration: none;
		padding: 0;
		transition: color 0.2s ease;
	}

	.btn-link:hover {
		color: #5a67d8;
		text-decoration: underline;
	}

	.category-section {
		margin-bottom: 2rem;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid #e5e7eb;
	}

	.category-section:last-child {
		border-bottom: none;
		margin-bottom: 0;
	}

	.category-section h3 {
		font-size: 1.125rem;
		font-weight: 600;
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.category-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.category-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		transition: background-color 0.2s ease;
	}

	.category-item:hover {
		background: #f3f4f6;
	}

	.category-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex: 1;
	}

	.category-label {
		font-weight: 500;
		color: #1f2937;
	}

	.category-value {
		color: #6b7280;
		font-size: 0.875rem;
	}

	.default-tag {
		background: #e5e7eb;
		color: #6b7280;
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.75rem;
		font-weight: 500;
	}

	.readonly {
		background-color: #f9fafb;
		color: #6b7280;
		cursor: not-allowed;
	}

	:global(.dark) .form-label-with-action label,
	:global(.dark) .category-section h3,
	:global(.dark) .category-label {
		color: #f9fafb;
	}

	:global(.dark) .category-item {
		background: #374151;
		border-color: #4b5563;
	}

	:global(.dark) .category-item:hover {
		background: #4b5563;
	}

	:global(.dark) .category-value {
		color: #9ca3af;
	}

	:global(.dark) .default-tag {
		background: #4b5563;
		color: #9ca3af;
	}

	:global(.dark) .readonly {
		background-color: #374151;
		color: #9ca3af;
	}

	@media (max-width: 768px) {
		.agent-admin {
			padding: 1rem;
		}

		.admin-title {
			font-size: 1.5rem;
		}

		.admin-toolbar {
			flex-direction: column;
			align-items: stretch;
			gap: 0.75rem;
		}

		.search-filters {
			flex-direction: column;
			gap: 0.5rem;
		}

		.search-input {
			width: 100%;
			padding: 0.75rem;
		}

		.filter-select {
			width: 100%;
			padding: 0.75rem;
		}

		.stats-grid {
			grid-template-columns: repeat(2, 1fr);
			gap: 0.75rem;
		}

		.stat-card {
			padding: 1rem;
		}

		.stat-value {
			font-size: 1.5rem;
		}

		.app-table {
			display: block;
			overflow-x: auto;
			white-space: nowrap;
		}

		table {
			min-width: 600px;
		}

		th,
		td {
			padding: 0.5rem;
			font-size: 0.875rem;
		}

		.app-info {
			gap: 0.5rem;
		}

		.app-icon {
			font-size: 1.25rem;
		}

		.action-buttons {
			flex-direction: column;
			gap: 0.25rem;
		}

		.pagination {
			flex-direction: column;
			gap: 0.5rem;
			text-align: center;
		}

		.form-grid {
			grid-template-columns: 1fr;
			gap: 0.75rem;
		}

		.modal-content {
			padding: 1rem;
			margin: 0.5rem auto;
			max-height: 95vh;
			max-width: calc(100vw - 1rem);
			border-radius: 0.5rem;
		}

		.modal-actions {
			flex-direction: column-reverse;
			gap: 0.5rem;
		}

		.modal-actions .btn {
			width: 100%;
			padding: 0.75rem 1rem;
			justify-content: center;
		}

		.fields-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 0.5rem;
		}

		.field-buttons {
			width: 100%;
			justify-content: flex-start;
			flex-wrap: wrap;
		}

		.field-item {
			flex-direction: column;
			align-items: stretch;
			gap: 0.5rem;
			padding: 0.5rem;
		}

		.category-item {
			flex-direction: column;
			align-items: stretch;
			gap: 0.5rem;
			padding: 0.75rem;
		}

		.category-info {
			flex-direction: column;
			align-items: flex-start;
			gap: 0.25rem;
		}

		.btn-sm {
			padding: 0.5rem 0.75rem;
			touch-action: manipulation;
		}
	}
</style>
