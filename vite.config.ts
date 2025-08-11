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
					// 将 node_modules 中的包分组
					if (id.includes('node_modules')) {
						// AI 相关的大型库
						if (id.includes('@huggingface/transformers') || id.includes('onnxruntime-web')) {
							return 'ai';
						}
						// 图表库
						if (id.includes('echarts') || id.includes('mermaid')) {
							return 'charts';
						}
						// 编辑器相关
						if (id.includes('@tiptap') || id.includes('codemirror')) {
							return 'editor';
						}
						// Pyodide
						if (id.includes('pyodide')) {
							return 'pyodide';
						}
						// UI 组件库
						if (id.includes('bits-ui') || id.includes('focus-trap')) {
							return 'ui';
						}
						// Svelte 核心
						if (id.includes('svelte') || id.includes('@sveltejs')) {
							return 'vendor';
						}
						// 其他第三方库
						return 'vendor';
					}
				}
			}
		},
		chunkSizeWarningLimit: 1600
	},
	worker: {
		format: 'es'
	}
});
