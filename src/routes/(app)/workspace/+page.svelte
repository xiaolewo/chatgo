<script>
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	onMount(() => {
		if ($user?.role !== 'admin') {
			// 应用广场和知识库已独立，优先跳转到提示词或工具
			if ($user?.permissions?.workspace?.prompts) {
				goto('/workspace/prompts');
			} else if ($user?.permissions?.workspace?.tools) {
				goto('/workspace/tools');
			} else {
				// 如果用户没有工作台权限，跳转到首页
				goto('/');
			}
		} else {
			// 管理员默认跳转到提示词
			goto('/workspace/prompts');
		}
	});
</script>
