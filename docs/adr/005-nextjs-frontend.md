# ADR-005: Next.js for Frontend

**Status:** Accepted  
**Date:** 2026-07-04  
**Deciders:** Spark Engineering

## Context

V1 used a single `index.html` file with hand-rolled JavaScript:
- ~2000 lines of inline JS handling all UI logic
- No component reuse (copy-paste between pages)
- No TypeScript (runtime errors from typos)
- Manual DOM manipulation (no virtual DOM)
- No build step (no minification, no tree-shaking)
- Monaco editor loaded from CDN with manual configuration

## Decision

Use Next.js (App Router) with TypeScript and Tailwind CSS for the frontend.

## Consequences

**Positive:**
- Component-based architecture (reusable FileTree, Terminal, MonacoEditor, etc.)
- TypeScript catches type errors at compile time
- Automatic code splitting and lazy loading
- Built-in routing with App Router
- Tailwind CSS for consistent, maintainable styling
- Server-side rendering capability (future optimization)
- Monaco editor properly configured with TypeScript types

**Negative:**
- Build step required (npm run build)
- Node.js runtime dependency
- Slightly more complex development setup
- Hot reload slower than V1's instant HTML reload

**Mitigations:**
- Dockerfile.web handles build and serving
- Development mode (npm run dev) provides fast HMR
- Static export option for simple deployments
- Build artifacts are small (Next.js optimized)

## Alternatives Considered

1. **Vanilla HTML/JS** — V1 approach, no component reuse
2. **React SPA (CRA/Vite)** — simpler but no SSR, less ecosystem
3. **Vue/Nuxt** — viable but team knows React better
4. **Svelte/SvelteKit** — excellent DX but smaller ecosystem
5. **Remix** — good but Next.js has larger community and tooling
