<script>
	import { createEventDispatcher } from 'svelte';

	// 导入表单字段组件
	import TextInput from './fields/TextInput.svelte';
	import SelectInput from './fields/SelectInput.svelte';
	import FileUpload from './fields/FileUpload.svelte';
	import SwitchInput from './fields/SwitchInput.svelte';
	import NumberInput from './fields/NumberInput.svelte';
	import DateInput from './fields/DateInput.svelte';
	import CheckboxGroup from './fields/CheckboxGroup.svelte';
	import RadioGroup from './fields/RadioGroup.svelte';

	const dispatch = createEventDispatcher();

	export let config = {};
	export let data = {};
	export let errors = {};
	export let readonly = false;

	// 字段组件映射
	const fieldComponents = {
		text: TextInput,
		select: SelectInput,
		file: FileUpload,
		switch: SwitchInput,
		number: NumberInput,
		date: DateInput,
		checkbox: CheckboxGroup,
		radio: RadioGroup
	};

	// 处理字段值变化
	const handleFieldChange = (fieldName, value) => {
		data = { ...data, [fieldName]: value };

		// 清除该字段的错误信息
		if (errors[fieldName]) {
			errors = { ...errors };
			delete errors[fieldName];
		}

		dispatch('change', { fieldName, value, data });
	};

	// 处理字段焦点事件
	const handleFieldFocus = (fieldName) => {
		dispatch('focus', { fieldName });
	};

	// 处理字段失焦事件
	const handleFieldBlur = (fieldName) => {
		dispatch('blur', { fieldName });
	};

	// 检查字段是否应该显示
	const shouldShowField = (field) => {
		if (!field.conditionalDisplay) return true;

		const { dependsOn, condition, value } = field.conditionalDisplay;
		const dependentValue = data[dependsOn];

		switch (condition) {
			case 'equals':
				return dependentValue === value;
			case 'not_equals':
				return dependentValue !== value;
			case 'contains':
				return Array.isArray(dependentValue) && dependentValue.includes(value);
			case 'not_empty':
				return dependentValue && dependentValue.length > 0;
			case 'empty':
				return !dependentValue || dependentValue.length === 0;
			default:
				return true;
		}
	};

	// 获取字段样式类
	const getFieldClasses = (field) => {
		let classes = ['form-field'];

		if (field.props?.width) {
			classes.push(`field-width-${field.props.width}`);
		}

		if (field.props?.alignment) {
			classes.push(`field-align-${field.props.alignment}`);
		}

		if (errors[field.name]) {
			classes.push('field-error');
		}

		return classes.join(' ');
	};

	// 响应式更新数据
	$: if (config.fields) {
		// 确保所有字段都有对应的数据项
		config.fields.forEach((field) => {
			if (!(field.name in data) && field.default_value !== undefined) {
				data = { ...data, [field.name]: field.default_value };
			}
		});
	}
</script>

<div class="form-renderer">
	{#if config.title}
		<div class="form-header">
			<h2 class="form-title">{config.title}</h2>
			{#if config.description}
				<p class="form-description">{config.description}</p>
			{/if}
		</div>
	{/if}

	<div class="form-fields" class:readonly>
		{#each config.fields || [] as field (field.name || field.id || field.type + '_' + Math.random())}
			{#if shouldShowField(field)}
				<div class={getFieldClasses(field)}>
					{#if fieldComponents[field.type]}
						<svelte:component
							this={fieldComponents[field.type]}
							{field}
							value={data[field.name]}
							error={errors[field.name]}
							{readonly}
							on:change={(e) => handleFieldChange(field.name, e.detail)}
							on:focus={() => handleFieldFocus(field.name)}
							on:blur={() => handleFieldBlur(field.name)}
						/>
					{:else}
						<div class="unsupported-field">
							<div class="unsupported-icon">⚠️</div>
							<p class="unsupported-message">
								不支持的字段类型: {field.type}
							</p>
						</div>
					{/if}
				</div>
			{/if}
		{/each}
	</div>

	{#if config.layout?.submitButton && !readonly}
		<div class="form-submit">
			<button
				type="submit"
				class="submit-btn {config.layout.submitButton.style || 'primary'}"
				disabled={readonly}
			>
				{config.layout.submitButton.text || '提交'}
			</button>
		</div>
	{/if}

	{#if config.layout?.actions && config.layout.actions.length > 0}
		<div class="form-actions">
			{#each config.layout.actions as action}
				<button
					type="button"
					class="action-btn action-{action.type}"
					on:click={() => dispatch('action', action)}
				>
					{#if action.icon}
						<span class="action-icon">{action.icon}</span>
					{/if}
					{action.text}
				</button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.form-renderer {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	/* 表单头部 */
	.form-header {
		margin-bottom: 1rem;
	}

	.form-title {
		font-size: 1.5rem;
		font-weight: 600;
		color: #374151;
		margin: 0 0 0.5rem 0;
	}

	.form-description {
		color: #6b7280;
		font-size: 1rem;
		line-height: 1.5;
		margin: 0;
	}

	/* 表单字段 */
	.form-fields {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.form-fields.readonly {
		opacity: 0.7;
		pointer-events: none;
	}

	.form-field {
		position: relative;
	}

	/* 字段宽度样式 */
	.field-width-small {
		max-width: 200px;
	}

	.field-width-medium {
		max-width: 400px;
	}

	.field-width-large {
		max-width: 600px;
	}

	.field-width-full {
		width: 100%;
	}

	/* 字段对齐样式 */
	.field-align-left {
		align-self: flex-start;
	}

	.field-align-center {
		align-self: center;
	}

	.field-align-right {
		align-self: flex-end;
	}

	/* 字段错误状态 */
	.field-error {
		/* 错误状态样式在各个字段组件内部处理 */
	}

	/* 不支持的字段类型 */
	.unsupported-field {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1rem;
		background: #fef3c7;
		border: 1px solid #f59e0b;
		border-radius: 0.5rem;
		color: #92400e;
	}

	.unsupported-icon {
		font-size: 1.25rem;
		flex-shrink: 0;
	}

	.unsupported-message {
		font-size: 0.925rem;
		font-weight: 500;
		margin: 0;
	}

	/* 提交按钮 */
	.form-submit {
		display: flex;
		justify-content: flex-end;
		padding-top: 1rem;
		border-top: 1px solid #e5e7eb;
	}

	.submit-btn {
		padding: 0.75rem 2rem;
		border-radius: 0.5rem;
		font-size: 1rem;
		font-weight: 500;
		transition: all 0.2s ease;
		cursor: pointer;
		border: none;
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
	}

	.submit-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.submit-btn.primary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}

	.submit-btn.primary:hover:not(:disabled) {
		background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}

	.submit-btn.secondary {
		background: #f9fafb;
		color: #374151;
		border: 1px solid #e5e7eb;
	}

	.submit-btn.secondary:hover:not(:disabled) {
		background: #f3f4f6;
		border-color: #d1d5db;
	}

	/* 表单动作按钮 */
	.form-actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
		flex-wrap: wrap;
	}

	.action-btn {
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		transition: all 0.2s ease;
		cursor: pointer;
		border: 1px solid transparent;
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: #f9fafb;
		color: #374151;
	}

	.action-btn:hover {
		background: #f3f4f6;
		transform: translateY(-1px);
	}

	.action-favorite {
		color: #dc2626;
	}

	.action-favorite:hover {
		background: #fef2f2;
		border-color: #fca5a5;
	}

	.action-share {
		color: #2563eb;
	}

	.action-share:hover {
		background: #eff6ff;
		border-color: #93c5fd;
	}

	.action-icon {
		font-size: 1rem;
	}

	/* 响应式设计 */
	@media (max-width: 768px) {
		.form-renderer {
			gap: 1.25rem;
		}

		.form-fields {
			gap: 1rem;
		}

		.form-title {
			font-size: 1.25rem;
		}

		.form-submit {
			flex-direction: column;
		}

		.submit-btn {
			width: 100%;
			justify-content: center;
		}

		.form-actions {
			flex-direction: column;
		}

		.action-btn {
			width: 100%;
			justify-content: center;
		}

		/* 移动端字段宽度重置 */
		.field-width-small,
		.field-width-medium,
		.field-width-large {
			max-width: none;
			width: 100%;
		}
	}

	@media (max-width: 480px) {
		.form-title {
			font-size: 1.125rem;
		}

		.form-description {
			font-size: 0.925rem;
		}

		.unsupported-field {
			flex-direction: column;
			text-align: center;
			padding: 0.75rem;
		}
	}

	/* 布局变体 */
	:global(.form-renderer.compact) .form-fields {
		gap: 1rem;
	}

	:global(.form-renderer.compact) .form-field {
		margin-bottom: 0;
	}

	:global(.form-renderer.horizontal) .form-fields {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
	}

	:global(.form-renderer.horizontal) .field-width-small {
		max-width: none;
	}

	:global(.form-renderer.horizontal) .field-width-medium {
		max-width: none;
	}

	/* 表单组分隔 */
	:global(.form-field-group) {
		border: 1px solid #e5e7eb;
		border-radius: 0.5rem;
		padding: 1.5rem;
		margin: 1rem 0;
		background: #fafbfc;
	}

	:global(.form-field-group .group-title) {
		font-size: 1.125rem;
		font-weight: 600;
		color: #374151;
		margin: 0 0 1rem 0;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid #e5e7eb;
	}

	/* 字段间距调整 */
	:global(.form-field + .form-field-group) {
		margin-top: 2rem;
	}

	:global(.form-field-group + .form-field) {
		margin-top: 2rem;
	}
</style>
