export function computeGreenCosts(
	kwhPerMonth: number,
	greenPercent: number,
	chargePerKwh: number
): { year: number; month: number; dayCents: number } {
	const greenKwhYear = kwhPerMonth * 12 * (greenPercent / 100);
	const year = greenKwhYear * chargePerKwh;
	return {
		year: Math.round(year * 100) / 100,
		month: Math.round((year / 12) * 100) / 100,
		dayCents: Math.round((year / 365) * 100)
	};
}

export function minServiceDateIso(minDays: number): string {
	const d = new Date();
	d.setDate(d.getDate() + minDays);
	return d.toISOString().slice(0, 10);
}
