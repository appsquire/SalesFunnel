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

	function statusFor(id: number): StepStatus {
		const key = String(id);
		if (stepStatus[key]) return stepStatus[key];
		if (id === currentStep) return 'in_progress';
		if (id <= maxReached) return 'incomplete';
		return 'not_started';
	}

	/** Step 0 is not persisted as complete; treat intro as done once the user has continued. */
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
			'mb-2 flex items-center gap-2 rounded-md px-2 py-1 text-xs font-bold uppercase tracking-wide';
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
		const base = 'flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold';
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
		const base = 'flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold';
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
		const base = 'flex w-full items-center gap-2.5 rounded-md px-2 py-2 text-left text-sm transition';
		if (isCurrent) {
			return `${base} cursor-default bg-sky-200 font-semibold text-sky-950 shadow-md ring-2 ring-sky-500 ring-offset-1`;
		}
		if (navDisabled) {
			return `${base} cursor-not-allowed text-slate-400 opacity-50`;
		}
		if (st === 'complete') return `${base} font-medium text-green-900 hover:bg-green-50`;
		if (st === 'incomplete') return `${base} text-amber-950 hover:bg-amber-50/80`;
		if (st === 'in_progress') return `${base} text-sky-900 hover:bg-sky-50`;
		return `${base} text-slate-600 hover:bg-slate-50`;
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
	<nav
		id="enrollment-step-nav"
		class="w-64 shrink-0 border-r border-sky-200 bg-gradient-to-b from-sky-50/80 to-white p-4 md:sticky md:top-0 md:h-screen md:overflow-y-auto"
		aria-label="Enrollment progress"
	>
		<p class="mb-5 border-b border-sky-200 pb-3 text-sm font-bold tracking-tight text-sky-900" id="enrollment-step-nav-title">
			UTILITYnet Sign-Up
		</p>
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
				<ul class="mt-1 space-y-0.5 border-l-2 border-sky-200 pl-2 ml-1">
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
								onclick={() => canJump(step.id) && onNavigate(step.id)}
							>
								<span class={stepBadgeClass(st, isCurrent)} aria-hidden="true">{icon(st)}</span>
								<span>{step.label}</span>
							</button>
						</li>
					{/each}
				</ul>
			</div>
		{/each}
	</nav>
{/if}
