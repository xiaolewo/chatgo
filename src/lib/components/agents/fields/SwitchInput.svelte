<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let field = {};
	export let value = false;
	export let error = '';
	export let readonly = false;

	// 处理值变化
	const handleChange = () => {
		if (readonly) return;
		value = !value;
		dispatch('change', value);
	};

	const handleFocus = () => {
		dispatch('focus');
	};

	const handleBlur = () => {
		dispatch('blur');
	};

	// 键盘操作
	const handleKeydown = (event) => {
		if (event.key === ' ' || event.key === 'Enter') {
			event.preventDefault();
			handleChange();
		}
	};

	// 获取开关尺寸
	$: size = field.props?.size || 'default'; // small, default, large

	// 获取开关文本
	$: checkedText = field.props?.checkedText || '';
	$: uncheckedText = field.props?.uncheckedText || '';

	// 获取开关颜色
	$: color = field.props?.color || 'primary'; // primary, success, warning, danger

	// 确保value是布尔值
	$: booleanValue = Boolean(value);
</script>

<div class="switch-input-wrapper" class:error={!!error}>
	<div class="switch-container">
		<div
			class="switch-control {size} {color}"
			class:checked={booleanValue}
			class:readonly
			class:error={!!error}
			tabindex={readonly ? -1 : 0}
			role="switch"
			aria-checked={booleanValue}
			aria-label={field.label}
			on:click={handleChange}
			on:keydown={handleKeydown}
			on:focus={handleFocus}
			on:blur={handleBlur}
		>
			<div class="switch-track">
				<div class="switch-thumb"></div>
				{#if checkedText || uncheckedText}
					<span class="switch-text">
						{booleanValue ? checkedText : uncheckedText}
					</span>
				{/if}
			</div>
		</div>

		<div class="switch-label-container">
			<label class="field-label" for="switch-{field.id}">
				{field.label}
				{#if field.required}
					<span class="required-marker">*</span>
				{/if}
			</label>

			{#if field.description}
				<p class="field-description">{field.description}</p>
			{/if}
		</div>
	</div>

	{#if error}
		<p class="field-error">{error}</p>
	{/if}

	{#if field.helpText && !error}
		<p class="field-help">{field.helpText}</p>
	{/if}
</div>

<style>
	.switch-input-wrapper {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.switch-container {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.switch-control {
		cursor: pointer;
		transition: all 0.2s ease;
		outline: none;
		border-radius: 9999px;
		flex-shrink: 0;
	}

	.switch-control:focus {
		box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
	}

	.switch-control.readonly {
		cursor: not-allowed;
		opacity: 0.6;
	}

	.switch-control.error:focus {
		box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
	}

	.switch-track {
		position: relative;
		display: flex;
		align-items: center;
		background: #d1d5db;
		border-radius: 9999px;
		transition: all 0.2s ease;
		overflow: hidden;
	}

	.switch-thumb {
		position: absolute;
		background: white;
		border-radius: 50%;
		transition: all 0.2s ease;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
		top: 50%;
		transform: translateY(-50%);
		z-index: 1;
	}

	.switch-text {
		position: absolute;
		font-size: 0.75rem;
		font-weight: 500;
		color: white;
		z-index: 0;
		transition: opacity 0.2s ease;
		white-space: nowrap;
	}

	/* 尺寸变体 */
	.switch-control.small .switch-track {
		width: 2.5rem;
		height: 1.25rem;
		padding: 0.125rem;
	}

	.switch-control.small .switch-thumb {
		width: 1rem;
		height: 1rem;
		left: 0.125rem;
	}

	.switch-control.small.checked .switch-thumb {
		left: 1.375rem;
	}

	.switch-control.default .switch-track {
		width: 3rem;
		height: 1.5rem;
		padding: 0.125rem;
	}

	.switch-control.default .switch-thumb {
		width: 1.25rem;
		height: 1.25rem;
		left: 0.125rem;
	}

	.switch-control.default.checked .switch-thumb {
		left: 1.625rem;
	}

	.switch-control.large .switch-track {
		width: 3.5rem;
		height: 1.75rem;
		padding: 0.125rem;
	}

	.switch-control.large .switch-thumb {
		width: 1.5rem;
		height: 1.5rem;
		left: 0.125rem;
	}

	.switch-control.large.checked .switch-thumb {
		left: 1.875rem;
	}

	/* 颜色变体 */
	.switch-control.primary.checked .switch-track {
		background: #667eea;
	}

	.switch-control.success.checked .switch-track {
		background: #10b981;
	}

	.switch-control.warning.checked .switch-track {
		background: #f59e0b;
	}

	.switch-control.danger.checked .switch-track {
		background: #ef4444;
	}

	/* 带文字的开关 */
	.switch-control.small .switch-text {
		font-size: 0.625rem;
		padding: 0 0.25rem;
	}

	.switch-control.default .switch-text {
		font-size: 0.75rem;
		padding: 0 0.375rem;
	}

	.switch-control.large .switch-text {
		font-size: 0.875rem;
		padding: 0 0.5rem;
	}

	.switch-control.checked .switch-text {
		left: 0.5rem;
	}

	.switch-control:not(.checked) .switch-text {
		right: 0.5rem;
	}

	.switch-label-container {
		flex: 1;
		min-width: 0;
	}

	.field-label {
		font-size: 0.925rem;
		font-weight: 500;
		color: #374151;
		display: flex;
		align-items: center;
		gap: 0.25rem;
		margin-bottom: 0.25rem;
		cursor: pointer;
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

	/* 悬停效果 */
	.switch-control:not(.readonly):hover .switch-track {
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
	}

	.switch-control:not(.readonly):hover .switch-thumb {
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
	}

	/* 禁用状态 */
	.switch-control.readonly .switch-track {
		background: #f3f4f6 !important;
	}

	.switch-control.readonly .switch-thumb {
		background: #e5e7eb;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.switch-control.readonly .switch-text {
		color: #9ca3af;
	}

	/* 响应式设计 */
	@media (max-width: 768px) {
		.switch-container {
			gap: 0.625rem;
		}

		.field-label {
			font-size: 0.875rem;
		}

		.field-description,
		.field-error,
		.field-help {
			font-size: 0.8rem;
		}

		/* 移动端使用较小的开关 */
		.switch-control.default .switch-track {
			width: 2.75rem;
			height: 1.375rem;
		}

		.switch-control.default .switch-thumb {
			width: 1.125rem;
			height: 1.125rem;
		}

		.switch-control.default.checked .switch-thumb {
			left: 1.5rem;
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

		.switch-track {
			background: #4b5563;
		}

		.switch-thumb {
			background: #e5e7eb;
		}

		.switch-control.readonly .switch-track {
			background: #374151 !important;
		}

		.switch-control.readonly .switch-thumb {
			background: #6b7280;
		}
	}
</style>
