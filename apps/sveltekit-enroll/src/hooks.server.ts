import type { HandleServerError } from '@sveltejs/kit';

export const handleError: HandleServerError = ({ error, event }) => {
	console.error(`[${event.url.pathname}]`, error);
	return {
		message: error instanceof Error ? error.message : 'Something went wrong'
	};
};
