export type StepStatus = 'not_started' | 'in_progress' | 'complete' | 'incomplete';

export type StepDef = {
	id: number;
	group: string;
	label: string;
	slug: string;
};

export const ENROLLMENT_STEPS: StepDef[] = [
	{ id: 0, group: 'Start', label: 'Before you begin', slug: 'intro' },
	{ id: 1, group: 'Contact', label: 'Who you are', slug: 'contact-who' },
	{ id: 2, group: 'Contact', label: 'About you', slug: 'contact-about' },
	{ id: 3, group: 'Contact', label: 'Alternate & applicant', slug: 'contact-alt' },
	{ id: 4, group: 'Your plan', label: 'Service date & move', slug: 'plan-date' },
	{ id: 5, group: 'Your plan', label: 'Rate & power', slug: 'plan-rate' },
	{ id: 6, group: 'Your plan', label: 'Add-ons & codes', slug: 'plan-addons' },
	{ id: 7, group: 'Addresses', label: 'Billing address', slug: 'address-billing' },
	{ id: 8, group: 'Addresses', label: 'Service location', slug: 'address-service' },
	{ id: 9, group: 'Review', label: 'Review', slug: 'review' },
	{ id: 10, group: 'Legal', label: 'Agreements', slug: 'legal' },
	{ id: 11, group: 'Payment', label: 'Bank document', slug: 'upload' }
];

export const DRAFT_STORAGE_KEY = 'funnel.enrollment.draft';

export type DraftStorage = {
	draft_uuid: string;
	current_step: number;
	max_step_reached: number;
	updated_at: string;
};

export function stepNavId(stepId: number): string {
	return `enrollment-step-nav-item-${stepId}`;
}
