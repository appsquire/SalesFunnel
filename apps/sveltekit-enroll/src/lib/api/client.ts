export type EnrollmentRecord = {
	draft_uuid: string;
	status: string;
	current_step: number;
	max_step_reached: number;
	step_status: Record<string, string>;
	payload: Record<string, unknown>;
	reference_number?: string | null;
};

export type FunnelConfig = Record<string, unknown>;

export class ApiValidationError extends Error {
	fieldErrors: Record<string, string>;

	constructor(message: string, fieldErrors: Record<string, string>) {
		super(message);
		this.name = 'ApiValidationError';
		this.fieldErrors = fieldErrors;
	}
}

const apiBase = '';

function throwApiError(data: unknown, fallback: string): never {
	if (typeof data === 'object' && data && 'detail' in data) {
		const detail = (data as { detail: unknown }).detail;
		if (typeof detail === 'object' && detail !== null && !Array.isArray(detail)) {
			const d = detail as { message?: string; field_errors?: Record<string, string> };
			if (d.field_errors || d.message) {
				throw new ApiValidationError(
					d.message ?? 'Please fix the errors below.',
					d.field_errors ?? {}
				);
			}
		}
		if (typeof detail === 'string') {
			throw new Error(detail);
		}
	}
	throw new Error(fallback);
}

async function parseJson<T>(res: Response): Promise<T> {
	const text = await res.text();
	let data: unknown = {};
	if (text) {
		try {
			data = JSON.parse(text);
		} catch {
			data = { detail: text };
		}
	}
	if (!res.ok) {
		throwApiError(data, res.statusText);
	}
	return data as T;
}

export async function fetchFunnelConfig(): Promise<FunnelConfig> {
	const res = await fetch(`${apiBase}/api/config/funnel`);
	return parseJson(res);
}

export async function createEnrollment(payload: Record<string, unknown>): Promise<EnrollmentRecord> {
	const res = await fetch(`${apiBase}/api/enrollments`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ step: 1, payload })
	});
	return parseJson(res);
}

export async function getEnrollment(draftUuid: string): Promise<EnrollmentRecord> {
	const res = await fetch(`${apiBase}/api/enrollments/${draftUuid}`);
	return parseJson(res);
}

export async function patchEnrollment(
	draftUuid: string,
	body: {
		step: number;
		payload?: Record<string, unknown>;
		current_step?: number;
		max_step_reached?: number;
		step_status?: Record<string, string>;
	}
): Promise<EnrollmentRecord> {
	const res = await fetch(`${apiBase}/api/enrollments/${draftUuid}`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
	return parseJson(res);
}

export async function submitEnrollment(draftUuid: string): Promise<EnrollmentRecord> {
	const res = await fetch(`${apiBase}/api/enrollments/${draftUuid}/submit`, {
		method: 'POST'
	});
	return parseJson(res);
}

export function validateStep1Client(payload: Record<string, unknown>): Record<string, string> {
	const errors: Record<string, string> = {};
	const first = String(payload.first_name ?? '').trim();
	const last = String(payload.last_name ?? '').trim();
	const email = String(payload.email ?? '').trim();
	const phone = String(payload.primary_phone ?? '').trim();

	if (!first) errors.first_name = 'First name is required.';
	if (!last) errors.last_name = 'Last name is required.';
	if (!email) errors.email = 'Email is required.';
	else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = 'Enter a valid email address.';
	if (!phone) errors.primary_phone = 'Phone is required.';
	else if (phone.replace(/\D/g, '').length < 10) errors.primary_phone = 'Enter at least 10 digits.';

	return errors;
}
