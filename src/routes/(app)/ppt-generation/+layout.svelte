<script>
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user, config, WEBUI_NAME } from '$lib/stores';

	const i18n = getContext('i18n');

	onMount(() => {
		// PPT功能检查在主页面中处理
	});
</script>

<svelte:head>
	<title>{$i18n.t('PPT Generation')} | {$WEBUI_NAME}</title>
</svelte:head>

<div class="min-h-screen w-full flex flex-col bg-white dark:bg-gray-900">
	<slot />
</div>
