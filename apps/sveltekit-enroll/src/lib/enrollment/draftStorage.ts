import { DRAFT_STORAGE_KEY, type DraftStorage } from './steps';

export function readDraftStorage(): DraftStorage | null {
	if (typeof localStorage === 'undefined') return null;
	try {
		const raw = localStorage.getItem(DRAFT_STORAGE_KEY);
		if (!raw) return null;
		return JSON.parse(raw) as DraftStorage;
	} catch {
		return null;
	}
}

export function writeDraftStorage(data: DraftStorage): void {
	localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(data));
}

export function clearDraftStorage(): void {
	localStorage.removeItem(DRAFT_STORAGE_KEY);
}
