<script lang="ts">
	export let size = 'md';
</script>

<!-- 整体居中 + 文字两侧圆点布局 -->
<div class="w-full mt-2 mb-2 flex items-center justify-center gap-2 py-1">
	<div class="flex gap-1.5">
		<div class="dot"></div>
		<div class="dot"></div>
		<div class="dot"></div>
	</div>
	<span class="text-sm text-gray-500 dark:text-gray-400">正在思考</span>
	<div class="flex gap-1.5">
		<div class="dot"></div>
		<div class="dot"></div>
		<div class="dot"></div>
	</div>
</div>

<style>
	.dot {
		width: 5px;
		height: 5px;
		border-radius: 50%;
		background: #9ca3af;
		/* 呼吸缩放动画：更适配居中布局，不突兀 */
		animation: breath 1.6s infinite ease-in-out;
	}

	/* 两侧圆点组的动画延迟错开，更自然 */
	/* 左侧第一个圆点组 */
	.dot:nth-child(1 of .flex:nth-child(1) > .dot) {
		animation-delay: 0s;
	}
	.dot:nth-child(2 of .flex:nth-child(1) > .dot) {
		animation-delay: 0.2s;
	}
	.dot:nth-child(3 of .flex:nth-child(1) > .dot) {
		animation-delay: 0.4s;
	}

	/* 右侧第二个圆点组 */
	.dot:nth-child(1 of .flex:nth-child(3) > .dot) {
		animation-delay: 0.1s;
	}
	.dot:nth-child(2 of .flex:nth-child(3) > .dot) {
		animation-delay: 0.3s;
	}
	.dot:nth-child(3 of .flex:nth-child(3) > .dot) {
		animation-delay: 0.5s;
	}

	/* 呼吸缩放动画：比弹跳更柔和，适合居中场景 */
	@keyframes breath {
		0%,
		100% {
			transform: scale(0.8);
			opacity: 0.4;
		}
		50% {
			transform: scale(1.2);
			opacity: 1;
		}
	}

	/* 深色模式适配 */
	:global(.dark) .dot {
		background: #d1d5db;
	}
</style>
