<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let field = {};
	export let value = [];
	export let error = '';
	export let readonly = false;

	let fileInput;
	let dragOver = false;
	let uploading = false;

	// 处理文件选择
	const handleFileSelect = async (event) => {
		const files = Array.from(event.target.files || []);
		await processFiles(files);
	};

	// 处理拖拽上传
	const handleDrop = async (event) => {
		event.preventDefault();
		dragOver = false;

		if (readonly) return;

		const files = Array.from(event.dataTransfer.files);
		await processFiles(files);
	};

	const handleDragOver = (event) => {
		event.preventDefault();
		if (!readonly) {
			dragOver = true;
		}
	};

	const handleDragLeave = () => {
		dragOver = false;
	};

	// 处理文件列表
	const processFiles = async (files) => {
		if (!files.length) return;

		const maxFiles = field.validation?.maxFiles || 10;
		const maxSize = parseSize(field.validation?.maxSize || '10MB');
		const allowedTypes = field.validation?.allowedTypes || [];

		// 验证文件
		const validFiles = [];
		const errors = [];

		for (const file of files) {
			// 检查文件数量限制
			if (value.length + validFiles.length >= maxFiles) {
				errors.push(`最多只能上传${maxFiles}个文件`);
				break;
			}

			// 检查文件大小
			if (file.size > maxSize) {
				errors.push(`文件"${file.name}"大小超过限制(${formatSize(maxSize)})`);
				continue;
			}

			// 检查文件类型
			if (allowedTypes.length > 0) {
				const fileExt = '.' + file.name.split('.').pop().toLowerCase();
				if (!allowedTypes.includes(fileExt)) {
					errors.push(`文件"${file.name}"格式不支持`);
					continue;
				}
			}

			validFiles.push(file);
		}

		if (errors.length > 0) {
			// 这里应该显示错误信息
			console.error('File validation errors:', errors);
			return;
		}

		// 上传文件
		if (validFiles.length > 0) {
			await uploadFiles(validFiles);
		}
	};

	// 上传文件
	const uploadFiles = async (files) => {
		uploading = true;

		try {
			const uploadedFiles = [];

			for (const file of files) {
				// 这里应该调用实际的上传API
				// 暂时创建本地文件对象
				const fileInfo = {
					id: generateId(),
					name: file.name,
					size: file.size,
					type: file.type,
					url: URL.createObjectURL(file), // 临时URL，实际应该是服务器返回的URL
					uploadTime: Date.now()
				};

				uploadedFiles.push(fileInfo);
			}

			value = [...value, ...uploadedFiles];
			dispatch('change', value);
		} catch (error) {
			console.error('File upload failed:', error);
		} finally {
			uploading = false;
		}
	};

	// 移除文件
	const removeFile = (fileId) => {
		value = value.filter((file) => file.id !== fileId);
		dispatch('change', value);
	};

	// 工具函数
	const parseSize = (sizeStr) => {
		const units = { KB: 1024, MB: 1024 * 1024, GB: 1024 * 1024 * 1024 };
		const match = sizeStr.match(/^(\d+)(KB|MB|GB)$/i);
		if (match) {
			return parseInt(match[1]) * units[match[2].toUpperCase()];
		}
		return parseInt(sizeStr) || 0;
	};

	const formatSize = (bytes) => {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
	};

	const generateId = () => {
		return Date.now().toString(36) + Math.random().toString(36).substr(2);
	};

	// 获取文件图标
	const getFileIcon = (fileName) => {
		const ext = fileName.split('.').pop().toLowerCase();
		const iconMap = {
			pdf: '📄',
			doc: '📝',
			docx: '📝',
			xls: '📊',
			xlsx: '📊',
			ppt: '📽️',
			pptx: '📽️',
			txt: '📃',
			jpg: '🖼️',
			jpeg: '🖼️',
			png: '🖼️',
			gif: '🖼️',
			mp4: '🎥',
			avi: '🎥',
			mov: '🎥',
			mp3: '🎵',
			wav: '🎵',
			zip: '📦',
			rar: '📦'
		};
		return iconMap[ext] || '📁';
	};

	const handleFocus = () => {
		dispatch('focus');
	};

	const handleBlur = () => {
		dispatch('blur');
	};

	// 获取配置参数
	$: allowDrag = field.props?.allowDrag !== false;
	$: allowMultiple = field.props?.allowMultiple !== false;
	$: showPreview = field.props?.showPreview !== false;
	$: maxFiles = field.validation?.maxFiles || 10;
	$: maxSize = field.validation?.maxSize || '10MB';
	$: allowedTypes = field.validation?.allowedTypes || [];

	// 确保value是数组
	$: if (!Array.isArray(value)) {
		value = [];
	}
</script>

<div class="flex flex-col gap-3" class:opacity-70={!!error}>
	<label class="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-1 mb-1">
		{field.label}
		{#if field.required}
			<span class="text-red-500 font-semibold">*</span>
		{/if}
	</label>

	{#if field.description}
		<p class="text-sm text-gray-600 dark:text-gray-400 leading-tight m-0">{field.description}</p>
	{/if}

	<!-- 上传区域 -->
	<div class="relative">
		{#if allowDrag}
			<div
				class="border-2 border-dashed rounded-xl p-8 text-center bg-gray-50 dark:bg-gray-800 cursor-pointer transition-all duration-200 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-900
					{dragOver
					? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
					: 'border-gray-300 dark:border-gray-600'}
					{readonly
					? 'cursor-not-allowed opacity-60 bg-gray-100 dark:bg-gray-700'
					: 'hover:border-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}
					{error ? 'border-red-500 bg-red-50 dark:bg-red-900/20' : ''}"
				on:drop={handleDrop}
				on:dragover={handleDragOver}
				on:dragleave={handleDragLeave}
				on:click={() => !readonly && fileInput.click()}
				on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && !readonly && fileInput.click()}
				tabindex={readonly ? -1 : 0}
				role="button"
				on:focus={handleFocus}
				on:blur={handleBlur}
			>
				<div class="flex flex-col items-center gap-2">
					{#if uploading}
						<div class="text-4xl opacity-70">⏳</div>
						<p class="text-base font-medium text-gray-900 dark:text-white m-0">上传中...</p>
					{:else}
						<div class="text-4xl opacity-70">📁</div>
						<p class="text-base font-medium text-gray-900 dark:text-white m-0">
							{#if readonly}
								只读模式
							{:else}
								点击选择文件或拖拽到此处
							{/if}
						</p>
						{#if !readonly}
							<p class="text-sm text-gray-600 dark:text-gray-400 m-0">
								支持格式: {allowedTypes.length > 0 ? allowedTypes.join(', ') : '所有格式'}
								· 最大 {maxSize} · 最多 {maxFiles} 个文件
							</p>
						{/if}
					{/if}
				</div>
			</div>
		{:else}
			<button
				type="button"
				class="px-6 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-base font-medium cursor-pointer transition-all duration-200 flex items-center gap-2
					{readonly || uploading
					? 'opacity-60 cursor-not-allowed'
					: 'hover:border-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}
					{error
					? 'border-red-500'
					: 'focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-900'}"
				disabled={readonly || uploading}
				on:click={() => fileInput.click()}
			>
				{#if uploading}
					⏳ 上传中...
				{:else}
					📁 选择文件
				{/if}
			</button>
		{/if}

		<!-- 隐藏的文件输入 -->
		<input
			bind:this={fileInput}
			type="file"
			class="hidden"
			multiple={allowMultiple}
			accept={allowedTypes.join(',')}
			disabled={readonly}
			on:change={handleFileSelect}
		/>
	</div>

	<!-- 文件列表 -->
	{#if value.length > 0}
		<div class="flex flex-col gap-3 max-h-80 overflow-y-auto">
			{#each value as file}
				<div
					class="flex items-center gap-4 p-3 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 transition-all duration-200 {readonly
						? ''
						: 'hover:border-gray-300 hover:shadow-sm'}"
				>
					<div class="flex items-center gap-3 flex-1 min-w-0">
						<span class="text-2xl flex-shrink-0">{getFileIcon(file.name)}</span>
						<div class="flex-1 min-w-0">
							<p
								class="text-sm font-medium text-gray-900 dark:text-white m-0 mb-1 overflow-hidden text-ellipsis whitespace-nowrap"
							>
								{file.name}
							</p>
							<p class="text-sm text-gray-600 dark:text-gray-400 m-0">{formatSize(file.size)}</p>
						</div>
					</div>

					{#if showPreview && file.type?.startsWith('image/')}
						<div class="flex-shrink-0">
							<img
								src={file.url}
								alt={file.name}
								class="w-12 h-12 object-cover rounded-md border border-gray-200 dark:border-gray-600"
							/>
						</div>
					{/if}

					{#if !readonly}
						<button
							type="button"
							class="w-8 h-8 border-0 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full cursor-pointer flex items-center justify-center text-sm transition-all duration-200 flex-shrink-0 hover:bg-red-500 hover:text-white"
							on:click={() => removeFile(file.id)}
							title="移除文件"
						>
							✕
						</button>
					{/if}
				</div>
			{/each}
		</div>
	{/if}

	{#if error}
		<p class="text-sm text-red-500 m-0 flex items-center gap-1">
			<span class="text-sm">⚠</span>
			{error}
		</p>
	{/if}

	{#if field.helpText && !error}
		<p class="text-sm text-gray-600 dark:text-gray-400 leading-tight m-0">{field.helpText}</p>
	{/if}
</div>
