import type { FunnelConfig } from '$lib/api/client';

export type HelpEntry = {
	text?: string;
	url?: string;
	url_label?: string;
};

export type HelpRegistry = Record<string, HelpEntry>;

export function helpRegistryFromConfig(config: FunnelConfig | null): HelpRegistry {
	const raw = config?.help;
	if (!raw || typeof raw !== 'object') return {};
	return raw as HelpRegistry;
}

export function getHelpEntry(registry: HelpRegistry, helpId: string): HelpEntry | null {
	const entry = registry[helpId];
	if (!entry || (!entry.text && !entry.url)) return null;
	return entry;
}
