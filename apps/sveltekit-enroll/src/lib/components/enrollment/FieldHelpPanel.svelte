<script lang="ts">
	import { getHelpEntry, type HelpRegistry } from '$lib/enrollment/help';
	import type { HelpAnchor } from '$lib/enrollment/helpAnchor';

	type Props = {
		activeHelpId: string | null;
		anchor: HelpAnchor | null;
		registry: HelpRegistry;
		onClose: () => void;
	};

	let { activeHelpId, anchor, registry, onClose }: Props = $props();

	const entry = $derived(activeHelpId ? getHelpEntry(registry, activeHelpId) : null);
	const show = $derived(Boolean(activeHelpId && entry && anchor));

	$effect(() => {
		if (!show) return;
		const onPointerDown = (e: PointerEvent) => {
			const t = e.target;
			if (!(t instanceof Element)) return;
			if (document.getElementById('enrollment-field-help-panel')?.contains(t)) return;
			if (t.closest('[id^="enrollment-help-trigger"]')) return;
			onClose();
		};
		const onKeyDown = (e: KeyboardEvent) => {
			if (e.key === 'Escape') onClose();
		};
		window.addEventListener('pointerdown', onPointerDown, true);
		window.addEventListener('keydown', onKeyDown);
		return () => {
			window.removeEventListener('pointerdown', onPointerDown, true);
			window.removeEventListener('keydown', onKeyDown);
		};
	});
</script>

{#if show && anchor && entry}
	<div
		id="enrollment-field-help-panel"
		class="fixed z-50 w-[min(100vw-1rem,20rem)] max-h-[min(70vh,24rem)] overflow-y-auto rounded-md border border-sky-300 bg-sky-50 px-4 py-3 text-base text-sky-950 shadow-lg sm:text-sm"
		style="top: {anchor.top}px; left: {anchor.left}px;"
		role="dialog"
		aria-modal="false"
		aria-labelledby="enrollment-field-help-panel-title"
	>
		<div class="flex items-start justify-between gap-3">
			<p id="enrollment-field-help-panel-title" class="font-semibold text-sky-900">Help</p>
			<button
				type="button"
				id="enrollment-field-help-close"
				class="shrink-0 rounded border border-sky-300 bg-white px-2 py-0.5 text-xs font-medium text-sky-800 hover:bg-sky-100"
				onclick={onClose}
			>
				Close
			</button>
		</div>
		{#if entry.text}
			<p class="mt-2 max-h-48 overflow-y-auto leading-relaxed" id="enrollment-field-help-text">
				{entry.text}
			</p>
		{/if}
		{#if entry.url}
			<p class="mt-2">
				<a
					id="enrollment-field-help-link"
					class="font-medium text-sky-800 underline hover:text-sky-950"
					href={entry.url}
					target="_blank"
					rel="noopener noreferrer"
				>
					{entry.url_label ?? 'View guide'}
				</a>
			</p>
		{/if}
	</div>
{/if}
