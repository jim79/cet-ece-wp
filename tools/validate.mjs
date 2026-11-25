// Validate WordPress block markup the same way the block editor does.
// Usage: node validate.mjs file1.html file2.php ...
import { JSDOM } from 'jsdom';
import fs from 'node:fs';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://localhost/' });
const g = globalThis;
for (const k of ['window', 'document', 'navigator', 'Node', 'HTMLElement', 'Element', 'DOMParser', 'MutationObserver', 'getComputedStyle', 'CustomEvent', 'Event', 'KeyboardEvent', 'MouseEvent', 'requestAnimationFrame', 'cancelAnimationFrame', 'localStorage', 'sessionStorage', 'matchMedia']) {
	if (!(k in g) || g[k] === undefined) {
		try { g[k] = dom.window[k]; } catch (e) {}
	}
}
g.window.matchMedia = g.window.matchMedia || (() => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} }));
g.matchMedia = g.window.matchMedia;
g.requestAnimationFrame = g.requestAnimationFrame || ((cb) => setTimeout(cb, 0));
g.cancelAnimationFrame = g.cancelAnimationFrame || ((id) => clearTimeout(id));
g.ResizeObserver = g.ResizeObserver || class { observe() {} unobserve() {} disconnect() {} };
g.IntersectionObserver = g.IntersectionObserver || class { observe() {} unobserve() {} disconnect() {} };

import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const blocks = require('@wordpress/blocks');
const lib = require('@wordpress/block-library');
lib.registerCoreBlocks();

// Our dynamic blocks: comment-only, register as dynamic so they parse.
const custom = ['news', 'copyright', 'faculty-directory', 'faculty-details', 'lab-list', 'lab-details', 'staff-advisors', 'publications', 'research-areas', 'tech-staff', 'faculty-card', 'last-updated', 'projects', 'research-figures'];
for (const n of custom) {
	blocks.registerBlockType('cet-ece/' + n, { apiVersion: 3, title: n, category: 'widgets', attributes: { type: { type: 'string' }, limit: { type: 'number' }, area: { type: 'string' }, designation: { type: 'string' }, programme: { type: 'string' }, showFilters: { type: 'boolean' }, order: { type: 'string' } }, save: () => null });
}

let bad = 0;
function walk(list, file) {
	for (const b of list) {
		let ok = b.isValid !== false, vIssues = b.validationIssues || [];
		if (b.name && b.name !== 'core/missing' && b.originalContent !== undefined && !b.name.startsWith('cet-ece/')) {
			const r = blocks.validateBlock(b);
			ok = r[0]; vIssues = r[1] || [];
		}
		if (b.name && !ok) {
			bad++;
			console.log(`INVALID ${file}: ${b.name}`);
			const issues = vIssues.map((i) => i.args ? i.args.map(String).join(' | ').slice(0, 900) : String(i)).join('\n   ');
			console.log('   ' + issues);
		}
		if (b.name === 'core/missing') { bad++; console.log(`MISSING ${file}: ${b.attributes.originalName}`); }
		if (b.innerBlocks) walk(b.innerBlocks, file);
	}
}
for (const f of process.argv.slice(2)) {
	let src = fs.readFileSync(f, 'utf8');
	if (f.endsWith('.php')) src = src.replace(/<\?php[\s\S]*?\?>/g, '');
	const parsed = blocks.parse(src);
	walk(parsed, f);
}
console.log(bad ? `${bad} problem(s)` : 'All blocks valid');
process.exit(bad ? 1 : 0);
