<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const doc = $derived(data.doc);
</script>

<article class="mx-auto max-w-4xl px-6 py-10" id="legal-page">
	<h1 class="mb-6 text-2xl font-semibold text-sky-900" id="legal-page-title">{doc.title}</h1>
	<div class="legal-content" id="legal-page-body">
		{@html doc.body}
	</div>
	<p class="mt-10 border-t border-slate-200 pt-6">
		<a href="/enroll" id="legal-back-to-enroll" class="text-sky-700 underline">Back to sign-up</a>
		<span class="mx-2 text-slate-400">·</span>
		<a href="/legal/privacy" id="legal-link-privacy" class="text-sky-700 underline">Privacy</a>
		<span class="mx-2 text-slate-400">·</span>
		<a href="/legal/faq" id="legal-link-faq" class="text-sky-700 underline">FAQ</a>
		<span class="mx-2 text-slate-400">·</span>
		<a href="/legal/legal" id="legal-link-legal" class="text-sky-700 underline">Legal notices</a>
	</p>
</article>

<style>
	:global(.legal-content) {
		font-size: 0.875rem;
		line-height: 1.5;
		color: rgb(51 65 85);
	}
	:global(.legal-content .txtheader) {
		font-size: 1.75rem;
		font-weight: 600;
		margin: 1.5rem 0 1rem;
	}
	:global(.legal-content .terms-title) {
		font-weight: 700;
		margin: 0.75rem 0;
	}
	:global(.legal-content .terms-center) {
		text-align: center;
	}
	:global(.legal-content .terms-bold) {
		font-weight: 700;
	}
	:global(.legal-content .termscontainer) {
		margin-bottom: 0.75rem;
	}
	:global(.legal-content .terms-number) {
		display: inline-block;
		min-width: 2rem;
		font-weight: 600;
		vertical-align: top;
	}
	:global(.legal-content .terms-text) {
		display: inline-block;
		width: calc(100% - 2.5rem);
		vertical-align: top;
	}
	:global(.legal-content a) {
		color: rgb(3 105 161);
		text-decoration: underline;
	}
	:global(.legal-content .panel-body) {
		padding: 0.75rem 0;
	}
	:global(.legal-content .faqpanel-group .panel-title a) {
		color: inherit;
	}
</style>
