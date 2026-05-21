import { error } from '@sveltejs/kit';
import { loadLegalDocument } from '$lib/server/legalContent';
import type { PageServerLoad } from './$types';

/** Legal pages read legacy/*.html directly — no API dependency. */
export const load: PageServerLoad = async ({ params }) => {
	try {
		const doc = loadLegalDocument(params.slug);
		return { doc };
	} catch (e) {
		const message = e instanceof Error ? e.message : 'Failed to load legal content';
		throw error(404, message);
	}
};
