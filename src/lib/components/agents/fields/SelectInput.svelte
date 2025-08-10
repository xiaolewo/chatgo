<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let field = {};
	export let value = '';
	export let error = '';
	export let readonly = false;

	let isOpen = false;
	let searchQuery = '';
	let selectElement;

	// 处理值变化
	const handleChange = (event) => {
		const newValue = event.target.value;
		value = newValue;
		dispatch('change', newValue);
	};

	const handleFocus = () => {
		dispatch('focus');
	};

	const handleBlur = () => {
		dispatch('blur');
	};

	// 获取选项列表
	$: options = field.options || [];

	// 是否可搜索
	$: searchable = field.props?.searchable || false;

	// 是否可清空
	$: clearable = field.props?.clearable || false;

	// 是否多选
	$: multiple = field.props?.multiple || false;

	// 获取显示值
	const getDisplayValue = (val) => {
		if (!val && val !== 0) return '';

		if (multiple && Array.isArray(val)) {
			return val
				.map((v) => {
					const option = options.find((opt) => opt.value === v);
					return option ? option.label : v;
				})
				.join(', ');
		}

		const option = options.find((opt) => opt.value === val);
		return option ? option.label : val;
	};

	// 处理多选
	const handleMultipleChange = (optionValue, checked) => {
		let newValue = Array.isArray(value) ? [...value] : [];

		if (checked) {
			if (!newValue.includes(optionValue)) {
				newValue.push(optionValue);
			}
		} else {
			newValue = newValue.filter((v) => v !== optionValue);
		}

		value = newValue;
		dispatch('change', newValue);
	};

	// 清空值
	const clearValue = () => {
		value = multiple ? [] : '';
		dispatch('change', value);
	};

	// 过滤选项（用于搜索）
	$: filteredOptions =
		searchable && searchQuery
			? options.filter((option) => option.label.toLowerCase().includes(searchQuery.toLowerCase()))
			: options;

	// 检查选项是否被选中
	const isOptionSelected = (optionValue) => {
		if (multiple && Array.isArray(value)) {
			return value.includes(optionValue);
		}
		return value === optionValue;
	};
</script>

<div class="flex flex-col gap-2">
	<label
		class="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-1 mb-1"
		for="field-{field.id}"
	>
		{field.label}
		{#if field.required}
			<span class="text-red-500 font-semibold">*</span>
		{/if}
	</label>

	{#if field.description}
		<p class="text-sm text-gray-600 dark:text-gray-400 leading-tight m-0">{field.description}</p>
	{/if}

	<div class="relative">
		{#if searchable || multiple}
			<!-- 自定义下拉框 -->
			<div class="relative" class:readonly>
				<div
					class="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 cursor-pointer transition-all duration-200 flex items-center justify-between gap-2
						{readonly
						? 'bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 cursor-not-allowed'
						: 'hover:border-gray-300 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-900'}
						{error ? 'border-red-500 ring-4 ring-red-100 dark:ring-red-900' : ''}"
					tabindex="0"
					on:click={() => !readonly && (isOpen = !isOpen)}
					on:keydown={(e) => e.key === 'Enter' && !readonly && (isOpen = !isOpen)}
				>
					<span
						class="flex-1 text-base text-gray-900 dark:text-white overflow-hidden text-ellipsis whitespace-nowrap"
					>
						{getDisplayValue(value) || field.placeholder || '请选择...'}
					</span>
					<div class="flex items-center gap-2 flex-shrink-0">
						{#if clearable && value && value !== '' && (!Array.isArray(value) || value.length > 0)}
							<button
								type="button"
								class="w-6 h-6 border-0 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full cursor-pointer flex items-center justify-center text-xs transition-all duration-200 hover:bg-gray-200 hover:text-gray-900 dark:hover:bg-gray-600 dark:hover:text-white"
								on:click|stopPropagation={clearValue}
								disabled={readonly}
							>
								✕
							</button>
						{/if}
						<span
							class="text-gray-400 text-xs transition-transform duration-200 {isOpen
								? 'rotate-180'
								: ''}">▼</span
						>
					</div>
				</div>

				{#if isOpen && !readonly}
					<div
						class="absolute top-full left-0 right-0 z-50 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-600 border-t-0 rounded-b-lg shadow-xl max-h-52 overflow-hidden"
					>
						{#if searchable}
							<div class="p-2 border-b border-gray-200 dark:border-gray-600">
								<input
									type="text"
									class="w-full px-2 py-2 border border-gray-200 dark:border-gray-600 rounded text-sm focus:outline-none focus:border-blue-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
									placeholder="搜索选项..."
									bind:value={searchQuery}
									on:click|stopPropagation
								/>
							</div>
						{/if}

						<div class="max-h-40 overflow-y-auto">
							{#each filteredOptions as option}
								<div
									class="px-4 py-3 cursor-pointer flex items-center gap-2 text-base text-gray-900 dark:text-white transition-colors duration-200
										{isOptionSelected(option.value)
										? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-300 font-medium'
										: 'hover:bg-gray-50 dark:hover:bg-gray-700'}
										{option.disabled ? 'text-gray-400 dark:text-gray-500 cursor-not-allowed' : ''}"
									on:click={() =>
										!option.disabled &&
										(multiple
											? handleMultipleChange(option.value, !isOptionSelected(option.value))
											: ((value = option.value),
												dispatch('change', option.value),
												(isOpen = false)))}
								>
									{#if multiple}
										<input
											type="checkbox"
											class="m-0 cursor-pointer"
											checked={isOptionSelected(option.value)}
											disabled={option.disabled}
											on:click|stopPropagation
											on:change={(e) => handleMultipleChange(option.value, e.target.checked)}
										/>
									{/if}
									<span class="flex-1">{option.label}</span>
								</div>
							{/each}

							{#if filteredOptions.length === 0}
								<div class="p-4 text-center text-gray-400 dark:text-gray-500 text-sm italic">
									{searchQuery ? '没有找到匹配的选项' : '没有可用选项'}
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>
		{:else}
			<!-- 标准select元素 -->
			<select
				bind:this={selectElement}
				id="field-{field.id}"
				class="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg text-base text-gray-900 dark:text-white bg-white dark:bg-gray-800 cursor-pointer transition-all duration-200
					{readonly
					? 'bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 cursor-not-allowed'
					: 'hover:border-gray-300 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-900'}
					{error ? 'border-red-500 ring-4 ring-red-100 dark:ring-red-900' : ''}"
				{readonly}
				disabled={readonly}
				{value}
				on:change={handleChange}
				on:focus={handleFocus}
				on:blur={handleBlur}
			>
				{#if field.placeholder}
					<option value="">{field.placeholder}</option>
				{/if}

				{#each options as option}
					<option value={option.value} disabled={option.disabled} selected={value === option.value}>
						{option.label}
					</option>
				{/each}
			</select>
		{/if}
	</div>

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

<!-- 点击外部关闭下拉框 -->
<svelte:window on:click={() => (isOpen = false)} />
