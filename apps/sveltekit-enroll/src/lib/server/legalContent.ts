import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as cheerio from 'cheerio';

const LEGACY_DIR = process.env.LEGACY_CONTENT_DIR
	? path.resolve(process.env.LEGACY_CONTENT_DIR)
	: path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../../../legacy');

const SLUG_FILES: Record<string, string> = {
	terms: 'Terms.html',
	faq: 'faq.html',
	privacy: 'privacy.html',
	legal: 'legal.html'
};

export type LegalDocument = {
	slug: string;
	title: string;
	format: 'html';
	body: string;
};

function readLegacy(name: string): string {
	const filePath = path.join(LEGACY_DIR, name);
	if (!fs.existsSync(filePath)) {
		throw new Error(`Legacy file not found: ${filePath}`);
	}
	return fs.readFileSync(filePath, 'utf-8');
}

function stripChrome($: cheerio.CheerioAPI) {
	$('script, link, nav, iframe').remove();
	$('[class*="navbar"]').remove();
}

function rewriteLinks($: cheerio.CheerioAPI) {
	const mapping: Record<string, string> = {
		'/faq.html': '/legal/faq',
		'faq.html': '/legal/faq',
		'/privacy.html': '/legal/privacy',
		'privacy.html': '/legal/privacy',
		'/legal.html': '/legal/legal',
		'legal.html': '/legal/legal'
	};
	$('a[href]').each((_, el) => {
		const href = $(el).attr('href');
		if (href && mapping[href]) {
			$(el).attr('href', mapping[href]);
		}
	});
}

function extractContainer(rawHtml: string): { title: string; html: string } {
	const $ = cheerio.load(rawHtml);
	stripChrome($);
	const col = $('div.col-sm-8').first();
	const container =
		col.length > 0
			? col
			: $('div.container.narrow').first().length > 0
				? $('div.container.narrow').first()
				: $('div.container').first();

	if (container.length === 0) {
		rewriteLinks($);
		const title = $('title').text().trim() || 'Legal';
		return { title, html: $('body').html() ?? rawHtml };
	}

	const fragment = cheerio.load(container.html() ?? '', null, false);
	rewriteLinks(fragment);
	const header = fragment('.txtheader, .terms-title, #terms-summary .terms-title').first();
	let title = 'Legal';
	if (header.length) {
		title = header.text().trim();
	} else if (fragment('#terms-summary').length) {
		title = 'Key Summary of Terms and Conditions';
	}
	return { title, html: fragment.root().html() ?? '' };
}

function extractDisclosure(): { title: string; html: string } {
	const raw = readLegacy('Terms.html');
	const $ = cheerio.load(raw);
	stripChrome($);
	const block = $('#term1005');
	if (!block.length) {
		throw new Error('Disclosure section #term1005 not found in Terms.html');
	}
	const fragment = cheerio.load(block.html() ?? '', null, false);
	rewriteLinks(fragment);
	return {
		title: 'Disclosure Statement to Consumers',
		html: `<div class="legal-legacy disclosure">${fragment.root().html() ?? ''}</div>`
	};
}

export function loadLegalDocument(slug: string): LegalDocument {
	if (slug === 'disclosure') {
		const { title, html } = extractDisclosure();
		return { slug, title, format: 'html', body: html };
	}

	const filename = SLUG_FILES[slug];
	if (!filename) {
		throw new Error(`Unknown legal page: ${slug}`);
	}

	const { title, html } = extractContainer(readLegacy(filename));
	return {
		slug,
		title,
		format: 'html',
		body: `<div class="legal-legacy">${html}</div>`
	};
}
