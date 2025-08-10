<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let field = {};
	export let value = '';
	export let error = '';
	export let readonly = false;

	let inputElement;

	// 处理值变化
	const handleInput = (event) => {
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

	// 获取配置参数
	$: format = field.props?.format || 'YYYY-MM-DD';
	$: showTime = field.props?.showTime || false;
	$: min = field.validation?.min;
	$: max = field.validation?.max;

	// 根据配置确定input类型
	$: inputType = showTime ? 'datetime-local' : 'date';

	// 格式化日期显示
	const formatDate = (dateStr) => {
		if (!dateStr) return '';

		try {
			const date = new Date(dateStr);
			if (isNaN(date.getTime())) return dateStr;

			const options = {
				year: 'numeric',
				month: '2-digit',
				day: '2-digit'
			};

			if (showTime) {
				options.hour = '2-digit';
				options.minute = '2-digit';
			}

			return date.toLocaleDateString('zh-CN', options);
		} catch {
			return dateStr;
		}
	};

	// 验证日期范围
	$: isValid = !value || ((!min || value >= min) && (!max || value <= max));
</script>

<div class="date-input-wrapper" class:error={!!error}>
	<label class="field-label" for="field-{field.id}">
		{field.label}
		{#if field.required}
			<span class="required-marker">*</span>
		{/if}
	</label>

	{#if field.description}
		<p class="field-description">{field.description}</p>
	{/if}

	<div class="input-container">
		<input
			bind:this={inputElement}
			id="field-{field.id}"
			type={inputType}
			class="date-input"
			class:error={!!error}
			class:invalid={!isValid}
			placeholder={field.placeholder || ''}
			{min}
			{max}
			{readonly}
			{value}
			on:input={handleInput}
			on:focus={handleFocus}
			on:blur={handleBlur}
		/>

		<div class="date-icon">
			{showTime ? '🕐' : '📅'}
		</div>
	</div>

	{#if !isValid}
		<p class="field-error">
			{#if min && max}
				日期必须在 {formatDate(min)} 到 {formatDate(max)} 之间
			{:else if min}
				日期不能早于 {formatDate(min)}
			{:else if max}
				日期不能晚于 {formatDate(max)}
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
	.date-input-wrapper {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.field-label {
		font-size: 0.925rem;
		font-weight: 500;
		color: #374151;
		display: flex;
		align-items: center;
		gap: 0.25rem;
		margin-bottom: 0.25rem;
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

	.input-container {
		position: relative;
		display: flex;
		align-items: center;
	}

	.date-input {
		width: 100%;
		padding: 0.75rem 3rem 0.75rem 1rem;
		border: 2px solid #e5e7eb;
		border-radius: 0.5rem;
		font-size: 1rem;
		line-height: 1.5;
		color: #374151;
		background: white;
		transition: all 0.2s ease;
		font-family: inherit;
	}

	.date-input:focus {
		outline: none;
		border-color: #667eea;
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
	}

	.date-input:disabled,
	.date-input[readonly] {
		background: #f9fafb;
		border-color: #d1d5db;
		color: #6b7280;
		cursor: not-allowed;
	}

	.date-input.error {
		border-color: #ef4444;
		box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
	}

	.date-input.error:focus {
		border-color: #dc2626;
		box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
	}

	.date-input.invalid {
		border-color: #f59e0b;
		color: #d97706;
	}

	.date-icon {
		position: absolute;
		right: 0.75rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 1.25rem;
		color: #9ca3af;
		pointer-events: none;
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

	/* 日期输入框的自定义样式 */
	.date-input::-webkit-calendar-picker-indicator {
		position: absolute;
		right: 0.75rem;
		width: 1.25rem;
		height: 1.25rem;
		cursor: pointer;
		opacity: 0;
	}

	/* Firefox日期输入框样式 */
	.date-input[type='date']::-moz-focus-inner {
		border: 0;
		padding: 0;
	}

	/* 占位符样式 */
	.date-input::placeholder {
		color: #9ca3af;
	}

	/* 响应式设计 */
	@media (max-width: 768px) {
		.date-input {
			padding: 0.625rem 2.75rem 0.625rem 0.875rem;
			font-size: 0.925rem;
		}

		.date-icon {
			right: 0.625rem;
			font-size: 1.125rem;
		}

		.field-label {
			font-size: 0.875rem;
		}

		.field-description,
		.field-error,
		.field-help {
			font-size: 0.8rem;
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

		.date-input {
			background: #1f2937;
			border-color: #374151;
			color: #f3f4f6;
		}

		.date-input:focus {
			border-color: #667eea;
			box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
		}

		.date-input:disabled,
		.date-input[readonly] {
			background: #111827;
			border-color: #4b5563;
			color: #9ca3af;
		}

		.date-icon {
			color: #6b7280;
		}

		.date-input::placeholder {
			color: #6b7280;
		}
	}

	/* 日期格式提示 */
	.date-input:not(:focus):not([value]):after {
		content: attr(placeholder);
		position: absolute;
		left: 1rem;
		color: #9ca3af;
		pointer-events: none;
	}

	/* 无效日期状态 */
	.date-input:invalid {
		border-color: #f59e0b;
	}

	/* 日期选择器打开时的样式 */
	.date-input::-webkit-calendar-picker-indicator:hover {
		background: rgba(0, 0, 0, 0.1);
		border-radius: 50%;
	}
</style>
