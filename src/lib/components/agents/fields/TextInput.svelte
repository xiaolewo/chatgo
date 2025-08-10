<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	export let field = {};
	export let value = '';
	export let error = '';
	export let readonly = false;

	let inputElement;
	let characterCount = 0;

	// 处理值变化
	const handleInput = (event) => {
		const newValue = event.target.value;
		value = newValue;
		characterCount = newValue.length;
		dispatch('change', newValue);
	};

	const handleFocus = () => {
		dispatch('focus');
	};

	const handleBlur = () => {
		dispatch('blur');
	};

	// 获取最大长度限制
	$: maxLength = field.validation?.maxLength || null;

	// 是否显示字符计数
	$: showCounter = field.props?.showCounter && maxLength;

	// 是否多行文本
	$: multiline = field.props?.multiline || false;

	// 文本框行数
	$: rows = field.props?.rows || 3;

	// 是否自动调整高度
	$: autoResize = field.props?.autoResize && multiline;

	// 更新字符计数
	$: if (value !== undefined) {
		characterCount = String(value).length;
	}

	// 自动调整文本域高度
	const autoResizeTextarea = (element) => {
		if (autoResize && element) {
			element.style.height = 'auto';
			element.style.height = element.scrollHeight + 'px';
		}
	};

	// 处理自动调整高度的输入事件
	const handleAutoResize = (event) => {
		autoResizeTextarea(event.target);
		handleInput(event);
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
		{#if multiline}
			<textarea
				bind:this={inputElement}
				id="field-{field.id}"
				class="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg text-base leading-relaxed text-gray-900 dark:text-white bg-white dark:bg-gray-800 transition-all duration-200 font-inherit resize-none min-h-20 resize-y
					{readonly
					? 'bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 cursor-not-allowed'
					: 'hover:border-gray-300 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-900'}
					{error ? 'border-red-500 ring-4 ring-red-100 dark:ring-red-900' : ''}"
				placeholder={field.placeholder || ''}
				{rows}
				{maxLength}
				{readonly}
				{value}
				on:input={autoResize ? handleAutoResize : handleInput}
				on:focus={handleFocus}
				on:blur={handleBlur}
			></textarea>
		{:else}
			<input
				bind:this={inputElement}
				id="field-{field.id}"
				type="text"
				class="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-600 rounded-lg text-base leading-relaxed text-gray-900 dark:text-white bg-white dark:bg-gray-800 transition-all duration-200 font-inherit
					{readonly
					? 'bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 cursor-not-allowed'
					: 'hover:border-gray-300 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-900'}
					{error ? 'border-red-500 ring-4 ring-red-100 dark:ring-red-900' : ''}"
				placeholder={field.placeholder || ''}
				{maxLength}
				{readonly}
				{value}
				on:input={handleInput}
				on:focus={handleFocus}
				on:blur={handleBlur}
			/>
		{/if}

		{#if showCounter}
			<div
				class="absolute bottom-2 right-3 text-xs font-medium px-2 py-1 rounded bg-white/90 dark:bg-gray-800/90
				{characterCount >= maxLength * 0.9
					? 'text-orange-600 dark:text-orange-400'
					: 'text-gray-500 dark:text-gray-400'}"
			>
				{characterCount}{#if maxLength}/{maxLength}{/if}
			</div>
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
