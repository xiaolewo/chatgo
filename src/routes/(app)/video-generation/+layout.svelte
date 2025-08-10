<script>
	import { onMount, getContext } from 'svelte';
	import { page } from '$app/stores';
	import { user } from '$lib/stores';

	const i18n = getContext('i18n');
</script>

<svelte:head>
	<title>
		{$i18n.t('Video Generation')} • OpenWebUI
	</title>
</svelte:head>

<div class="h-screen max-h-[100dvh] w-full flex flex-col">
	<div class="px-4 pt-3 mt-2">
		
	</div>

	<div class="flex-1 overflow-auto">
		<slot />
	</div>
</div>