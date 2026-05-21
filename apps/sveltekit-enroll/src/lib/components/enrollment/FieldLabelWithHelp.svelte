<script lang="ts">
	import FieldHelpButton, { type HelpToggleHandler } from './FieldHelpButton.svelte';
	import { getHelpEntry, type HelpRegistry } from '$lib/enrollment/help';

	type Props = {
		label: string;
		required?: boolean;
		helpId?: string;
		activeHelpId: string | null;
		registry: HelpRegistry;
		onHelpToggle: HelpToggleHandler;
	};

	let {
		label,
		required = false,
		helpId,
		activeHelpId,
		registry,
		onHelpToggle
	}: Props = $props();

	const showHelp = $derived(helpId != null && getHelpEntry(registry, helpId) != null);
</script>

<span class="inline-flex flex-wrap items-center gap-1.5">
	{label}
	{#if required}
		<span class="text-red-600" aria-hidden="true">*</span>
	{/if}
	{#if showHelp && helpId}
		<FieldHelpButton {helpId} {registry} {activeHelpId} {onHelpToggle} />
	{/if}
</span>
