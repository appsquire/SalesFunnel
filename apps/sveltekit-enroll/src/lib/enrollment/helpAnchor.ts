export type HelpAnchor = {
	top: number;
	left: number;
};

export function anchorFromElement(el: HTMLElement, panelWidth = 320): HelpAnchor {
	const r = el.getBoundingClientRect();
	const gap = 6;
	let left = r.left;
	const maxLeft = window.innerWidth - panelWidth - 8;
	if (left > maxLeft) left = Math.max(8, maxLeft);
	if (left < 8) left = 8;

	return { top: r.bottom + gap, left };
}
