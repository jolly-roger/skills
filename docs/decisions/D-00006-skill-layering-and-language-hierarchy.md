# D-00006: Skill Layering and Language Hierarchy

## Status

Accepted

## Date

2026-11-17

## Context

The repository distributes language-agnostic engineering principles (`pragmatic-functional-programming`), an ECMAScript / JavaScript skill (`javascript`, planned in `P-00006`), and a TypeScript specialization (`typescript`, integrated in `P-00005`).

An audit of `skills/pragmatic-functional-programming/`, `raw-skills/javascript-skill-canonical/`, and `skills/typescript/` shows direct topic intersections across all three:

1. **`pragmatic-functional-programming` and `javascript` intersect** on pure core vs. effectful boundaries, input mutation ownership, validation at trust boundaries, intentional error handling without silent fallbacks, concurrency/cancellation/resource cleanup, and deterministic behavioral testing.
2. **`javascript` and `typescript` intersect** on language and ecosystem guidance that spans general API design, ECMAScript runtime semantics, and TypeScript-specific representation, including:
   - Nullish coalescing (`??`) vs. logical OR (`||`)
   - Parameter objects for optional configuration
   - Error wrapping with `new Error(..., { cause })` and avoiding catch-and-rethrow
   - `Promise.all` and `Promise.allSettled` observable semantics
   - `AbortSignal` cancellation and `Promise.race` timeout vs. abort behavior
   - `return await` behavior inside `try/catch` and `try/finally`
   - Module-boundary conventions, barrel exports, and circular initialization hazards
   - Runtime validation vs. compile-time/JSDoc type erasure at trust boundaries
   - Non-mutating collection operations (e.g., `toSorted()`)

Without an explicit hierarchy, ECMAScript runtime rules risk being duplicated or drifting across `javascript`, `typescript`, and future JavaScript-ecosystem skills (such as host runtimes or UI frameworks).

## Decision

Establish a three-tier skill layering and precedence model for JavaScript and its derived languages, supersets, and runtime/framework environments:

```text
pragmatic-functional-programming  (Tier 1: Universal engineering foundation)
  └─> javascript                  (Tier 2: Canonical ECMAScript runtime & language semantics)
        └─> typescript / host / framework skills  (Tier 3: Static type system, host APIs, UI conventions)
```

1. **Tier 1 — `pragmatic-functional-programming` (Base for all languages):**
   - Authoritative for language-independent engineering decisions: data vs. calculations vs. actions, mutation ownership, trust-boundary placement, error policy, concurrency/cancellation policy, behavioral test scope, API-shape decisions such as when a parameter object improves clarity, and architectural module-boundary decisions such as whether a curated public barrel is appropriate.
   - Applies first to every coding task in any language and takes precedence over lower tiers on shared concerns.

2. **Tier 2 — `javascript` (Base for ECMAScript-derived languages and environments):**
   - Authoritative for ECMAScript language semantics and runtime mechanisms: coercion and equality (`??`, `===`, `Object.is`, `Object.hasOwn`), prototype pollution guards, shallow copy aliasing, `WeakMap`/`WeakSet`, internal slots and `Proxy` receiver checks, array/collection/iterator semantics, `this` binding, `Error.cause`/`AggregateError`, `Promise` combinators, `return await`, `using`/`await using`, async generators, ES module live bindings/TDZ/TLA cycles, and JSDoc erasure vs. runtime checks.
   - Serves as the shared ECMAScript foundation for TypeScript and future JavaScript-based runtime or framework skills.
   - Owns the runtime consequences of module design—including live bindings, evaluation order, temporal dead zones, top-level-await cycles, and circular initialization—but does not decide whether a project should expose a barrel or another public module boundary.

3. **Tier 3 — `typescript` (and future JS-ecosystem specializations):**
   - Authoritative for static type-system modeling, compile-time narrowing, `unknown`/`never`/`satisfies`/`as const`, `import type`, `tsconfig` strictness, type-aware linting, and compile-time type tests.
   - Inherits general engineering principles from `pragmatic-functional-programming` and ECMAScript runtime semantics from `javascript` rather than redefining them.
   - Precedence order on conflict: `pragmatic-functional-programming` > `javascript` > `typescript` (for runtime/ECMAScript semantics), while `typescript` remains authoritative for static type-system rules.
   - Owns TypeScript-specific representation and tooling consequences of upstream decisions, including typing parameter-object contracts, `import type`, compiler module resolution and emission, and type-surface effects of barrels; it does not independently choose the API or module-boundary architecture.

This hierarchy is a contractual dependency enforced through the repository's instruction surfaces rather than installer metadata:

- `AGENTS.md` must activate the tiers in order for TypeScript and other JavaScript-derived work.
- Each dependent skill must declare its upstream prerequisites and precedence before its workflow.
- Dependent-tier references must delegate upstream-owned decisions and semantics instead of carrying independent normative copies.
- Installation continues to distribute all repository skills together; no dependency engine or per-skill metadata is required.

## Alternatives considered

### Keep `javascript` and `typescript` as independent siblings under `pragmatic-functional-programming`

Each skill would independently carry overlapping ECMAScript runtime guidance (such as `??` vs. `||`, `Promise.all` semantics, `return await`, `Error.cause`, and ES module cycles). This was rejected because it duplicates ECMAScript rules across `javascript`, `typescript`, and any future JS-derived runtime or framework skills, increasing maintenance cost and drift risk.

### Merge `javascript` and `typescript` into a single combined skill

Combining both into one skill would force plain JavaScript tasks to load TypeScript compiler, `tsconfig`, and type-level modeling guidance, and would blur the boundary between runtime ECMAScript semantics and static type-system rules. Keeping them layered preserves clean activation for `.js`/`.mjs`/`.cjs`/`.jsx` projects while allowing `.ts`/`.tsx` projects to build on the canonical ECMAScript base.

## Consequences

### Positive

- Establishes a single canonical owner for each layer: general engineering (`pragmatic-functional-programming`), ECMAScript runtime semantics (`javascript`), and static type system (`typescript`).
- Provides a clear extension model for future JavaScript-ecosystem skills (Node.js, browser/DOM, React/JSX, etc.) without duplicating ECMAScript fundamentals.
- Removes duplication from `skills/typescript/references/` through the `P-00006` alignment (e.g., `??` vs. `||`, `Error.cause`, `Promise.all`/`allSettled`, `return await`, and ES module cycles).

### Negative

- TypeScript and other Tier 3 JS-derived skills require awareness of two upstream layers (`pragmatic-functional-programming` and `javascript`) in `AGENTS.md` activation instructions.
- Existing `skills/typescript/` references contain overlapping ECMAScript sections from `P-00005`; `P-00006` must align their activation, prerequisites, and runtime guidance with this hierarchy while preserving TypeScript-specific rules and traceability to the behavior previously documented there.

## Related documents

- [P-00005: TypeScript skill integration](../plans/P-00005-typescript-skill-integration.md)
- [P-00006: JavaScript skill integration](../plans/P-00006-javascript-skill-integration.md)

## Supersedes

None

## Superseded by

None
