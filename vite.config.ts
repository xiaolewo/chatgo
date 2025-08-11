import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

import { viteStaticCopy } from 'vite-plugin-static-copy';

// /** @type {import('vite').Plugin} */
// const viteServerConfig = {
// 	name: 'log-request-middleware',
// 	configureServer(server) {
// 		server.middlewares.use((req, res, next) => {
// 			res.setHeader('Access-Control-Allow-Origin', '*');
// 			res.setHeader('Access-Control-Allow-Methods', 'GET');
// 			res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
// 			res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
// 			next();
// 		});
// 	}
// };

export default defineConfig({
	plugins: [
		sveltekit(),
		viteStaticCopy({
			targets: [
				{
					src: 'node_modules/onnxruntime-web/dist/*.jsep.*',

					dest: 'wasm'
				}
			]
		})
	],
	define: {
		APP_VERSION: JSON.stringify(process.env.npm_package_version),
		APP_BUILD_HASH: JSON.stringify(process.env.APP_BUILD_HASH || 'dev-build')
	},
	build: {
		sourcemap: true,
		rollupOptions: {
			output: {
				manualChunks: (id) => {
					// 只对 node_modules 中的大型包进行分割
					if (id.includes('node_modules')) {
						// AI 相关的大型库（最重要的优化）
						if (id.includes('@huggingface/transformers')) return 'ai-transformers';
						if (id.includes('onnxruntime-web')) return 'ai-onnx';

						// 图表库
						if (id.includes('echarts')) return 'charts-echarts';
						if (id.includes('mermaid')) return 'charts-mermaid';

						// Pyodide（大型库）
						if (id.includes('pyodide')) return 'pyodide';

						// 编辑器相关
						if (id.includes('@tiptap')) return 'editor-tiptap';
						if (id.includes('codemirror')) return 'editor-codemirror';

						// Svelte 核心
						if (id.includes('@sveltejs/kit')) return 'svelte-kit';
						if (id.includes('svelte') && !id.includes('@sveltejs')) return 'svelte-core';

						// 其他较大的第三方库
						if (id.includes('prosemirror')) return 'editor-prosemirror';

						// 小的 UI 库不分割，避免过度分割
					}
					// 不返回任何值，让 Vite 自动处理其他模块
				}
			}
		},
		chunkSizeWarningLimit: 1600
	},
	worker: {
		format: 'es'
	}
});
