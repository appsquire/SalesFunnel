<script lang="ts">
	import { ENROLLMENT_STEPS, stepNavId, type StepStatus } from '$lib/enrollment/steps';

	type Props = {
		currentStep: number;
		maxReached: number;
		stepStatus: Record<string, StepStatus>;
		onNavigate: (step: number) => void;
		showNav: boolean;
	};

	let { currentStep, maxReached, stepStatus, onNavigate, showNav }: Props = $props();

	let mobileOpen = $state(false);

	const currentStepDef = $derived(ENROLLMENT_STEPS.find((s) => s.id === currentStep));
	const currentStepLabel = $derived(currentStepDef?.label ?? 'Sign-up');

	$effect(() => {
		currentStep;
		mobileOpen = false;
	});

	$effect(() => {
		if (typeof document === 'undefined' || !showNav) return;
		if (mobileOpen) {
			const prev = document.body.style.overflow;
			document.body.style.overflow = 'hidden';
			return () => {
				document.body.style.overflow = prev;
			};
		}
	});

	function statusFor(id: number): StepStatus {
		const key = String(id);
		if (stepStatus[key]) return stepStatus[key];
		if (id === currentStep) return 'in_progress';
		if (id <= maxReached) return 'incomplete';
		return 'not_started';
	}

	function effectiveStatusFor(id: number): StepStatus {
		const st = statusFor(id);
		if (id === 0 && st !== 'complete' && maxReached >= 1) return 'complete';
		return st;
	}

	type GroupStatus = 'complete' | 'in_progress' | 'incomplete' | 'not_started';

	function groupStatus(steps: (typeof ENROLLMENT_STEPS)[number][]): GroupStatus {
		const ids = steps.map((s) => s.id);
		const statuses = ids.map((id) => effectiveStatusFor(id));
		if (statuses.every((s) => s === 'complete')) return 'complete';
		if (ids.includes(currentStep)) return 'in_progress';
		if (statuses.some((s) => s === 'incomplete')) return 'incomplete';
		if (statuses.some((s) => s === 'in_progress')) return 'in_progress';
		if (statuses.some((s) => s !== 'not_started')) return 'incomplete';
		return 'not_started';
	}

	function groupNavId(group: string): string {
		return `enrollment-step-nav-group-${group.toLowerCase().replace(/\s+/g, '-')}`;
	}

	function groupHeaderClass(gs: GroupStatus): string {
		const base =
			'mb-2 flex items-center gap-2 rounded-md px-2 py-1.5 text-xs font-bold uppercase tracking-wide';
		switch (gs) {
			case 'complete':
				return `${base} bg-sky-50 text-sky-900 ring-1 ring-sky-200`;
			case 'in_progress':
				return `${base} bg-sky-100 text-sky-900 ring-1 ring-sky-300`;
			case 'incomplete':
				return `${base} bg-amber-50 text-amber-900 ring-1 ring-amber-200`;
			default:
				return `${base} bg-sky-50 text-sky-800`;
		}
	}

	function groupBadgeClass(gs: GroupStatus): string {
		const base =
			'flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold md:h-5 md:w-5 md:text-[10px]';
		switch (gs) {
			case 'complete':
				return `${base} bg-green-600 text-white`;
			case 'in_progress':
				return `${base} bg-sky-600 text-white`;
			case 'incomplete':
				return `${base} bg-amber-500 text-white`;
			default:
				return `${base} bg-sky-200 text-sky-800`;
		}
	}

	function stepBadgeClass(st: StepStatus, isCurrent: boolean): string {
		const base =
			'flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold md:h-5 md:w-5 md:text-[10px]';
		if (isCurrent) return `${base} bg-sky-700 text-white ring-2 ring-white ring-offset-1 ring-offset-sky-500`;
		switch (st) {
			case 'complete':
				return `${base} bg-green-600 text-white`;
			case 'incomplete':
				return `${base} bg-amber-500 text-white`;
			case 'in_progress':
				return `${base} bg-sky-500 text-white`;
			default:
				return `${base} border border-slate-300 bg-white text-slate-400`;
		}
	}

	function stepRowClass(st: StepStatus, isCurrent: boolean, navDisabled: boolean): string {
		const base =
			'flex w-full min-h-12 items-center gap-3 rounded-md px-3 py-2.5 text-left text-base transition md:min-h-0 md:gap-2.5 md:px-2 md:py-2 md:text-sm';
		if (isCurrent) {
			return `${base} cursor-default bg-sky-200 font-semibold text-sky-950 shadow-md ring-2 ring-sky-500 ring-offset-1`;
		}
		if (navDisabled) {
			return `${base} cursor-not-allowed text-slate-400 opacity-50`;
		}
		if (st === 'complete') return `${base} font-medium text-green-900 active:bg-green-50 md:hover:bg-green-50`;
		if (st === 'incomplete') return `${base} text-amber-950 active:bg-amber-50/80 md:hover:bg-amber-50/80`;
		if (st === 'in_progress') return `${base} text-sky-900 active:bg-sky-50 md:hover:bg-sky-50`;
		return `${base} text-slate-600 active:bg-slate-50 md:hover:bg-slate-50`;
	}

	function isNavDisabled(id: number): boolean {
		if (id === currentStep) return false;
		return !canJump(id);
	}

	function groupIcon(gs: GroupStatus): string {
		switch (gs) {
			case 'complete':
				return '✓';
			case 'incomplete':
				return '!';
			case 'in_progress':
				return '●';
			default:
				return '';
		}
	}

	function canJump(id: number): boolean {
		if (id === currentStep) return false;
		const st = statusFor(id);
		if (id === 0) return true;
		if (st === 'complete' || st === 'incomplete') return true;
		return id <= maxReached;
	}

	function icon(s: StepStatus): string {
		switch (s) {
			case 'complete':
				return '✓';
			case 'incomplete':
				return '!';
			case 'in_progress':
				return '●';
			default:
				return '○';
		}
	}

	function handleNavigate(step: number) {
		if (!canJump(step)) return;
		onNavigate(step);
		mobileOpen = false;
	}

	let groups = $derived.by(() => {
		const map = new Map<string, typeof ENROLLMENT_STEPS>();
		for (const step of ENROLLMENT_STEPS) {
			if (!map.has(step.group)) map.set(step.group, []);
			map.get(step.group)!.push(step);
		}
		return [...map.entries()];
	});
</script>

{#if showNav}
	<div class="contents">
		<div
			class="sticky top-0 z-30 border-b border-sky-200 bg-white px-4 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))] md:hidden"
			id="enrollment-step-nav-mobile-bar"
		>
			<button
				type="button"
				id="enrollment-step-nav-toggle"
				class="flex min-h-12 w-full items-center justify-between gap-3 rounded-lg bg-sky-50 px-4 py-3 text-left ring-1 ring-sky-200 active:bg-sky-100"
				aria-expanded={mobileOpen}
				aria-controls="enrollment-step-nav"
				onclick={() => (mobileOpen = !mobileOpen)}
			>
				<span class="min-w-0 flex-1">
					<span class="block text-xs font-normal text-slate-500">Step {currentStep} of 11</span>
					<span class="block truncate text-sm font-semibold text-sky-950">{currentStepLabel}</span>
				</span>
				<span class="shrink-0 text-sm font-medium text-sky-800" aria-hidden="true">
					{mobileOpen ? 'Close' : 'Steps'}
				</span>
			</button>
		</div>

		{#if mobileOpen}
			<button
				type="button"
				id="enrollment-step-nav-backdrop"
				class="fixed inset-0 z-40 bg-slate-900/50 md:hidden"
				aria-label="Close steps menu"
				onclick={() => (mobileOpen = false)}
			></button>
		{/if}

		<nav
			id="enrollment-step-nav"
			class="fixed inset-y-0 left-0 z-50 flex w-[min(100%,20rem)] flex-col border-r border-sky-200 bg-gradient-to-b from-sky-50/95 to-white p-4 shadow-xl transition-transform duration-200 ease-out
				{mobileOpen ? 'translate-x-0' : '-translate-x-full pointer-events-none'}
				md:pointer-events-auto md:static md:z-auto md:h-screen md:w-64 md:shrink-0 md:translate-x-0 md:overflow-y-auto md:shadow-none"
			aria-label="Enrollment progress"
		>
			<div class="mb-4 flex items-center justify-between gap-2 md:hidden">
				<p class="text-sm font-bold text-sky-900">Your progress</p>
				<button
					type="button"
					id="enrollment-step-nav-close"
					class="min-h-11 min-w-11 rounded-lg border border-sky-300 bg-white px-3 text-sm font-medium text-sky-900 active:bg-sky-50"
					onclick={() => (mobileOpen = false)}
				>
					Close
				</button>
			</div>

			<p
				class="mb-5 hidden border-b border-sky-200 pb-3 text-sm font-bold tracking-tight text-sky-900 md:block"
				id="enrollment-step-nav-title"
			>
				UTILITYnet Sign-Up
			</p>
			<div class="flex-1 overflow-y-auto overscroll-contain pb-[env(safe-area-inset-bottom)]">
				{#each groups as [group, steps] (group)}
					{@const gs = groupStatus(steps)}
					<div class="mb-5" id={groupNavId(group)}>
						<p class={groupHeaderClass(gs)} aria-label="{group} section {gs.replaceAll('_', ' ')}">
							<span class={groupBadgeClass(gs)} aria-hidden="true">
								{#if groupIcon(gs)}
									{groupIcon(gs)}
								{:else}
									·
								{/if}
							</span>
							<span>{group}</span>
						</p>
						<ul class="mt-1 space-y-1 border-l-2 border-sky-200 pl-2 ml-1 md:space-y-0.5">
							{#each steps as step (step.id)}
								{@const st = effectiveStatusFor(step.id)}
								{@const isCurrent = step.id === currentStep}
								{@const navDisabled = isNavDisabled(step.id)}
								<li>
									<button
										type="button"
										id={stepNavId(step.id)}
										class={stepRowClass(st, isCurrent, navDisabled)}
										disabled={navDisabled}
										aria-current={isCurrent ? 'step' : undefined}
										aria-disabled={navDisabled && !isCurrent ? 'true' : undefined}
										onclick={() => handleNavigate(step.id)}
									>
										<span class={stepBadgeClass(st, isCurrent)} aria-hidden="true">{icon(st)}</span>
										<span>{step.label}</span>
									</button>
								</li>
							{/each}
						</ul>
					</div>
				{/each}
			</div>
		</nav>
	</div>
{/if}
