<script>
	import { onMount, getContext } from 'svelte';
	import { knowledge } from '$lib/stores';
	import { getKnowledgeBases } from '$lib/apis/knowledge';
	import Knowledge from '$lib/components/workspace/Knowledge.svelte';

	const i18n = getContext('i18n');

	onMount(async () => {
		try {
			knowledge.set(await getKnowledgeBases(localStorage.token));
		} catch (error) {
			console.error('Error loading knowledge bases:', error);
		}
	});
</script>

{#if $knowledge !== null}
	<Knowledge />
{:else}
	<div class="w-full h-full flex justify-center items-center">
		<div>Loading...</div>
	</div>
{/if}
