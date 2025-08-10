<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let field = {};
	export let value = null;
	export let error = '';
	export let readonly = false;

	let inputElement;

	// 处理值变化
	const handleInput = (event) => {
		const newValue = event.target.value;

		if (newValue === '') {
			value = null;
		} else {
			const numValue = parseFloat(newValue);
			if (!isNaN(numValue)) {
				value = numValue;
			}
		}

		dispatch('change', value);
	};

	// 处理步进按钮
	const handleStep = (direction) => {
		if (readonly) return;

		const step = field.validation?.step || 1;
		const min = field.validation?.min;
		const max = field.validation?.max;

		let newValue = (value || 0) + direction * step;

		if (min !== undefined) newValue = Math.max(min, newValue);
		if (max !== undefined) newValue = Math.min(max, newValue);

		// 处理精度
		if (precision > 0) {
			newValue = parseFloat(newValue.toFixed(precision));
		}

		value = newValue;
		dispatch('change', value);
	};

	const handleFocus = () => {
		dispatch('focus');
	};

	const handleBlur = () => {
		dispatch('blur');
	};

	// 键盘事件处理
	const handleKeydown = (event) => {
		if (readonly) return;

		switch (event.key) {
			case 'ArrowUp':
				event.preventDefault();
				handleStep(1);
				break;
			case 'ArrowDown':
				event.preventDefault();
				handleStep(-1);
				break;
		}
	};

	// 获取配置参数
	$: min = field.validation?.min;
	$: max = field.validation?.max;
	$: step = field.validation?.step || 1;
	$: precision = field.props?.precision || 0;
	$: showControls = field.props?.showControls !== false;
	$: prefix = field.props?.prefix || '';
	$: suffix = field.props?.suffix || '';

	// 格式化显示值
	$: displayValue =
		value !== null && value !== undefined
			? precision > 0
				? value.toFixed(precision)
				: value.toString()
			: '';

	// 输入验证
	$: isValid =
		value === null ||
		value === undefined ||
		((min === undefined || value >= min) && (max === undefined || value <= max));
</script>

<div class="number-input-wrapper" class:error={!!error}>
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
		{#if prefix}
			<span class="input-prefix">{prefix}</span>
		{/if}

		<div class="number-input-control" class:has-controls={showControls}>
			<input
				bind:this={inputElement}
				id="field-{field.id}"
				type="number"
				class="number-input"
				class:error={!!error}
				class:invalid={!isValid}
				placeholder={field.placeholder || ''}
				{min}
				{max}
				{step}
				{readonly}
				value={displayValue}
				on:input={handleInput}
				on:focus={handleFocus}
				on:blur={handleBlur}
				on:keydown={handleKeydown}
			/>

			{#if showControls && !readonly}
				<div class="number-controls">
					<button
						type="button"
						class="control-btn control-up"
						disabled={max !== undefined && value !== null && value >= max}
						on:click={() => handleStep(1)}
						tabindex="-1"
					>
						▲
					</button>
					<button
						type="button"
						class="control-btn control-down"
						disabled={min !== undefined && value !== null && value <= min}
						on:click={() => handleStep(-1)}
						tabindex="-1"
					>
						▼
					</button>
				</div>
			{/if}
		</div>

		{#if suffix}
			<span class="input-suffix">{suffix}</span>
		{/if}
	</div>

	{#if !isValid}
		<p class="field-error">
			{#if min !== undefined && max !== undefined}
				值必须在 {min} 到 {max} 之间
			{:else if min !== undefined}
				值不能小于 {min}
			{:else if max !== undefined}
				值不能大于 {max}
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
	.number-input-wrapper {
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
		display: flex;
		align-items: stretch;
		background: white;
		border: 2px solid #e5e7eb;
		border-radius: 0.5rem;
		overflow: hidden;
		transition: all 0.2s ease;
	}

	.input-container:focus-within {
		border-color: #667eea;
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
	}

	.input-container:has(.error) {
		border-color: #ef4444;
		box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
	}

	.input-prefix,
	.input-suffix {
		display: flex;
		align-items: center;
		padding: 0 0.75rem;
		background: #f9fafb;
		color: #6b7280;
		font-size: 0.925rem;
		font-weight: 500;
		border-right: 1px solid #e5e7eb;
		user-select: none;
	}

	.input-suffix {
		border-right: none;
		border-left: 1px solid #e5e7eb;
	}

	.number-input-control {
		display: flex;
		flex: 1;
		position: relative;
	}

	.number-input {
		width: 100%;
		padding: 0.75rem 1rem;
		border: none;
		font-size: 1rem;
		line-height: 1.5;
		color: #374151;
		background: transparent;
		outline: none;
		font-family: inherit;
	}

	.number-input:disabled,
	.number-input[readonly] {
		background: #f9fafb;
		color: #6b7280;
		cursor: not-allowed;
	}

	.has-controls .number-input {
		padding-right: 2.5rem;
	}

	.number-input.invalid {
		color: #dc2626;
	}

	/* Chrome等浏览器隐藏默认的数字输入控件 */
	.number-input::-webkit-outer-spin-button,
	.number-input::-webkit-inner-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}

	.number-input[type='number'] {
		-moz-appearance: textfield;
	}

	/* 自定义数字控制按钮 */
	.number-controls {
		position: absolute;
		right: 0;
		top: 0;
		bottom: 0;
		display: flex;
		flex-direction: column;
		width: 2rem;
	}

	.control-btn {
		flex: 1;
		border: none;
		background: #f9fafb;
		color: #6b7280;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.7rem;
		transition: all 0.15s ease;
		border-left: 1px solid #e5e7eb;
	}

	.control-btn:hover:not(:disabled) {
		background: #f3f4f6;
		color: #374151;
	}

	.control-btn:active:not(:disabled) {
		background: #e5e7eb;
	}

	.control-btn:disabled {
		color: #d1d5db;
		cursor: not-allowed;
	}

	.control-up {
		border-bottom: 1px solid #e5e7eb;
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
		.number-input {
			padding: 0.625rem 0.875rem;
			font-size: 0.925rem;
		}

		.has-controls .number-input {
			padding-right: 2.25rem;
		}

		.number-controls {
			width: 1.75rem;
		}

		.control-btn {
			font-size: 0.65rem;
		}

		.input-prefix,
		.input-suffix {
			padding: 0 0.625rem;
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
	}

	/* 聚焦状态 */
	.number-input:focus {
		outline: none;
	}

	/* 占位符样式 */
	.number-input::placeholder {
		color: #9ca3af;
	}

	/* 错误状态 */
	.input-container:has(.error) .control-btn {
		border-left-color: #ef4444;
		border-bottom-color: #ef4444;
	}

	/* 只读状态 */
	.input-container:has([readonly]) {
		background: #f9fafb;
		border-color: #d1d5db;
	}

	.input-container:has([readonly]) .input-prefix,
	.input-container:has([readonly]) .input-suffix {
		background: #f3f4f6;
		color: #9ca3af;
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

		.input-container {
			background: #1f2937;
			border-color: #374151;
		}

		.number-input {
			color: #f3f4f6;
		}

		.input-prefix,
		.input-suffix {
			background: #111827;
			color: #9ca3af;
			border-color: #374151;
		}

		.control-btn {
			background: #111827;
			color: #9ca3af;
			border-color: #374151;
		}

		.control-btn:hover:not(:disabled) {
			background: #374151;
			color: #d1d5db;
		}

		.number-input:disabled,
		.number-input[readonly] {
			background: #111827;
			color: #6b7280;
		}

		.number-input::placeholder {
			color: #6b7280;
		}
	}
</style>
