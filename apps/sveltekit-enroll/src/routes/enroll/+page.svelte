<script lang="ts">
	import { onMount } from 'svelte';
	import StepNav from '$lib/components/enrollment/StepNav.svelte';
	import FieldHelpPanel from '$lib/components/enrollment/FieldHelpPanel.svelte';
	import FieldHelpButton from '$lib/components/enrollment/FieldHelpButton.svelte';
	import FieldLabelWithHelp from '$lib/components/enrollment/FieldLabelWithHelp.svelte';
	import {
		ApiValidationError,
		createEnrollment,
		fetchFunnelConfig,
		getEnrollment,
		patchEnrollment,
		submitEnrollment,
		validateStep1Client,
		type EnrollmentRecord,
		type FunnelConfig
	} from '$lib/api/client';
	import { clearDraftStorage, readDraftStorage, writeDraftStorage } from '$lib/enrollment/draftStorage';
	import { computeGreenCosts, minServiceDateIso } from '$lib/enrollment/greenCalc';
	import { helpRegistryFromConfig } from '$lib/enrollment/help';
	import { anchorFromElement, type HelpAnchor } from '$lib/enrollment/helpAnchor';
	import type { StepStatus } from '$lib/enrollment/steps';

	let funnelConfig = $state<FunnelConfig | null>(null);
	let loading = $state(true);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let fieldErrors = $state<Record<string, string>>({});
	let record = $state<EnrollmentRecord | null>(null);
	let currentStep = $state(0);
	let maxReached = $state(0);
	let stepStatus = $state<Record<string, StepStatus>>({});
	let payload = $state<Record<string, unknown>>({});
	let incompleteBanner = $state(false);
	let activeHelpId = $state<string | null>(null);
	let helpAnchor = $state<HelpAnchor | null>(null);

	const helpRegistry = $derived(helpRegistryFromConfig(funnelConfig));

	function clearHelp() {
		activeHelpId = null;
		helpAnchor = null;
	}

	function toggleHelp(id: string | null, anchorEl?: HTMLElement | null) {
		if (id === null || id === activeHelpId) {
			clearHelp();
			return;
		}
		activeHelpId = id;
		helpAnchor = anchorEl ? anchorFromElement(anchorEl) : null;
	}

	const showNav = $derived(currentStep >= 1 && record?.status !== 'submitted');

	onMount(async () => {
		try {
			funnelConfig = await fetchFunnelConfig();
			const stored = readDraftStorage();
			if (stored?.draft_uuid) {
				record = await getEnrollment(stored.draft_uuid);
				payload = record.payload ?? {};
				currentStep = stored.current_step ?? record.current_step;
				maxReached = Math.max(stored.max_step_reached ?? 0, record.max_step_reached);
				stepStatus = (record.step_status ?? {}) as Record<string, StepStatus>;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load';
		} finally {
			loading = false;
		}
	});

	function syncStorage() {
		if (!record) return;
		writeDraftStorage({
			draft_uuid: record.draft_uuid,
			current_step: currentStep,
			max_step_reached: maxReached,
			updated_at: new Date().toISOString()
		});
	}

	function updateStatuses(completedStep: number) {
		stepStatus = { ...stepStatus, [String(completedStep)]: 'complete' };
	}

	function clearErrors() {
		error = null;
		fieldErrors = {};
	}

	function clearErrorsAndHelp() {
		clearErrors();
		clearHelp();
	}

	function applyValidationError(e: unknown) {
		if (e instanceof ApiValidationError) {
			error = e.message;
			fieldErrors = e.fieldErrors;
			return;
		}
		error = e instanceof Error ? e.message : 'Something went wrong. Please try again.';
		fieldErrors = {};
	}

	function fieldClass(name: string): string {
		const base =
			'mt-1 w-full rounded border px-3 py-3 text-base min-h-12 sm:py-2 sm:text-sm sm:min-h-[2.5rem]';
		return fieldErrors[name]
			? `${base} border-red-500 ring-1 ring-red-200`
			: `${base} border-slate-300`;
	}

	function selectClass(name?: string): string {
		const base =
			'mt-1 w-full rounded border border-slate-300 px-3 py-3 text-base min-h-12 sm:py-2 sm:text-sm sm:min-h-[2.5rem]';
		if (name && fieldErrors[name]) {
			return `${base} border-red-500 ring-1 ring-red-200`;
		}
		return base;
	}

	async function goContinue() {
		clearErrorsAndHelp();
		saving = true;
		try {
			if (currentStep === 0) {
				currentStep = 1;
				maxReached = Math.max(maxReached, 1);
				syncStorage();
				return;
			}

			if (currentStep === 1 && !record) {
				const clientErrs = validateStep1Client(payload);
				if (Object.keys(clientErrs).length > 0) {
					fieldErrors = clientErrs;
					error = 'Please complete the required fields below.';
					stepStatus = { ...stepStatus, '1': 'incomplete' };
					return;
				}
				record = await createEnrollment({
					first_name: payload.first_name,
					last_name: payload.last_name,
					email: payload.email,
					primary_phone: payload.primary_phone
				});
				payload = record.payload;
				maxReached = 1;
				updateStatuses(1);
				syncStorage();
				currentStep = 2;
				maxReached = 2;
				syncStorage();
				return;
			}

			if (!record) throw new Error('No draft — complete step 1 first');

			const next = Math.min(currentStep + 1, 11);
			record = await patchEnrollment(record.draft_uuid, {
				step: currentStep,
				payload,
				current_step: next,
				max_step_reached: Math.max(maxReached, next),
				step_status: stepStatus
			});
			payload = record.payload;
			updateStatuses(currentStep);
			currentStep = next;
			maxReached = Math.max(maxReached, next);
			syncStorage();
		} catch (e) {
			applyValidationError(e);
			stepStatus = { ...stepStatus, [String(currentStep)]: 'incomplete' };
		} finally {
			saving = false;
		}
	}

	function goBack() {
		if (currentStep <= 0) return;
		clearErrorsAndHelp();
		incompleteBanner = false;
		currentStep -= 1;
		syncStorage();
	}

	function navigate(step: number) {
		if (step === currentStep) return;
		clearErrorsAndHelp();
		incompleteBanner = step >= 10 && !dataStepsComplete();
		currentStep = step;
		syncStorage();
	}

	function dataStepsComplete(): boolean {
		for (let i = 1; i <= 8; i++) {
			if (stepStatus[String(i)] !== 'complete') return false;
		}
		return true;
	}

	async function handleSubmit() {
		if (!record) return;
		saving = true;
		error = null;
		try {
			record = await submitEnrollment(record.draft_uuid);
			clearDraftStorage();
			currentStep = 12;
		} catch (e) {
			applyValidationError(e);
		} finally {
			saving = false;
		}
	}

	const rateLine = $derived(
		(funnelConfig?.rates as { display_line?: string })?.display_line ??
			'Variable Market Price + 0.27 cents/kWh Transaction Fee'
	);

	const minServiceDays = $derived(
		Number((funnelConfig?.branding as { service_date_min_days?: number })?.service_date_min_days ?? 10)
	);
	const serviceDateMin = $derived(minServiceDateIso(minServiceDays));
	const padWithdrawalDays = $derived(
		(funnelConfig?.pad_withdrawal_days as string[] | undefined) ?? []
	);
	const greenPercentages = $derived(
		(funnelConfig?.green_power_percentages as number[] | undefined) ?? [0, 10, 15, 25, 50, 75, 100]
	);
	const greenChargePerKwh = $derived(
		Number((funnelConfig?.branding as { green_charge_per_kwh?: number })?.green_charge_per_kwh ?? 0.0185)
	);
	const greenPreview = $derived.by(() => {
		if (payload.green_power !== 'yes') return null;
		const kwh = Number(payload.example_kwh_per_month ?? 600);
		const pct = Number(payload.green_percentage ?? 0);
		return computeGreenCosts(kwh, pct, greenChargePerKwh);
	});

	function reviewRows(): { label: string; value: string }[] {
		const p = payload;
		const rows: { label: string; value: string }[] = [
			{ label: 'Name', value: `${p.first_name ?? ''} ${p.last_name ?? ''}`.trim() },
			{ label: 'Email', value: String(p.email ?? '') },
			{ label: 'Phone', value: String(p.primary_phone ?? '') },
			{ label: 'Birthday', value: String(p.birthday ?? '') },
			{
				label: 'Applicant',
				value:
					p.applicant_type === 'authorized_representative'
						? 'Authorized representative'
						: 'Customer'
			},
			{ label: 'Service date', value: String(p.requested_service_date ?? '') },
			{
				label: 'Moving',
				value: p.moving_new_location === 'yes' ? 'Yes' : p.moving_new_location === 'no' ? 'No' : ''
			},
			{ label: 'Referral code', value: String(p.referral_code ?? '—') },
			{ label: 'Promotion code', value: String(p.promotion_code ?? '—') },
			{ label: 'AIR MILES', value: String(p.air_miles_number ?? '—') },
			{
				label: 'Green power',
				value:
					p.green_power === 'yes'
						? `Yes (${p.green_percentage ?? 0}%)`
						: p.green_power === 'no'
							? 'No'
							: ''
			},
			{
				label: 'Billing address',
				value: [p.billing_street, p.billing_city, p.billing_postal].filter(Boolean).join(', ')
			}
		];
		if (p.service_same_as_billing === 'yes') {
			rows.push({ label: 'Service location', value: 'Same as billing' });
		} else {
			rows.push({
				label: 'Service location',
				value: [p.service_street, p.service_city, p.service_postal].filter(Boolean).join(', ')
			});
		}
		return rows.filter((r) => r.value);
	}
</script>

{#if loading}
	<p class="p-8 text-slate-600" id="enrollment-loading">Loading…</p>
{:else}
	<div class="flex min-h-screen flex-col md:flex-row">
		<StepNav {currentStep} {maxReached} {stepStatus} {showNav} onNavigate={navigate} />

		<main class="flex min-w-0 flex-1 flex-col" id="enrollment-main">
			<header class="border-b border-slate-200 bg-white px-4 py-4 sm:px-6">
				<h1 class="text-lg font-semibold text-sky-900" id="enrollment-form-title">
					{(funnelConfig?.branding as { form_title?: string })?.form_title ?? 'UTILITYnet Sign-Up Form'}
				</h1>
				<p class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-600" id="enrollment-form-legend">
					<span><span class="text-red-600">*</span> Required</span>
					<span class="inline-flex items-center gap-1">
						<span
							class="inline-flex h-4 w-4 items-center justify-center rounded-full bg-sky-600 text-[10px] font-bold text-white"
							aria-hidden="true"
							>?</span
						>
						Help
					</span>
					<span class="inline-flex items-center gap-1">
						<span
							class="inline-flex h-4 w-4 items-center justify-center rounded-full bg-amber-500 text-[10px] font-bold text-white"
							aria-hidden="true"
							>!</span
						>
						Invalid
					</span>
				</p>
			</header>

			<div class="flex-1 px-4 py-6 sm:px-6 sm:py-8">
				{#if error}
					<div
						class="mb-4 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
						id="enrollment-error"
						role="alert"
					>
						{error}
					</div>
				{/if}

				{#if incompleteBanner}
					<div
						class="mb-4 rounded border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
						id="enrollment-incomplete-banner"
					>
						Some earlier sections are incomplete. You can continue, but submission will stay blocked until
						required fields validate.
					</div>
				{/if}

				{#if currentStep === 0}
					<section id="enrollment-step-0">
						<h2 class="mb-4 text-xl font-medium">
							{(funnelConfig?.branding as { intro_title?: string })?.intro_title ??
								'UTILITYnet Sign-Up Form Information'}
						</h2>
						<h3 class="mb-2 font-medium">Ready to Sign Up?</h3>
						<ul class="mb-6 list-disc space-y-2 pl-5 text-sm text-slate-700">
							<li>Pre-authorized debit information is collected later in the process.</li>
							<li>You authorize a credit check as part of enrollment.</li>
							<li>
								Review our
								<a class="text-sky-700 underline" href="/legal/terms" id="enrollment-intro-terms-link"
									>Terms and Conditions</a
								>
								and
								<a class="text-sky-700 underline" href="/legal/privacy" id="enrollment-intro-privacy-link"
									>Privacy Statement</a
								>.
							</li>
							<li>
								See
								<a class="text-sky-700 underline" href="/legal/faq" id="enrollment-intro-faq-link">FAQ</a>.
							</li>
						</ul>
					</section>
				{:else if currentStep === 1}
					<section id="enrollment-step-1">
						<h2 class="mb-4 text-xl font-medium">Who you are</h2>
						<div class="grid max-w-lg gap-4">
							<label class="block text-sm">
								<span>First name <span class="text-red-600">*</span></span>
								<input
									id="enrollment-first-name"
									class={fieldClass('first_name')}
									aria-invalid={fieldErrors.first_name ? 'true' : undefined}
									bind:value={payload.first_name}
								/>
								{#if fieldErrors.first_name}
									<p id="enrollment-error-first-name" class="mt-1 text-sm text-red-600" role="alert">
										{fieldErrors.first_name}
									</p>
								{/if}
							</label>
							<label class="block text-sm">
								<span>Last name <span class="text-red-600">*</span></span>
								<input
									id="enrollment-last-name"
									class={fieldClass('last_name')}
									aria-invalid={fieldErrors.last_name ? 'true' : undefined}
									bind:value={payload.last_name}
								/>
								{#if fieldErrors.last_name}
									<p id="enrollment-error-last-name" class="mt-1 text-sm text-red-600" role="alert">
										{fieldErrors.last_name}
									</p>
								{/if}
							</label>
							<label class="block text-sm">
								<span>Email <span class="text-red-600">*</span></span>
								<input
									id="enrollment-email"
									type="email"
									class={fieldClass('email')}
									aria-invalid={fieldErrors.email ? 'true' : undefined}
									bind:value={payload.email}
								/>
								{#if fieldErrors.email}
									<p id="enrollment-error-email" class="mt-1 text-sm text-red-600" role="alert">
										{fieldErrors.email}
									</p>
								{/if}
							</label>
							<label class="block text-sm">
								<span>Phone <span class="text-red-600">*</span></span>
								<input
									id="enrollment-primary-phone"
									type="tel"
									class={fieldClass('primary_phone')}
									aria-invalid={fieldErrors.primary_phone ? 'true' : undefined}
									bind:value={payload.primary_phone}
								/>
								{#if fieldErrors.primary_phone}
									<p id="enrollment-error-primary-phone" class="mt-1 text-sm text-red-600" role="alert">
										{fieldErrors.primary_phone}
									</p>
								{/if}
							</label>
						</div>
					</section>
				{:else if currentStep === 2}
					<section id="enrollment-step-2">
						<h2 class="mb-4 text-xl font-medium">About you</h2>
						<div class="grid max-w-lg gap-4">
							<label class="block text-sm">
								<FieldLabelWithHelp
									label="Birthday"
									required
									helpId="account_holder_birth_date"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
								<input
									id="enrollment-birthday"
									type="date"
									class={fieldClass('birthday')}
									bind:value={payload.birthday}
								/>
							</label>
							<label class="block text-sm">
								<FieldLabelWithHelp
									label="Nickname (optional)"
									helpId="nickname"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
								<input
									id="enrollment-nickname"
									maxlength="40"
									class={fieldClass('nickname')}
									bind:value={payload.nickname}
								/>
							</label>
							<label class="block text-sm">
								<span>Phone extension (optional)</span>
								<input
									id="enrollment-phone-extension"
									class={fieldClass('phone_extension')}
									bind:value={payload.phone_extension}
								/>
							</label>
						</div>
					</section>
				{:else if currentStep === 3}
					<section id="enrollment-step-3">
						<h2 class="mb-4 text-xl font-medium">Alternate contact &amp; applicant</h2>
						<fieldset class="mb-6 max-w-lg">
							<legend class="mb-2 text-sm font-medium">
								<FieldLabelWithHelp
									label="Who is completing this application?"
									required
									helpId="applicant_type"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
							</legend>
							<div class="flex flex-col gap-1 text-sm">
								<label class="flex min-h-12 cursor-pointer items-center gap-3 rounded-lg border border-transparent px-2 py-2 active:bg-slate-50">
									<input
										id="enrollment-applicant-type-customer"
										type="radio"
										name="applicant_type"
										value="customer"
										bind:group={payload.applicant_type}
									/>
									I am the customer
								</label>
								<label class="flex min-h-12 cursor-pointer items-center gap-3 rounded-lg border border-transparent px-2 py-2 active:bg-slate-50">
									<input
										id="enrollment-applicant-type-rep"
										type="radio"
										name="applicant_type"
										value="authorized_representative"
										bind:group={payload.applicant_type}
									/>
									I am an authorized representative
								</label>
							</div>
							{#if fieldErrors.applicant_type}
								<p id="enrollment-error-applicant-type" class="mt-2 text-sm text-red-600" role="alert">
									{fieldErrors.applicant_type}
								</p>
							{/if}
						</fieldset>

						{#if payload.applicant_type === 'authorized_representative'}
							<div class="mb-6 grid max-w-lg gap-4">
								<label class="block text-sm">
									<span>Authorized representative details <span class="text-red-600">*</span></span>
									<textarea
										id="enrollment-authorized-rep-details"
										rows="3"
										class={fieldClass('authorized_rep_details')}
										bind:value={payload.authorized_rep_details}
									></textarea>
									{#if fieldErrors.authorized_rep_details}
										<p class="mt-1 text-sm text-red-600" role="alert">{fieldErrors.authorized_rep_details}</p>
									{/if}
								</label>
								<label class="block text-sm">
									<FieldLabelWithHelp
										label="PAD withdrawal day"
										required
										helpId="authorized_rep_pad_day"
										registry={helpRegistry}
										{activeHelpId}
										onHelpToggle={toggleHelp}
									/>
									<select
										id="enrollment-authorized-rep-pad-day"
										class={fieldClass('authorized_rep_pad_day')}
										bind:value={payload.authorized_rep_pad_day}
									>
										<option value="">Select…</option>
										{#each padWithdrawalDays as day (day)}
											<option value={day}>{day}</option>
										{/each}
									</select>
									{#if fieldErrors.authorized_rep_pad_day}
										<p class="mt-1 text-sm text-red-600" role="alert">{fieldErrors.authorized_rep_pad_day}</p>
									{/if}
								</label>
							</div>
						{/if}

						<h3 class="mb-2 text-sm font-medium text-slate-800">
							<FieldLabelWithHelp
								label="Alternate contact (optional)"
								helpId="alternate_contact"
								registry={helpRegistry}
								{activeHelpId}
								onHelpToggle={toggleHelp}
							/>
						</h3>
						<div class="grid max-w-lg gap-4">
							<label class="block text-sm">
								<span>First name</span>
								<input id="enrollment-alternate-first-name" class={fieldClass('alternate_first_name')} bind:value={payload.alternate_first_name} />
							</label>
							<label class="block text-sm">
								<span>Last name</span>
								<input id="enrollment-alternate-last-name" class={fieldClass('alternate_last_name')} bind:value={payload.alternate_last_name} />
							</label>
							<label class="block text-sm">
								<span>Email</span>
								<input id="enrollment-alternate-email" type="email" class={fieldClass('alternate_email')} bind:value={payload.alternate_email} />
							</label>
							<label class="block text-sm">
								<span>Phone</span>
								<input id="enrollment-alternate-phone" type="tel" class={fieldClass('alternate_phone')} bind:value={payload.alternate_phone} />
							</label>
						</div>
					</section>
				{:else if currentStep === 4}
					<section id="enrollment-step-4">
						<h2 class="mb-4 text-xl font-medium">Service date &amp; move</h2>
						<div class="grid max-w-lg gap-4">
							<label class="block text-sm">
								<FieldLabelWithHelp
									label="Requested service date"
									required
									helpId="requested_service_date"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
								<input
									id="enrollment-requested-service-date"
									type="date"
									min={serviceDateMin}
									class={fieldClass('requested_service_date')}
									bind:value={payload.requested_service_date}
								/>
								<p class="mt-1 text-xs text-slate-500">
									Must be at least {minServiceDays} days from today.
								</p>
								{#if fieldErrors.requested_service_date}
									<p id="enrollment-error-service-date" class="mt-1 text-sm text-red-600" role="alert">
										{fieldErrors.requested_service_date}
									</p>
								{/if}
							</label>
							<label class="block text-sm">
								<FieldLabelWithHelp
									label="Are you moving to a new location?"
									required
									helpId="moving_new_location"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
								<select
									id="enrollment-moving-new-location"
									class={fieldClass('moving_new_location')}
									bind:value={payload.moving_new_location}
								>
									<option value="">Select…</option>
									<option value="yes">Yes</option>
									<option value="no">No</option>
								</select>
								{#if fieldErrors.moving_new_location}
									<p class="mt-1 text-sm text-red-600" role="alert">{fieldErrors.moving_new_location}</p>
								{/if}
							</label>
						</div>
					</section>
				{:else if currentStep === 5}
					<section id="enrollment-step-5">
						<h2 class="mb-4 text-xl font-medium">Rate &amp; power</h2>
						<p class="mb-4 rounded bg-slate-100 px-3 py-2 text-sm" id="enrollment-rate-line">{rateLine}</p>
						<label class="mb-4 block text-sm">
							<FieldLabelWithHelp
								label="Does this location currently have power?"
								helpId="location_has_power"
								registry={helpRegistry}
								{activeHelpId}
								onHelpToggle={toggleHelp}
							/>
							<select
								id="enrollment-location-has-power"
								class={selectClass('location_has_power')}
								bind:value={payload.location_has_power}
							>
								<option value="">Select…</option>
								<option value="yes">Yes</option>
								<option value="no">No</option>
							</select>
						</label>
						{#if payload.location_has_power === 'no'}
							<label class="block text-sm">
								<FieldLabelWithHelp
									label="Do you want power at this site? (3–5 business days)"
									helpId="want_power_at_site"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
								<select
									id="enrollment-want-power"
									class={selectClass('want_power_at_site')}
									bind:value={payload.want_power_at_site}
								>
									<option value="">Select…</option>
									<option value="yes">Yes</option>
									<option value="no">No</option>
								</select>
							</label>
						{/if}
						{#if fieldErrors.location_has_power}
							<p id="enrollment-error-location-has-power" class="mt-2 text-sm text-red-600" role="alert">
								{fieldErrors.location_has_power}
							</p>
						{/if}
					</section>
				{:else if currentStep === 6}
					<section id="enrollment-step-6">
						<h2 class="mb-4 text-xl font-medium">Referral, promotion &amp; green power</h2>
						<div class="grid max-w-lg gap-4">
							<label class="block text-sm">
								<FieldLabelWithHelp
									label="Referral code (optional)"
									helpId="referral_code"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
								<input id="enrollment-referral-code" class={fieldClass('referral_code')} bind:value={payload.referral_code} />
							</label>
							<label class="block text-sm">
								<FieldLabelWithHelp
									label="Promotion code (optional)"
									helpId="promotion_code"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
								<input id="enrollment-promotion-code" class={fieldClass('promotion_code')} bind:value={payload.promotion_code} />
							</label>
							<label class="block text-sm">
								<FieldLabelWithHelp
									label="AIR MILES collector number (optional)"
									helpId="air_miles_number"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
								<input id="enrollment-air-miles-number" class={fieldClass('air_miles_number')} bind:value={payload.air_miles_number} />
							</label>
							<label class="block text-sm">
								<FieldLabelWithHelp
									label="Green power"
									required
									helpId="green_power"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
								<select id="enrollment-green-power" class={fieldClass('green_power')} bind:value={payload.green_power}>
									<option value="">Select…</option>
									<option value="yes">Yes</option>
									<option value="no">No</option>
								</select>
								{#if fieldErrors.green_power}
									<p class="mt-1 text-sm text-red-600" role="alert">{fieldErrors.green_power}</p>
								{/if}
							</label>
							{#if payload.green_power === 'yes'}
								<label class="block text-sm">
									<FieldLabelWithHelp
										label="Green power percentage"
										required
										helpId="green_percentage"
										registry={helpRegistry}
										{activeHelpId}
										onHelpToggle={toggleHelp}
									/>
									<select
										id="enrollment-green-percentage"
										class={fieldClass('green_percentage')}
										bind:value={payload.green_percentage}
									>
										<option value="">Select…</option>
										{#each greenPercentages as pct (pct)}
											<option value={pct}>{pct}%</option>
										{/each}
									</select>
									{#if fieldErrors.green_percentage}
										<p class="mt-1 text-sm text-red-600" role="alert">{fieldErrors.green_percentage}</p>
									{/if}
								</label>
								<label class="block text-sm">
									<span>Example kWh per month (for estimate)</span>
									<input
										id="enrollment-example-kwh"
										type="number"
										min="0"
										class={fieldClass('example_kwh_per_month')}
										bind:value={payload.example_kwh_per_month}
									/>
								</label>
								{#if greenPreview}
									<div
										class="rounded border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-900"
										id="enrollment-green-cost-preview"
									>
										Estimated green charge: ${greenPreview.month}/month (${greenPreview.year}/year, about
										{greenPreview.dayCents}¢/day at {(greenChargePerKwh * 100).toFixed(2)}¢/kWh).
									</div>
								{/if}
							{/if}
						</div>
					</section>
				{:else if currentStep === 7}
					<section id="enrollment-step-7">
						<h2 class="mb-4 inline-flex flex-wrap items-center gap-2 text-xl font-medium">
							<span id="enrollment-step-7-title">Billing address</span>
							<FieldHelpButton
								helpId="billing_address"
								registry={helpRegistry}
								{activeHelpId}
								onHelpToggle={toggleHelp}
							/>
						</h2>
						<p class="mb-4 flex flex-wrap gap-3 text-xs">
							<span class="text-slate-600">Address format guides:</span>
							<button
								type="button"
								id="enrollment-help-trigger-civic_address"
								class="text-sky-700 underline hover:text-sky-900"
								onclick={(e) => toggleHelp('civic_address', e.currentTarget as HTMLElement)}
							>
								Civic
							</button>
							<button
								type="button"
								id="enrollment-help-trigger-post_office_box"
								class="text-sky-700 underline hover:text-sky-900"
								onclick={(e) => toggleHelp('post_office_box', e.currentTarget as HTMLElement)}
							>
								PO Box
							</button>
							<button
								type="button"
								id="enrollment-help-trigger-rural_route"
								class="text-sky-700 underline hover:text-sky-900"
								onclick={(e) => toggleHelp('rural_route', e.currentTarget as HTMLElement)}
							>
								Rural route
							</button>
							<button
								type="button"
								id="enrollment-help-trigger-general_delivery"
								class="text-sky-700 underline hover:text-sky-900"
								onclick={(e) => toggleHelp('general_delivery', e.currentTarget as HTMLElement)}
							>
								General delivery
							</button>
						</p>
						<div class="grid max-w-lg gap-4">
							<label class="block text-sm">
								<span>Street address <span class="text-red-600">*</span></span>
								<input id="enrollment-billing-street" class={fieldClass('billing_street')} bind:value={payload.billing_street} />
							</label>
							<label class="block text-sm">
								<span>City <span class="text-red-600">*</span></span>
								<input id="enrollment-billing-city" class={fieldClass('billing_city')} bind:value={payload.billing_city} />
							</label>
							<label class="block text-sm">
								<span>Province</span>
								<input id="enrollment-billing-province" class={fieldClass('billing_province')} bind:value={payload.billing_province} placeholder="AB" />
							</label>
							<label class="block text-sm">
								<FieldLabelWithHelp
									label="Postal code"
									required
									helpId="postal_code"
									registry={helpRegistry}
									{activeHelpId}
									onHelpToggle={toggleHelp}
								/>
								<input id="enrollment-billing-postal" class={fieldClass('billing_postal')} bind:value={payload.billing_postal} />
							</label>
						</div>
					</section>
				{:else if currentStep === 8}
					<section id="enrollment-step-8">
						<h2 class="mb-4 text-xl font-medium" id="enrollment-step-8-title">Service location</h2>
						<p class="mb-4 flex flex-wrap gap-3 text-xs">
							<span class="text-slate-600">Service address guides:</span>
							<button
								type="button"
								id="enrollment-help-trigger-legal_land_description"
								class="text-sky-700 underline hover:text-sky-900"
								onclick={(e) => toggleHelp('legal_land_description', e.currentTarget as HTMLElement)}
							>
								Legal land description
							</button>
							<button
								type="button"
								id="enrollment-help-trigger-land_title"
								class="text-sky-700 underline hover:text-sky-900"
								onclick={(e) => toggleHelp('land_title', e.currentTarget as HTMLElement)}
							>
								Land title
							</button>
						</p>
						<label class="mb-4 flex min-h-12 cursor-pointer items-start gap-3 rounded-lg px-1 py-2 text-sm active:bg-slate-50">
							<input
								id="enrollment-service-same-as-billing"
								type="checkbox"
								class="mt-1 h-5 w-5 shrink-0 rounded border-slate-300"
								checked={payload.service_same_as_billing === 'yes'}
								onchange={(e) => {
									payload.service_same_as_billing = (e.currentTarget as HTMLInputElement).checked
										? 'yes'
										: 'no';
								}}
							/>
							<FieldLabelWithHelp
								label="Service address is the same as billing"
								helpId="service_same_as_billing"
								registry={helpRegistry}
								{activeHelpId}
								onHelpToggle={toggleHelp}
							/>
						</label>
						{#if payload.service_same_as_billing !== 'yes'}
							<div class="grid max-w-lg gap-4">
								<label class="block text-sm">
									<span>Street address <span class="text-red-600">*</span></span>
									<input id="enrollment-service-street" class={fieldClass('service_street')} bind:value={payload.service_street} />
								</label>
								<label class="block text-sm">
									<span>City <span class="text-red-600">*</span></span>
									<input id="enrollment-service-city" class={fieldClass('service_city')} bind:value={payload.service_city} />
								</label>
								<label class="block text-sm">
									<span>Postal code <span class="text-red-600">*</span></span>
									<input id="enrollment-service-postal" class={fieldClass('service_postal')} bind:value={payload.service_postal} />
								</label>
							</div>
						{/if}
						<label class="mt-4 block max-w-lg text-sm">
							<FieldLabelWithHelp
								label="Site ID (optional)"
								helpId="site_id"
								registry={helpRegistry}
								{activeHelpId}
								onHelpToggle={toggleHelp}
							/>
							<input id="enrollment-site-id" class={fieldClass('site_id')} bind:value={payload.site_id} />
						</label>
						<label class="mt-4 block max-w-lg text-sm">
							<FieldLabelWithHelp
								label="Meter number (optional)"
								helpId="meter_number"
								registry={helpRegistry}
								{activeHelpId}
								onHelpToggle={toggleHelp}
							/>
							<input
								id="enrollment-meter-number"
								class={fieldClass('meter_number')}
								bind:value={payload.meter_number}
							/>
						</label>
					</section>
				{:else if currentStep === 9}
					<section id="enrollment-step-9">
						<h2 class="mb-4 text-xl font-medium">Review your application</h2>
						<p class="mb-4 text-sm text-slate-600">
							Confirm the details below before agreements and payment setup.
						</p>
						<dl class="max-w-lg divide-y divide-slate-200 rounded border border-slate-200 text-sm" id="enrollment-review-list">
							{#each reviewRows() as row, i (row.label)}
								<div class="flex flex-col gap-1 border-b border-slate-100 px-3 py-3 last:border-0 sm:grid sm:grid-cols-3 sm:gap-2 sm:py-2">
									<dt class="font-medium text-slate-600">{row.label}</dt>
									<dd class="text-slate-900 sm:col-span-2" id="enrollment-review-{i}">{row.value}</dd>
								</div>
							{/each}
						</dl>
					</section>
				{:else if currentStep === 10}
					<section id="enrollment-step-10">
						<h2 class="mb-4 text-xl font-medium">Agreements</h2>
						<ul class="mb-4 list-disc space-y-1 pl-5 text-sm">
							<li>
								<a class="text-sky-700 underline" href="/legal/terms" id="enrollment-legal-terms-link" target="_blank"
									>Terms and Conditions</a
								>
							</li>
							<li>
								<a class="text-sky-700 underline" href="/legal/privacy" id="enrollment-legal-privacy-link" target="_blank"
									>Privacy Statement</a
								>
							</li>
						</ul>
						<div class="max-w-lg space-y-2 text-base sm:text-sm">
							<label class="flex min-h-12 cursor-pointer items-start gap-3 rounded-lg px-1 py-3 active:bg-slate-50">
								<input
									id="enrollment-disclosure-acknowledged"
									type="checkbox"
									class="mt-0.5 h-5 w-5 shrink-0 rounded border-slate-300"
									checked={payload.disclosure_acknowledged === 'yes'}
									onchange={(e) => {
										payload.disclosure_acknowledged = (e.currentTarget as HTMLInputElement).checked
											? 'yes'
											: 'no';
									}}
								/>
								<span>I have read and agree to the disclosure and terms.</span>
							</label>
							<label class="flex min-h-12 cursor-pointer items-start gap-3 rounded-lg px-1 py-3 active:bg-slate-50">
								<input
									id="enrollment-pad-acknowledged"
									type="checkbox"
									class="mt-0.5 h-5 w-5 shrink-0 rounded border-slate-300"
									checked={payload.pad_acknowledged === 'yes'}
									onchange={(e) => {
										payload.pad_acknowledged = (e.currentTarget as HTMLInputElement).checked ? 'yes' : 'no';
									}}
								/>
								<span>I authorize pre-authorized debit (PAD) as described in the terms.</span>
							</label>
						</div>
					</section>
				{:else if currentStep === 11}
					<section id="enrollment-step-11">
						<h2 class="mb-4 inline-flex flex-wrap items-center gap-2 text-xl font-medium">
							<span id="enrollment-step-11-title">Void cheque / PAD document</span>
							<FieldHelpButton
								helpId="bank_document"
								registry={helpRegistry}
								{activeHelpId}
								onHelpToggle={toggleHelp}
							/>
						</h2>
						<p class="mb-4 max-w-lg text-sm text-slate-600">
							Upload a void cheque or PAD form now, or choose Upload Later (you will receive a link by email).
						</p>
						<label class="mb-4 flex min-h-12 cursor-pointer items-center gap-3 rounded-lg px-1 py-2 text-base active:bg-slate-50 sm:text-sm">
							<input
								id="enrollment-upload-later"
								type="checkbox"
								class="h-5 w-5 shrink-0 rounded border-slate-300"
								checked={payload.upload_later === 'yes'}
								onchange={(e) => {
									payload.upload_later = (e.currentTarget as HTMLInputElement).checked ? 'yes' : 'no';
								}}
							/>
							Upload later
						</label>
						{#if payload.upload_later !== 'yes'}
							<label class="block max-w-lg text-sm">
								<span>Select file</span>
								<input id="enrollment-bank-document" type="file" accept="image/*,.pdf" class="mt-1 block w-full text-sm" />
								<p class="mt-1 text-xs text-slate-500">File upload to server will be wired on submit in a follow-up pass.</p>
							</label>
						{/if}
					</section>
				{:else if currentStep === 12 || record?.status === 'submitted'}
					<section id="enrollment-complete">
						<h2 class="mb-2 text-xl font-medium text-green-800">Application received</h2>
						<p class="text-slate-700">
							Reference number:
							<strong id="enrollment-reference-number">{record?.reference_number}</strong>
						</p>
						<p class="mt-4 text-sm text-slate-600">
							A confirmation email will be sent to {payload.email}. Upload void cheque / PAD if you chose Upload
							Later.
						</p>
					</section>
				{/if}
			</div>

			<footer
				class="sticky bottom-0 z-20 flex gap-3 border-t border-slate-200 bg-white px-4 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:px-6 sm:py-4"
				id="enrollment-actions"
			>
				<button
					type="button"
					id="enrollment-back"
					class="min-h-12 min-w-[44%] flex-1 rounded-lg border border-slate-300 px-4 py-3 text-base font-medium active:bg-slate-50 disabled:opacity-40 sm:min-h-0 sm:py-2 sm:text-sm"
					disabled={currentStep === 0 || saving}
					onclick={goBack}
				>
					Back
				</button>
				{#if record?.status === 'submitted' || currentStep === 12}
					<span class="text-sm text-slate-500">Done</span>
				{:else if currentStep === 11}
					<button
						type="button"
						id="enrollment-submit"
						class="min-h-12 min-w-[44%] flex-1 rounded-lg bg-green-700 px-4 py-3 text-base font-semibold text-white active:bg-green-800 disabled:opacity-50 sm:min-h-0 sm:py-2 sm:text-sm"
						disabled={saving}
						onclick={handleSubmit}
					>
						{saving ? 'Submitting…' : 'Submit application'}
					</button>
				{:else}
					<button
						type="button"
						id="enrollment-continue"
						class="min-h-12 min-w-[44%] flex-1 rounded-lg bg-sky-700 px-4 py-3 text-base font-semibold text-white active:bg-sky-800 disabled:opacity-50 sm:min-h-0 sm:py-2 sm:text-sm"
						disabled={saving}
						onclick={goContinue}
					>
						{saving ? 'Saving…' : 'Continue'}
					</button>
				{/if}
			</footer>
		</main>
	</div>
	{#if currentStep >= 1 && currentStep <= 11}
		<FieldHelpPanel
			activeHelpId={activeHelpId}
			anchor={helpAnchor}
			registry={helpRegistry}
			onClose={clearHelp}
		/>
	{/if}
{/if}
