<script lang="ts">
	import { getHelpEntry, type HelpRegistry } from '$lib/enrollment/help';

	export type HelpToggleHandler = (id: string | null, anchorEl?: HTMLElement | null) => void;

	type Props = {
		helpId: string;
		activeHelpId: string | null;
		onHelpToggle: HelpToggleHandler;
		registry?: HelpRegistry;
	};

	let { helpId, activeHelpId, onHelpToggle, registry }: Props = $props();

	const expanded = $derived(activeHelpId === helpId);
	const visible = $derived(!registry || getHelpEntry(registry, helpId) != null);

	function toggle(e: MouseEvent) {
		const btn = e.currentTarget as HTMLElement;
		if (expanded) {
			onHelpToggle(null);
		} else {
			onHelpToggle(helpId, btn);
		}
	}
</script>

{#if visible}
	<button
		type="button"
		id="enrollment-help-trigger-{helpId}"
		class="inline-flex shrink-0 items-center justify-center rounded-full p-2.5 text-sky-700 active:bg-sky-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-1
			{expanded ? 'bg-sky-50' : ''}"
		aria-label="Help for this field"
		aria-expanded={expanded}
		aria-controls="enrollment-field-help-panel"
		onclick={toggle}
	>
		<span
			class="flex h-6 w-6 items-center justify-center rounded-full bg-sky-600 text-[13px] font-bold leading-none text-white shadow-sm
				{expanded ? 'ring-2 ring-sky-300 ring-offset-1' : ''}"
			aria-hidden="true"
		>
			?
		</span>
	</button>
{/if}
