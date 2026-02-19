<script lang="ts">
	import { onMount } from 'svelte';

	let codeHtml = $state('');
	let loading = $state(true);

	onMount(async () => {
		const { createHighlighter } = await import('shiki');
		const {
			transformerTwoslashPython,
			rendererRichPython,
			renderMarkdown,
			renderMarkdownInline,
		} = await import('twoslash-python');

		const [codeRes, nodesRes] = await Promise.all([
			fetch('./example.py'),
			fetch('./example.nodes.json'),
		]);
		const code = await codeRes.text();
		const nodes = await nodesRes.json();

		// Inline twoslasher that uses pre-generated nodes
		// In production, use createTwoslasherPython() with json_file_path in meta
		const inlineTwoslasher = Object.assign(
			(code: string, _lang?: string, _options?: unknown, _pythonOptions?: unknown) => ({
				code,
				nodes,
			}),
			{ getCacheMap: () => undefined },
		);

		const transformer = transformerTwoslashPython({
			twoslasher: inlineTwoslasher,
			renderer: rendererRichPython({
				renderMarkdown,
				renderMarkdownInline,
			}),
			langs: ['python'],
			filter: (lang) => lang === 'python',
		});

		const highlighter = await createHighlighter({
			themes: ['github-dark', 'github-light'],
			langs: ['python'],
		});

		// Cast needed due to @shikijs/types version mismatch between linked package and example
		codeHtml = highlighter.codeToHtml(code, {
			lang: 'python',
			theme: 'github-dark',
			transformers: [transformer as any],
			meta: {
				json_file_path: 'inline',
				__raw: 'twoslash',
			},
		});

		loading = false;
	});
</script>

<svelte:head>
	<title>Twoslash Python</title>
	<meta name="description" content="Python LSP-powered hover tooltips for Shiki code blocks" />
</svelte:head>

<main>
	<header>
		<h1>Twoslash Python</h1>
		<p class="tagline">
			LSP-powered type information for Python code blocks, built on
			<a href="https://shiki.style/">Shiki</a>.
		</p>
	</header>

	<section>
		<h2>Live Demo</h2>
		<p>Hover over symbols in the code block below to see type signatures and documentation.</p>

		{#if loading}
			<div class="loading">Loading highlighter...</div>
		{:else}
			{@html codeHtml}
		{/if}
	</section>

	<section>
		<h2>Installation</h2>

		<h3>1. Node.js package</h3>
		<pre><code>bun add twoslash-python</code></pre>

		<h3>2. Python CLI (requires Python 3.12+)</h3>
		<pre><code>pip install pytwoslash</code></pre>
	</section>

	<section>
		<h2>How It Works</h2>
		<div class="steps">
			<div class="step">
				<span class="step-num">1</span>
				<div>
					<strong>Generate hover data</strong>
					<p>
						Run <code>pytwoslash</code> on your Python source file. It starts a language server via
						<a href="https://github.com/microsoft/monitors4codegen">multilspy</a>, walks the AST, and
						fetches hover info for each symbol.
					</p>
					<pre><code
							>pytwoslash example.py /path/to/project -o example.nodes.json</code
						></pre>
				</div>
			</div>
			<div class="step">
				<span class="step-num">2</span>
				<div>
					<strong>Configure the Shiki transformer</strong>
					<p>
						Pass the transformer to Shiki. It reads the JSON and injects hover popups into the
						rendered HTML.
					</p>
					<pre><code
							>{`import {
  createTwoslasherPython,
  transformerTwoslashPython,
  rendererRichPython,
  renderMarkdown,
  renderMarkdownInline,
} from 'twoslash-python';

const transformer = transformerTwoslashPython({
  twoslasher: createTwoslasherPython({}),
  renderer: rendererRichPython({
    renderMarkdown,
    renderMarkdownInline,
  }),
  explicitTrigger: true,
  langs: ['python'],
});`}</code
						></pre>
				</div>
			</div>
			<div class="step">
				<span class="step-num">3</span>
				<div>
					<strong>Render your code</strong>
					<p>Use Shiki with the transformer. Point to the generated JSON via metadata.</p>
					<pre><code
							>{`const html = await codeToHtml(code, {
  lang: 'python',
  theme: 'github-dark',
  transformers: [transformer],
  meta: {
    json_file_path: './example.nodes.json',
    __raw: 'twoslash',
  },
});`}</code
						></pre>
				</div>
			</div>
		</div>
	</section>

	<section>
		<h2>Features</h2>
		<ul>
			<li>Type signatures and documentation on hover</li>
			<li>Works with any Python project (uses the real LSP)</li>
			<li>Seamless integration with Shiki themes</li>
			<li>Compatible with VitePress, Astro, SvelteKit, and more</li>
			<li>Pre-generated JSON -- no LSP at runtime</li>
		</ul>
	</section>

	<footer>
		<p>
			<a href="https://github.com/julien-blanchon/twoslash-python">GitHub</a> &middot;
			<a href="https://www.npmjs.com/package/twoslash-python">npm</a> &middot; MIT License
		</p>
	</footer>
</main>

<style>
	:global(body) {
		background: #0d1117;
		color: #e6edf3;
		margin: 0;
		padding: 0;
	}

	main {
		max-width: 800px;
		margin: 0 auto;
		padding: 2rem 1rem 4rem;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}

	header {
		margin-bottom: 2rem;
	}

	h1 {
		font-size: 2rem;
		margin: 0 0 0.5rem;
	}

	.tagline {
		color: #8b949e;
		font-size: 1.1rem;
		margin: 0;
	}

	.tagline a {
		color: #58a6ff;
		text-decoration: none;
	}

	.tagline a:hover {
		text-decoration: underline;
	}

	section {
		margin-top: 2.5rem;
	}

	h2 {
		font-size: 1.4rem;
		margin: 0 0 0.75rem;
		padding-bottom: 0.3rem;
		border-bottom: 1px solid #21262d;
	}

	h3 {
		font-size: 1rem;
		margin: 1rem 0 0.5rem;
		color: #c9d1d9;
	}

	p {
		color: #8b949e;
		line-height: 1.6;
		margin: 0.5rem 0;
	}

	a {
		color: #58a6ff;
		text-decoration: none;
	}

	a:hover {
		text-decoration: underline;
	}

	ul {
		color: #8b949e;
		line-height: 1.8;
		padding-left: 1.5rem;
	}

	code {
		font-family: 'SF Mono', SFMono-Regular, ui-monospace, Menlo, monospace;
		font-size: 0.85em;
		background: #161b22;
		padding: 0.15em 0.4em;
		border-radius: 4px;
	}

	pre {
		background: #161b22;
		border: 1px solid #21262d;
		border-radius: 8px;
		padding: 0.75rem 1rem;
		overflow-x: auto;
		font-size: 0.85rem;
		line-height: 1.5;
	}

	pre code {
		background: none;
		padding: 0;
		border-radius: 0;
	}

	.loading {
		padding: 2rem;
		text-align: center;
		color: #6b7280;
	}

	.steps {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.step {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
	}

	.step-num {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 28px;
		height: 28px;
		background: #58a6ff;
		color: #0d1117;
		border-radius: 50%;
		font-weight: 700;
		font-size: 0.85rem;
		margin-top: 0.1rem;
	}

	.step div {
		flex: 1;
		min-width: 0;
	}

	.step strong {
		color: #e6edf3;
	}

	footer {
		margin-top: 3rem;
		padding-top: 1.5rem;
		border-top: 1px solid #21262d;
		text-align: center;
	}

	footer p {
		color: #6b7280;
		font-size: 0.9rem;
	}

	/* Twoslash styles */
	:global(.twoslash) {
		position: relative;
	}

	:global(.twoslash .twoslash-hover) {
		position: relative;
		border-bottom: 1px dotted rgba(136, 136, 136, 0.4);
		transition: border-color 0.3s;
		cursor: pointer;
	}

	:global(.twoslash .twoslash-hover:hover) {
		border-color: #58a6ff;
	}

	:global(.twoslash .twoslash-popup-container) {
		display: none;
		position: absolute;
		bottom: 100%;
		left: 0;
		z-index: 10;
		padding: 0;
		margin-bottom: 4px;
		border-radius: 6px;
		background: #1c2128;
		border: 1px solid #30363d;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
		max-width: 500px;
		min-width: 200px;
		white-space: normal;
	}

	:global(.twoslash .twoslash-hover:hover > .twoslash-popup-container) {
		display: block;
	}

	:global(.twoslash .twoslash-popup-code) {
		display: block;
		padding: 8px 12px;
		font-size: 0.85em;
		line-height: 1.4;
		white-space: pre-wrap;
		word-break: break-word;
	}

	:global(.twoslash .twoslash-popup-code pre) {
		margin: 0;
		padding: 0;
		background: transparent !important;
	}

	:global(.twoslash .twoslash-popup-docs) {
		padding: 8px 12px;
		border-top: 1px solid #30363d;
		font-size: 0.85em;
		line-height: 1.5;
		color: #8b949e;
	}

	:global(.twoslash .twoslash-popup-docs p) {
		margin: 0;
		color: #8b949e;
	}

	:global(.twoslash-error) {
		text-decoration: wavy underline red;
		text-underline-offset: 3px;
	}

	:global(.shiki) {
		padding: 1rem;
		border-radius: 8px;
		overflow-x: auto;
		font-size: 14px;
		line-height: 1.6;
	}
</style>
