# Kindled Web App

This package contains Kindled's Astro and React browser interface. It loads game-specific parser and analyzer packages from the workspace and performs save analysis locally in the browser.

The app has no upload endpoint and does not send save contents or generated reports to a server.

## Development

From the repository root:

```powershell
pnpm install
pnpm --filter @save-analyzer/web dev
```

The local site is available at `http://localhost:4321` by default.

## Verification

```powershell
pnpm test
pnpm typecheck
pnpm build
```

These root commands run package tests, TypeScript and Astro diagnostics, and the production web build.

## Structure

```text
src/components/      Shared Astro and React UI
src/components/analyzer/  Interactive save-analysis interface
src/data/            Browser-facing game data imports
src/layouts/         Shared page layouts and metadata
src/pages/           Static routes
src/styles/          Global and site-specific styles
public/              Static public assets
```
