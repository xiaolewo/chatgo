<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let field = {};
	export let value = [];
	export let error = '';
	export let readonly = false;

	// 处理选项变化
	const handleChange = (optionValue, checked) => {
		if (readonly) return;

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

	const handleFocus = () => {
		dispatch('focus');
	};

	const handleBlur = () => {
		dispatch('blur');
	};

	// 全选/取消全选
	const handleSelectAll = () => {
		if (readonly) return;

		const allValues = options.filter((opt) => !opt.disabled).map((opt) => opt.value);
		const isAllSelected = allValues.every((val) => value.includes(val));

		if (isAllSelected) {
			value = value.filter((val) => !allValues.includes(val));
		} else {
			value = [...new Set([...value, ...allValues])];
		}

		dispatch('change', value);
	};

	// 获取配置参数
	$: options = field.options || [];
	$: layout = field.props?.layout || 'vertical'; // vertical, horizontal, grid
	$: columns = field.props?.columns || 2;
	$: showSelectAll = field.props?.showSelectAll || false;
	$: minSelected = field.validation?.minSelected;
	$: maxSelected = field.validation?.maxSelected;

	// 确保value是数组
	$: if (!Array.isArray(value)) {
		value = [];
	}

	// 验证选择数量
	$: isValid =
		(!minSelected || value.length >= minSelected) && (!maxSelected || value.length <= maxSelected);

	// 检查是否全选
	$: availableOptions = options.filter((opt) => !opt.disabled);
	$: isAllSelected =
		availableOptions.length > 0 && availableOptions.every((opt) => value.includes(opt.value));
	$: isIndeterminate = value.length > 0 && !isAllSelected;
</script>

<div class="checkbox-group-wrapper" class:error={!!error}>
	<div class="field-header">
		<label class="field-label">
			{field.label}
			{#if field.required}
				<span class="required-marker">*</span>
			{/if}
		</label>

		{#if showSelectAll && !readonly && options.length > 1}
			<button type="button" class="select-all-btn" on:click={handleSelectAll}>
				{isAllSelected ? '取消全选' : '全选'}
			</button>
		{/if}
	</div>

	{#if field.description}
		<p class="field-description">{field.description}</p>
	{/if}

	<div
		class="checkbox-list {layout}"
		class:readonly
		style={layout === 'grid' ? `--columns: ${columns}` : ''}
	>
		{#if showSelectAll && options.length > 1}
			<label class="checkbox-item select-all-item" class:readonly>
				<input
					type="checkbox"
					class="checkbox-input"
					checked={isAllSelected}
					indeterminate={isIndeterminate}
					disabled={readonly}
					on:change={handleSelectAll}
					on:focus={handleFocus}
					on:blur={handleBlur}
				/>
				<span class="checkbox-custom"></span>
				<span class="checkbox-label">全选</span>
			</label>
		{/if}

		{#each options as option}
			<label class="checkbox-item" class:disabled={option.disabled} class:readonly>
				<input
					type="checkbox"
					class="checkbox-input"
					value={option.value}
					checked={value.includes(option.value)}
					disabled={option.disabled || readonly}
					on:change={(e) => handleChange(option.value, e.target.checked)}
					on:focus={handleFocus}
					on:blur={handleBlur}
				/>
				<span class="checkbox-custom"></span>
				<span class="checkbox-label">{option.label}</span>
				{#if option.description}
					<p class="option-description">{option.description}</p>
				{/if}
			</label>
		{/each}
	</div>

	{#if !isValid}
		<p class="field-error">
			{#if minSelected && maxSelected}
				请选择 {minSelected} 到 {maxSelected} 个选项
			{:else if minSelected}
				至少选择 {minSelected} 个选项
			{:else if maxSelected}
				最多选择 {maxSelected} 个选项
			{/if}
		</p>
	{:else if error}
		<p class="field-error">{error}</p>
	{/if}

	{#if field.helpText && !error && isValid}
		<p class="field-help">{field.helpText}</p>
	{/if}
</div>

<style>
	.checkbox-group-wrapper {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.field-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	.field-label {
		font-size: 0.925rem;
		font-weight: 500;
		color: #374151;
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}

	.required-marker {
		color: #ef4444;
		font-weight: 600;
	}

	.select-all-btn {
		font-size: 0.825rem;
		color: #667eea;
		background: none;
		border: none;
		cursor: pointer;
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		transition: all 0.2s ease;
	}

	.select-all-btn:hover {
		background: #eff6ff;
		color: #4f46e5;
	}

	.field-description {
		font-size: 0.825rem;
		color: #6b7280;
		line-height: 1.4;
		margin: 0;
	}

	.checkbox-list {
		display: flex;
		gap: 0.75rem;
	}

	.checkbox-list.vertical {
		flex-direction: column;
	}

	.checkbox-list.horizontal {
		flex-direction: row;
		flex-wrap: wrap;
		gap: 1rem 2rem;
	}

	.checkbox-list.grid {
		display: grid;
		grid-template-columns: repeat(var(--columns, 2), 1fr);
		gap: 0.75rem;
	}

	.checkbox-list.readonly {
		opacity: 0.7;
	}

	.checkbox-item {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 0.375rem;
		transition: all 0.2s ease;
		user-select: none;
	}

	.checkbox-item:hover:not(.disabled):not(.readonly) {
		background: #f9fafb;
	}

	.checkbox-item.disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.checkbox-item.readonly {
		cursor: default;
	}

	.select-all-item {
		border-bottom: 1px solid #e5e7eb;
		margin-bottom: 0.5rem;
		padding-bottom: 0.75rem;
		font-weight: 500;
	}

	.checkbox-input {
		position: absolute;
		opacity: 0;
		width: 0;
		height: 0;
	}

	.checkbox-custom {
		position: relative;
		width: 1.25rem;
		height: 1.25rem;
		border: 2px solid #d1d5db;
		border-radius: 0.25rem;
		background: white;
		transition: all 0.2s ease;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}

	.checkbox-input:checked + .checkbox-custom {
		background: #667eea;
		border-color: #667eea;
	}

	.checkbox-input:checked + .checkbox-custom::after {
		content: '';
		position: absolute;
		left: 0.25rem;
		top: 0.125rem;
		width: 0.375rem;
		height: 0.625rem;
		border: solid white;
		border-width: 0 2px 2px 0;
		transform: rotate(45deg);
	}

	.checkbox-input:indeterminate + .checkbox-custom {
		background: #667eea;
		border-color: #667eea;
	}

	.checkbox-input:indeterminate + .checkbox-custom::after {
		content: '';
		position: absolute;
		left: 0.1875rem;
		top: 0.4375rem;
		width: 0.625rem;
		height: 2px;
		background: white;
		border-radius: 1px;
		transform: none;
	}

	.checkbox-input:focus + .checkbox-custom {
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
	}

	.checkbox-input:disabled + .checkbox-custom {
		background: #f3f4f6;
		border-color: #d1d5db;
		cursor: not-allowed;
	}

	.checkbox-label {
		flex: 1;
		font-size: 0.925rem;
		color: #374151;
		line-height: 1.4;
	}

	.checkbox-item.disabled .checkbox-label {
		color: #9ca3af;
	}

	.option-description {
		font-size: 0.8rem;
		color: #6b7280;
		line-height: 1.3;
		margin: 0.25rem 0 0 0;
		grid-column: 2;
	}

	.field-error {
		font-size: 0.825rem;
		color: #ef4444;
		margin: 0;
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}

	.field-error::before {
		content: '⚠';
		font-size: 0.875rem;
	}

	.field-help {
		font-size: 0.825rem;
		color: #6b7280;
		line-height: 1.4;
		margin: 0;
	}

	/* 响应式设计 */
	@media (max-width: 768px) {
		.checkbox-list.horizontal {
			flex-direction: column;
			gap: 0.75rem;
		}

		.checkbox-list.grid {
			grid-template-columns: 1fr;
		}

		.field-header {
			flex-direction: column;
			align-items: stretch;
			gap: 0.5rem;
		}

		.select-all-btn {
			align-self: flex-start;
		}

		.checkbox-custom {
			width: 1.125rem;
			height: 1.125rem;
		}

		.checkbox-input:checked + .checkbox-custom::after {
			left: 0.1875rem;
			top: 0.0625rem;
			width: 0.3125rem;
			height: 0.5625rem;
		}

		.checkbox-label {
			font-size: 0.875rem;
		}

		.field-label {
			font-size: 0.875rem;
		}

		.field-description,
		.field-error,
		.field-help {
			font-size: 0.8rem;
		}

		.option-description {
			font-size: 0.775rem;
		}
	}

	/* 深色模式支持 */
	@media (prefers-color-scheme: dark) {
		.field-label {
			color: #f3f4f6;
		}

		.field-description,
		.field-help {
			color: #9ca3af;
		}

		.option-description {
			color: #9ca3af;
		}

		.checkbox-item:hover:not(.disabled):not(.readonly) {
			background: #374151;
		}

		.checkbox-custom {
			background: #1f2937;
			border-color: #4b5563;
		}

		.checkbox-input:checked + .checkbox-custom {
			background: #667eea;
			border-color: #667eea;
		}

		.checkbox-input:disabled + .checkbox-custom {
			background: #111827;
			border-color: #374151;
		}

		.checkbox-label {
			color: #f3f4f6;
		}

		.checkbox-item.disabled .checkbox-label {
			color: #6b7280;
		}

		.select-all-item {
			border-bottom-color: #374151;
		}

		.select-all-btn {
			color: #93c5fd;
		}

		.select-all-btn:hover {
			background: #1e3a8a;
			color: #bfdbfe;
		}
	}
</style>
