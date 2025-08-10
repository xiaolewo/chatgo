<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let field = {};
	export let value = '';
	export let error = '';
	export let readonly = false;

	// 处理选择变化
	const handleChange = (optionValue) => {
		if (readonly) return;
		value = optionValue;
		dispatch('change', optionValue);
	};

	const handleFocus = () => {
		dispatch('focus');
	};

	const handleBlur = () => {
		dispatch('blur');
	};

	// 键盘导航
	const handleKeydown = (event, optionValue) => {
		if (readonly) return;

		if (event.key === ' ' || event.key === 'Enter') {
			event.preventDefault();
			handleChange(optionValue);
		} else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
			event.preventDefault();
			navigateOptions(event.key === 'ArrowUp' ? -1 : 1);
		}
	};

	// 方向键导航
	const navigateOptions = (direction) => {
		const enabledOptions = options.filter((opt) => !opt.disabled);
		if (enabledOptions.length === 0) return;

		const currentIndex = enabledOptions.findIndex((opt) => opt.value === value);
		let nextIndex = currentIndex + direction;

		if (nextIndex < 0) nextIndex = enabledOptions.length - 1;
		if (nextIndex >= enabledOptions.length) nextIndex = 0;

		handleChange(enabledOptions[nextIndex].value);
	};

	// 获取配置参数
	$: options = field.options || [];
	$: layout = field.props?.layout || 'vertical'; // vertical, horizontal, grid
	$: columns = field.props?.columns || 2;

	// 生成唯一的字段名
	$: fieldName = `radio-${field.id}-${Date.now()}`;
</script>

<div class="radio-group-wrapper" class:error={!!error}>
	<label class="field-label">
		{field.label}
		{#if field.required}
			<span class="required-marker">*</span>
		{/if}
	</label>

	{#if field.description}
		<p class="field-description">{field.description}</p>
	{/if}

	<div
		class="radio-list {layout}"
		class:readonly
		style={layout === 'grid' ? `--columns: ${columns}` : ''}
		role="radiogroup"
		aria-labelledby="field-{field.id}"
	>
		{#each options as option, index}
			<label
				class="radio-item"
				class:disabled={option.disabled}
				class:readonly
				class:selected={value === option.value}
			>
				<input
					type="radio"
					class="radio-input"
					name={fieldName}
					value={option.value}
					checked={value === option.value}
					disabled={option.disabled || readonly}
					on:change={() => handleChange(option.value)}
					on:focus={handleFocus}
					on:blur={handleBlur}
					on:keydown={(e) => handleKeydown(e, option.value)}
				/>
				<span class="radio-custom"></span>
				<div class="radio-content">
					<span class="radio-label">{option.label}</span>
					{#if option.description}
						<p class="option-description">{option.description}</p>
					{/if}
				</div>
			</label>
		{/each}
	</div>

	{#if error}
		<p class="field-error">{error}</p>
	{/if}

	{#if field.helpText && !error}
		<p class="field-help">{field.helpText}</p>
	{/if}
</div>

<style>
	.radio-group-wrapper {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
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

	.field-description {
		font-size: 0.825rem;
		color: #6b7280;
		line-height: 1.4;
		margin: 0;
	}

	.radio-list {
		display: flex;
		gap: 0.75rem;
	}

	.radio-list.vertical {
		flex-direction: column;
	}

	.radio-list.horizontal {
		flex-direction: row;
		flex-wrap: wrap;
		gap: 1rem 2rem;
	}

	.radio-list.grid {
		display: grid;
		grid-template-columns: repeat(var(--columns, 2), 1fr);
		gap: 0.75rem;
	}

	.radio-list.readonly {
		opacity: 0.7;
	}

	.radio-item {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		cursor: pointer;
		padding: 0.75rem;
		border-radius: 0.5rem;
		transition: all 0.2s ease;
		user-select: none;
		border: 2px solid transparent;
		background: #fafbfc;
	}

	.radio-item:hover:not(.disabled):not(.readonly) {
		background: #f3f4f6;
		border-color: #e5e7eb;
	}

	.radio-item.selected {
		background: #eff6ff;
		border-color: #667eea;
	}

	.radio-item.disabled {
		opacity: 0.5;
		cursor: not-allowed;
		background: #f9fafb;
	}

	.radio-item.readonly {
		cursor: default;
	}

	.radio-input {
		position: absolute;
		opacity: 0;
		width: 0;
		height: 0;
	}

	.radio-custom {
		position: relative;
		width: 1.25rem;
		height: 1.25rem;
		border: 2px solid #d1d5db;
		border-radius: 50%;
		background: white;
		transition: all 0.2s ease;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}

	.radio-input:checked + .radio-custom {
		background: white;
		border-color: #667eea;
	}

	.radio-input:checked + .radio-custom::after {
		content: '';
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		width: 0.5rem;
		height: 0.5rem;
		background: #667eea;
		border-radius: 50%;
	}

	.radio-input:focus + .radio-custom {
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
	}

	.radio-input:disabled + .radio-custom {
		background: #f3f4f6;
		border-color: #d1d5db;
		cursor: not-allowed;
	}

	.radio-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.radio-label {
		font-size: 0.925rem;
		color: #374151;
		line-height: 1.4;
		font-weight: 500;
	}

	.radio-item.disabled .radio-label {
		color: #9ca3af;
	}

	.option-description {
		font-size: 0.8rem;
		color: #6b7280;
		line-height: 1.3;
		margin: 0;
	}

	.radio-item.disabled .option-description {
		color: #9ca3af;
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

	/* 紧凑布局变体 */
	:global(.radio-group-compact) .radio-item {
		padding: 0.5rem;
		background: transparent;
		border-color: transparent;
	}

	:global(.radio-group-compact) .radio-item:hover:not(.disabled):not(.readonly) {
		background: #f9fafb;
	}

	:global(.radio-group-compact) .radio-item.selected {
		background: transparent;
		border-color: transparent;
	}

	/* 卡片布局变体 */
	:global(.radio-group-cards) .radio-item {
		border: 2px solid #e5e7eb;
		background: white;
		border-radius: 0.75rem;
		padding: 1rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	:global(.radio-group-cards) .radio-item:hover:not(.disabled):not(.readonly) {
		border-color: #d1d5db;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		transform: translateY(-1px);
	}

	:global(.radio-group-cards) .radio-item.selected {
		border-color: #667eea;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
	}

	/* 响应式设计 */
	@media (max-width: 768px) {
		.radio-list.horizontal {
			flex-direction: column;
			gap: 0.75rem;
		}

		.radio-list.grid {
			grid-template-columns: 1fr;
		}

		.radio-item {
			padding: 0.625rem;
		}

		.radio-custom {
			width: 1.125rem;
			height: 1.125rem;
		}

		.radio-input:checked + .radio-custom::after {
			width: 0.4375rem;
			height: 0.4375rem;
		}

		.radio-label {
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

		:global(.radio-group-cards) .radio-item {
			padding: 0.875rem;
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

		.radio-item {
			background: #374151;
		}

		.radio-item:hover:not(.disabled):not(.readonly) {
			background: #4b5563;
			border-color: #6b7280;
		}

		.radio-item.selected {
			background: #1e3a8a;
			border-color: #667eea;
		}

		.radio-item.disabled {
			background: #1f2937;
		}

		.radio-custom {
			background: #1f2937;
			border-color: #4b5563;
		}

		.radio-input:checked + .radio-custom {
			background: #1f2937;
			border-color: #667eea;
		}

		.radio-input:disabled + .radio-custom {
			background: #111827;
			border-color: #374151;
		}

		.radio-label {
			color: #f3f4f6;
		}

		.radio-item.disabled .radio-label,
		.radio-item.disabled .option-description {
			color: #6b7280;
		}

		:global(.radio-group-compact) .radio-item {
			background: transparent;
		}

		:global(.radio-group-compact) .radio-item:hover:not(.disabled):not(.readonly) {
			background: #374151;
		}

		:global(.radio-group-cards) .radio-item {
			background: #1f2937;
			border-color: #374151;
		}

		:global(.radio-group-cards) .radio-item:hover:not(.disabled):not(.readonly) {
			border-color: #4b5563;
		}
	}
</style>
