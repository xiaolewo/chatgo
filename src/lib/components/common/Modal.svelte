<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { fade } from 'svelte/transition';

	import { flyAndScale } from '$lib/utils/transitions';
	import * as FocusTrap from 'focus-trap';
	export let show = true;
	export let size = 'md';
	export let containerClassName = 'p-3';
	export let className = 'bg-white dark:bg-gray-900 rounded-2xl';

	let modalElement = null;
	let mounted = false;
	let timeoutId = null;
	// Create focus trap to trap user tabs inside modal
	// https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html
	// https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html
	let focusTrap: FocusTrap.FocusTrap | null = null;

	const sizeToWidth = (size) => {
		if (size === 'full') {
			return 'w-full';
		}
		if (size === 'xs') {
			return 'w-[16rem]';
		} else if (size === 'sm') {
			return 'w-[30rem]';
		} else if (size === 'md') {
			return 'w-[42rem]';
		} else {
			return 'w-[56rem]';
		}
	};

	const handleKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Escape' && isTopModal()) {
			console.log('Escape');
			show = false;
		}
	};

	const isTopModal = () => {
		if (!modalElement) return false;
		const modals = document.getElementsByClassName('modal');
		return modals.length && modals[modals.length - 1] === modalElement;
	};

	onMount(() => {
		mounted = true;
	});

	$: if (show && modalElement && mounted) {
		// Clear any existing timeout
		if (timeoutId) {
			clearTimeout(timeoutId);
			timeoutId = null;
		}

		document.body.appendChild(modalElement);
		// Add a small delay to ensure content is fully rendered before activating focus trap
		timeoutId = setTimeout(() => {
			// Check if modalElement still exists and is in DOM
			if (!modalElement || !document.body.contains(modalElement) || !show) {
				return;
			}

			try {
				// 先聚焦到modal容器本身，避免自动聚焦到输入框
				modalElement.focus();

				if (!focusTrap) {
					focusTrap = FocusTrap.createFocusTrap(modalElement, {
						allowOutsideClick: true,
						fallbackFocus: modalElement,
						initialFocus: modalElement, // 明确指定聚焦到modal容器
						clickOutsideDeactivates: true,
						escapeDeactivates: true,
						returnFocusOnDeactivate: true
					});
				}
				focusTrap.activate();
			} catch (error) {
				console.warn('Focus trap activation failed:', error);
				// Continue without focus trap if it fails
				// 如果focus trap失败，至少确保modal是可访问的
				if (modalElement && modalElement.setAttribute) {
					modalElement.setAttribute('tabindex', '-1');
					modalElement.focus();
				}
			}
		}, 50); // 增加延迟确保内容完全渲染
		window.addEventListener('keydown', handleKeyDown);
		document.body.style.overflow = 'hidden';
	} else if (modalElement && !show) {
		// Clear timeout if modal is closing
		if (timeoutId) {
			clearTimeout(timeoutId);
			timeoutId = null;
		}

		if (focusTrap) {
			try {
				focusTrap.deactivate();
				focusTrap = null;
			} catch (error) {
				console.warn('Focus trap deactivation failed:', error);
			}
		}
		window.removeEventListener('keydown', handleKeyDown);
		if (modalElement && document.body.contains(modalElement)) {
			document.body.removeChild(modalElement);
		}
		document.body.style.overflow = 'unset';
	}

	onDestroy(() => {
		show = false;

		// Clear any pending timeouts
		if (timeoutId) {
			clearTimeout(timeoutId);
			timeoutId = null;
		}

		if (focusTrap) {
			try {
				focusTrap.deactivate();
				focusTrap = null;
			} catch (error) {
				console.warn('Focus trap deactivation failed during destroy:', error);
			}
		}
		window.removeEventListener('keydown', handleKeyDown);
		if (modalElement && document.body.contains(modalElement)) {
			try {
				document.body.removeChild(modalElement);
			} catch (error) {
				console.warn('Failed to remove modal element during destroy:', error);
			}
		}
		document.body.style.overflow = 'unset';
	});
</script>

{#if show}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div
		bind:this={modalElement}
		aria-modal="true"
		role="dialog"
		tabindex="-1"
		class="modal fixed top-0 right-0 left-0 bottom-0 bg-black/60 w-full h-screen max-h-[100dvh] {containerClassName} flex items-start justify-center z-9999 overflow-y-auto overscroll-contain outline-none"
		in:fade={{ duration: 10 }}
		on:mousedown={() => {
			show = false;
		}}
	>
		<div
			class="w-full max-w-full {sizeToWidth(size)} {size !== 'full'
				? 'mx-2'
				: ''} min-h-fit {className}"
			in:flyAndScale
			on:mousedown={(e) => {
				e.stopPropagation();
			}}
		>
			<slot />
		</div>
	</div>
{/if}

<style>
	.modal-content {
		animation: scaleUp 0.1s ease-out forwards;
	}

	@keyframes scaleUp {
		from {
			transform: scale(0.985);
			opacity: 0;
		}
		to {
			transform: scale(1);
			opacity: 1;
		}
	}
</style>
