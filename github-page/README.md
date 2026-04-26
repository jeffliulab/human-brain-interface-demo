# github-page

Static product showcase site. Built with Astro 5 + MDX + React islands + Tailwind v4.

Deploys to `https://jeffliulab.github.io/human-brain-interface-demo/` via GitHub Actions on push to `main` (paths `github-page/**`).

## Local dev

```bash
cd github-page
npm install
npm run dev      # http://localhost:4321/human-brain-interface-demo/
npm run build    # → dist/
npm run preview  # serve dist/ locally
```

## Content

- Landing: `src/pages/index.astro`
- Product prototype: `src/pages/prototype.astro`
- Architecture: `src/pages/architecture.astro`
- Scenes: `src/content/scenes/*.mdx` rendered via `src/pages/scenes/[slug].astro`
- Docs: `src/content/docs/*.mdx` rendered via `src/pages/docs/[...slug].astro`

All copy is original to this folder. `planning/**` and `anima-intention-action/docs/**` are private reference and must not be published.
