<script>
	import { onMount, getContext } from 'svelte';

	const i18n = getContext('i18n');
</script>

<div class="agents-layout">
	<slot />
</div>

<style>
	.agents-layout {
		min-height: 100vh;
		background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
	}
</style>
