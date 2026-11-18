# P-00006: JavaScript Skill Integration

## Status

Implemented

## Date

2026-11-17

## Objective

Integrate the canonical JavaScript skill staged in `raw-skills/javascript-skill-canonical/` as a first-class library skill (`skills/javascript/`) that is automatically distributed to workspaces and activated for ECMAScript / JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`) and JSDoc-typed JavaScript work, and as the ECMAScript prerequisite for TypeScript / TSX and future JavaScript-ecosystem specializations.

Per [D-00006](../decisions/D-00006-skill-layering-and-language-hierarchy.md), `javascript` serves as Tier 2 in the repository's skill hierarchy (`pragmatic-functional-programming` -> `javascript` -> `typescript` and future JS-ecosystem skills): `pragmatic-functional-programming` remains foundational and authoritative for general decisions about trust boundaries, mutation ownership, error policy, concurrency, cleanup, and behavioral testing, while `javascript` is the canonical owner of ECMAScript runtime semantics and mechanisms (runtime boundary validation, object/collection ownership, error chains, async lifecycles, and ES modules) for JavaScript and its derived languages and environments.

## Scope

- Add `skills/javascript/` with `SKILL.md` and the six ECMAScript reference files from `raw-skills/javascript-skill-canonical/javascript/references/`:
  - `values-and-validation.md`
  - `objects-and-collections.md`
  - `functions-and-errors.md`
  - `async-and-lifecycle.md`
  - `modules-and-boundaries.md`
  - `verification-and-contracts.md`
- Adapt the canonical entrypoint and references so ECMAScript-specific semantics and mechanisms are preserved without independently restating general rules owned by `pragmatic-functional-programming`.
- Adapt `raw-skills/javascript-skill-canonical/AGENTS.example.md` into a `## JavaScript Rules` section in the authoritative `AGENTS.md`, and update `## TypeScript Rules` so TypeScript and TSX tasks load `pragmatic-functional-programming`, `javascript`, and `typescript` in tier order.
- Align `skills/typescript/SKILL.md` and its references with D-00006: declare `javascript` as the required ECMAScript prerequisite, delegate overlapping runtime semantics to the canonical JavaScript references, and preserve TypeScript-specific static type-system guidance.
- Require semantic alignment of both `skills/javascript/` and the updated `skills/typescript/` with their respective origins in `raw-skills/` (`raw-skills/javascript-skill-canonical/` and `raw-skills/typescript-skill/` via `P-00005`), accounting for every original item as retained, delegated across tiers, or intentionally excluded with rationale.
- Document the new skill in `skills/README.md` and the root `README.md`.
- Extend `tests/test_install.py` to verify installation, manifest tracking, excluded staging files, and internal relative Markdown links for `skills/javascript/`.
- Run the full test suite (`python3 -m unittest discover tests`) and verify repeatability and clean `raw-skills/` state.

## Non-goals

- Change the installer (`tools/install.py`) or uninstaller (`tools/uninstall.py`) architecture.
- Add JavaScript/Node.js runtime code, packages, linters, or test runners to this repository.
- Copy `raw-skills/javascript-skill-canonical/AGENTS.example.md` into `skills/javascript/`.
- Modify or remove the user-owned staging directory under `raw-skills/`.
- Merge `javascript` and `typescript` into a single skill or change the mandatory TypeScript modeling policies and fallback safety rules established by `P-00005`; TypeScript edits are limited to tier activation and fallback conditions, prerequisite declarations, and delegation of ECMAScript runtime semantics to `javascript`.
- Rewrite unrelated rules, skills, plans, or documentation.

## Related decisions

- [D-00004: Copy Skills into Workspaces](../decisions/D-00004-copy-skills-into-workspaces.md)
- [D-00005: Repository and Installation Identity](../decisions/D-00005-repository-and-installation-identity.md)
- [D-00006: Skill Layering and Language Hierarchy](../decisions/D-00006-skill-layering-and-language-hierarchy.md)

## Design

### Skill layout

Add the following source tree under `skills/`:

```text
skills/javascript/
├── SKILL.md
└── references/
    ├── async-and-lifecycle.md
    ├── functions-and-errors.md
    ├── modules-and-boundaries.md
    ├── objects-and-collections.md
    ├── values-and-validation.md
    └── verification-and-contracts.md
```

The existing skill discovery logic in `tools/common/skill_files.py` will detect `skills/javascript/SKILL.md`, snapshot the regular-file tree, and copy it into `<workspace>/.agents/skills/javascript/` with manifest tracking. No installer code changes or explicit skill registration in `tools/` are required.

The source staging directories `raw-skills/javascript-skill-canonical/` and `raw-skills/typescript-skill/` are ignored by Git and treated as read-only inputs. Record both regular-file inventories and SHA-256 checksums before implementation and verify they remain unchanged afterward.

Do not copy `raw-skills/javascript-skill-canonical/AGENTS.example.md` into `skills/javascript/`. Its workspace-facing activation rule belongs in `AGENTS.md`, while repository authoring guidance (keeping reference examples self-contained standard ECMAScript without host-specific imports) does not belong in distributed workspace `AGENTS.md` files.

### Relationship with `AGENTS.md`, `pragmatic-functional-programming`, and `typescript`

- **Three-tier hierarchy (`D-00006`)**:
  - **Tier 1 (`pragmatic-functional-programming`)**: Activated by `AGENTS.md` (`## Pragmatic Functional Programming Rules`) for every coding task in any language. Load and apply it first; it has precedence wherever lower tiers address the same general engineering concern.
  - **Tier 2 (`javascript`)**: Canonical ECMAScript base for JavaScript and all languages/environments derived from or built on JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`, JSDoc-typed JS, TypeScript, and future runtime/framework skills). Supplies ECMAScript-specific semantics and mechanisms such as `??` vs `||`, `Object.hasOwn`, shallow-spread aliasing, mutating versus copying array methods, `Error.cause`, Promise combinator behavior, `try/finally` `return await`, `using`, and ES module live bindings.
  - **Tier 3 (`typescript` and future JS-ecosystem skills)**: Owns static type-system rules (`.ts`, `.tsx`), host APIs, and framework/UI conventions on top of Tier 1 and Tier 2. This plan aligns the existing TypeScript skill and activation rules so ECMAScript runtime semantics delegate to `javascript` while TypeScript-specific policy remains unchanged.
- **Concern ownership**: `pragmatic-functional-programming` decides whether a value crosses a trust boundary, whether mutation is safely owned, what error behavior is intended, whether work may run concurrently, what cleanup is required, and what behavior needs tests. `javascript` supplies ECMAScript-specific semantics and mechanisms that implement those decisions.
- **JavaScript vs TypeScript boundary**: `## JavaScript Rules` in `AGENTS.md` activates `javascript` for `.js`, `.jsx`, `.mjs`, `.cjs`, and JSDoc-typed JavaScript files as the canonical ECMAScript layer, and directs agents to pair it with `typescript` (`.ts`, `.tsx`) for static type-system rules or with separate runtime/framework skills for host APIs and UI conventions.
- **Authoring note placement**: Omit the last sentence of `AGENTS.example.md` ("Keep any code examples added to `references/*.md` self-contained standard ECMAScript without host-specific imports.") from the distributed `AGENTS.md` rule, as it is a skill-maintainer guideline rather than a workspace coding rule. Keep that constraint documented in `skills/javascript/` or `skills/README.md` if desired.

Apply this ownership boundary when adapting overlapping canonical guidance:

| Concern | Owner |
| --- | --- |
| Whether and where runtime validation is required | `pragmatic-functional-programming` |
| How JavaScript distinguishes omission, `undefined`, `null`, and valid falsy values | `javascript` |
| Whether mutation is safely owned | `pragmatic-functional-programming` |
| How spread, shallow copying, array methods, `Map`, and `Set` affect JavaScript ownership | `javascript` |
| Intended error propagation, recovery, and fallback policy | `pragmatic-functional-programming` |
| JavaScript thrown-value behavior, `Error.cause`, `AggregateError`, and callback receiver semantics | `javascript` |
| Whether concurrency and cancellation are appropriate | `pragmatic-functional-programming` |
| Promise combinator, async iteration, `return await`, and disposal semantics | `javascript` |
| What observable behavior and invariants require tests | `pragmatic-functional-programming` |
| JSDoc erasure, runtime guards, and JavaScript-specific regression cases | `javascript` |
| Whether an API should use a parameter object for clarity and evolution | `pragmatic-functional-programming` |
| How a parameter-object contract is represented and checked statically in TypeScript | `typescript` |
| Whether a curated public barrel or another module boundary is architecturally appropriate | `pragmatic-functional-programming` |
| ES module live bindings, evaluation order, TDZ, top-level-await cycles, and circular initialization behavior | `javascript` |
| TypeScript module resolution/emission, `import type`, and the exported type-surface consequences of barrels | `typescript` |

### `AGENTS.md` integration

Add a `## JavaScript Rules` section to `AGENTS.md` after `## Pragmatic Functional Programming Rules` and before `## TypeScript Rules`, adapted from `raw-skills/javascript-skill-canonical/AGENTS.example.md`:

- State activation scope: tasks that write, modify, test, or review JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`) or JSDoc-typed JavaScript, plus ECMAScript runtime semantics used by TypeScript/TSX and other JavaScript-ecosystem specializations.
- Require `pragmatic-functional-programming` to be loaded and applied first, with precedence for general engineering decisions.
- State responsibility: use `javascript` as the canonical ECMAScript base for language semantics, runtime validation, ownership, and async lifecycles; pair with separate runtime, framework, or TypeScript skills (`.ts`, `.tsx`) for host APIs, UI conventions, or static type-system rules.
- State verification expectation: consult relevant references, preserve observable contracts unless explicitly requested, and verify changes through deterministic tests and existing project checks.

Update the existing `## TypeScript Rules` section without changing its mandatory modeling policies or fallback safety rules:

- Require every TypeScript and TSX task to load `pragmatic-functional-programming` first, `javascript` second, and `typescript` third.
- State precedence explicitly: `pragmatic-functional-programming` owns general engineering decisions, `javascript` owns ECMAScript runtime semantics, and `typescript` owns static type-system rules.
- Define fallback behavior explicitly: if `pragmatic-functional-programming` is unavailable, do not apply `javascript`, `typescript`, or their fallback rules; if `javascript` is unavailable, do not apply or claim to apply the dependent `typescript` skill, but retain the mandatory `AGENTS.md` TypeScript policies and fallback safety rules; if both prerequisites are available but `typescript` is unavailable, apply the existing TypeScript fallback safety rules.

### `SKILL.md` and references adaptation

Inspect `raw-skills/javascript-skill-canonical/javascript/SKILL.md` and `references/*.md` during implementation and adapt them against the concern-ownership table:

- Preserve `name: javascript`, ECMAScript-specific semantics, reference routing, and language-specific completion checks; expand the activation description to cover ECMAScript runtime semantics in TypeScript/TSX and other JavaScript-ecosystem specializations as required by D-00006.
- Declare `pragmatic-functional-programming` as the foundation and establish its precedence before the JavaScript workflow.
- Recast overlapping general rules as short cross-references to the foundational skill while retaining the JavaScript-specific mechanisms, consequences, examples, and edge cases that implement them.
- Do not independently decide trust boundaries, mutation policy, concurrency strategy, cleanup requirements, error policy, or behavioral-test scope merely because an example is written in JavaScript.
- Ensure all relative links in `SKILL.md` (`references/*.md`) resolve within `skills/javascript/`.
- Verify there are no symlinks, broken links, or references to external staging files (`AGENTS.example.md`).
- Keep `references/*.md` self-contained standard ECMAScript examples without host-specific imports.
- Record a topic-by-topic semantic coverage check showing that canonical JavaScript-specific guidance is retained, delegated to `pragmatic-functional-programming`, or intentionally excluded with rationale.

### TypeScript alignment

Align `skills/typescript/` with D-00006 in the same implementation:

- Update `skills/typescript/SKILL.md` frontmatter and prerequisite section to require both `pragmatic-functional-programming` and `javascript`, in that order, before applying TypeScript guidance.
- Keep TypeScript authoritative for interfaces, type aliases, discriminated unions, narrowing, `unknown`, `never`, `satisfies`, `as const`, `import type`, compiler configuration, type-aware linting, and compile-time type tests.
- Replace independently normative explanations of ECMAScript runtime behavior—including `??` vs `||`, `Error.cause`, Promise combinator behavior, cancellation mechanics, `return await`, collection copying APIs, and module initialization cycles—with concise routing to the relevant JavaScript reference.
- Retain TypeScript-specific consequences of those runtime mechanisms, such as inferred result types, discriminated `PromiseSettledResult` handling, type-aware floating-promise detection, `AbortSignal` typing, emitted-module implications, and compiler target compatibility.
- Delegate the decision to introduce a parameter object or curated public barrel to `pragmatic-functional-programming`; retain TypeScript-specific contract typing, `import type`, module-resolution/emission behavior, and exported type-surface consequences, while routing ES module initialization and cycle behavior to `javascript`.
- Preserve useful links and location-independent routing after installation; do not create repository-relative links from an installed skill to a sibling skill. Refer to the `javascript` skill and its reference name in text when cross-skill links would break after copying.
- Extend the semantic coverage record to verify that `skills/typescript/` remains semantically aligned with its `raw-skills/typescript-skill/` origin (via `P-00005`), mapping each removed or shortened TypeScript runtime topic to its canonical JavaScript owner and identifying every retained TypeScript-specific consequence without losing origin guidance.

### Post-implementation alignment corrections

Complete these corrections before returning the plan to `Implemented`:

1. Restore the `P-00005` guidance that multi-step asynchronous operations and error handling should prefer `async`/`await` when it makes sequencing and failure flow clearer than nested Promise chains. Assign the readability decision to `pragmatic-functional-programming`, document the ECMAScript mechanism in `skills/javascript/references/async-and-lifecycle.md`, and route TypeScript readers to that canonical guidance without independently duplicating it.
2. Correct the TypeScript `PromiseRejectedResult` documentation in `skills/typescript/references/async.md`: show the standard library's actual `reason: any` declaration, then separately recommend treating or narrowing the value as `unknown` before inspecting it. Do not present the safer recommendation as the declared library type.
3. Add durable implementation evidence recording that both ignored staging trees matched their before-work regular-file inventories and SHA-256 checksum baselines after implementation. Record the number of files compared and the exact-match result for each tree; include the baseline hashes or identify a durable repository artifact containing them so the acceptance criterion is independently verifiable.
4. Update the combined semantic coverage record so the restored `async`/`await` guidance has an explicit owner and mapping, then rerun the complete test suite, installation dry run, link checks, and staging-tree comparison.
5. Strengthen the installer regression test so it verifies the structure and order of the installed TypeScript skill's prerequisite declaration: `pragmatic-functional-programming` first, `javascript` second, then TypeScript guidance. Merely checking that both prerequisite names occur somewhere in the file is insufficient.

### Documentation updates

- **`skills/README.md`**: Add `javascript` under `## Available Skills` with links to `SKILL.md` and all six files in `references/`.
- **`README.md`**:
  - Mention JavaScript in `## Purpose` alongside TypeScript and pragmatic functional programming.
  - Add `[JavaScript Rules](./AGENTS.md#javascript-rules)` under the `AGENTS.md` contents list.
  - Add `[javascript](./skills/javascript/SKILL.md)` under the `skills/` contents list.
- In both skill lists, order the hierarchy as `pragmatic-functional-programming`, `javascript`, then `typescript`, followed by the remaining skills.

## Implementation steps

1. Record the regular-file inventories and SHA-256 checksums of both `raw-skills/javascript-skill-canonical/` and `raw-skills/typescript-skill/` to verify read-only preservation after implementation.
2. Create `skills/javascript/SKILL.md` and `skills/javascript/references/*.md` from `raw-skills/javascript-skill-canonical/javascript/`, adapting overlapping general guidance according to the concern-ownership table while preserving JavaScript-specific semantics and mechanisms.
3. Complete a topic-by-topic semantic coverage check against the canonical entrypoint and six references, classifying guidance as retained, delegated to the current `pragmatic-functional-programming` skill, or intentionally excluded with rationale.
4. Add the `## JavaScript Rules` section to `AGENTS.md` adapted from `raw-skills/javascript-skill-canonical/AGENTS.example.md`, requiring foundational precedence and excluding the maintainer-only `references/*.md` authoring note from workspace-distributed rules.
5. Update `## TypeScript Rules` and `skills/typescript/SKILL.md` to require `pragmatic-functional-programming`, `javascript`, and `typescript` in tier order with explicit ownership and missing-prerequisite behavior.
6. Align TypeScript references with the canonical JavaScript skill, delegating overlapping ECMAScript runtime semantics while retaining TypeScript-specific consequences; extend the semantic coverage record with explicit source-to-owner mappings.
7. Update `skills/README.md` and `README.md` to document the hierarchy and order the three skills by dependency.
8. Extend `tests/test_install.py` to:
   - Include `"javascript"` in the expected installed skill names and manifest entries.
   - Verify all six expected reference files exist as regular files under `.agents/skills/javascript/references/`.
   - Verify `AGENTS.example.md` is not copied into `.agents/skills/javascript/`.
   - Verify all relative Markdown links inside the installed `javascript` skill resolve to files within `.agents/skills/javascript/`.
   - Assert that the installed managed `AGENTS.md` block contains `## JavaScript Rules` and activates all three TypeScript tiers in order.
   - Verify the installed TypeScript skill structurally declares `pragmatic-functional-programming` first and `javascript` second before TypeScript guidance, rather than merely checking that both names occur, and contains no relative links that escape its installed skill tree.
9. Run `python3 -m unittest discover tests` and confirm all tests pass.
10. Verify both staging-tree inventories and checksums match step 1 and complete the combined JavaScript/TypeScript semantic coverage record confirming semantic alignment with `raw-skills/javascript-skill-canonical/` and `raw-skills/typescript-skill/` (via `P-00005`).
11. Complete every post-implementation alignment correction above and record the verification evidence in this plan or another durable repository artifact linked from it.
12. Rerun `python3 -m unittest discover tests`, the self-install dry run, relative-link validation, and both staging-tree comparisons.
13. Only after every acceptance criterion passes, update this plan's status to `Implemented` in both this document and `docs/plans/README.md`.

## Test plan

- **Unit & integration tests**: Run `python3 -m unittest discover tests`, covering:
  - Skill discovery and regular-file validation for `skills/javascript/`.
  - Installation of `skills/javascript/` and its six `references/*.md` files into a temporary workspace, plus manifest verification.
  - Relative Markdown link integrity within the installed `javascript` skill tree.
  - Exclusion of `AGENTS.example.md` from the installed skill directory.
  - Managed `AGENTS.md` block installation containing `## JavaScript Rules` and repeatability (second install is a no-op).
  - TypeScript activation order (`pragmatic-functional-programming` -> `javascript` -> `typescript`) in the installed managed rules.
  - Installed TypeScript prerequisite declarations, including their required structure and order (`pragmatic-functional-programming` -> `javascript` -> `typescript`), and valid location-independent delegation to the JavaScript skill.
  - Uninstaller removal of the manifest-backed `javascript` skill copy.
- **Self-install dry-run**: Optionally run `python3 tools/install.py --workspace . --dry-run` to preview skill discovery in the repository itself.
- **Source-preservation evidence**: Record durable before/after inventory and SHA-256 checksum evidence for both ignored staging trees, including each file count and exact-match result; include the baseline hashes in this plan or link a durable repository artifact that contains them.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Overlap or conflicting ownership between `javascript` and `pragmatic-functional-programming` | Establish foundational precedence, use the concern-ownership table during adaptation, and verify canonical guidance through the semantic coverage check. |
| Confusion between JavaScript and TypeScript activation | Clearly scope `## JavaScript Rules` in `AGENTS.md` to `.js`/`.jsx`/`.mjs`/`.cjs` and JSDoc-typed JS, and state how it pairs with `typescript` for `.ts`/`.tsx`. |
| TypeScript loses useful guidance while duplicate runtime sections are removed | Use explicit semantic coverage mappings and retain TypeScript-specific type, compiler, tooling, and emitted-runtime consequences. |
| Cross-skill Markdown links break after skills are copied independently | Use location-independent textual routing between sibling skills and validate that relative links remain inside each installed skill tree. |
| Maintainer-only `references/*.md` authoring instruction leaks into target workspaces via `AGENTS.md` | Omit the `references/*.md` authoring sentence from `AGENTS.md` during adaptation from `AGENTS.example.md`. |
| Broken relative links or accidental symlinks in `skills/javascript/` | Validate regular-file tree and relative Markdown links in `tests/test_install.py`. |
| Accidental modification of either gitignored `raw-skills/` staging tree | Record inventories and checksums for both JavaScript and TypeScript sources before implementation and verify both are unchanged afterward. |

## Acceptance criteria

- `skills/javascript/SKILL.md` and all six `skills/javascript/references/*.md` files exist as regular files with valid relative links.
- `AGENTS.md` includes `## JavaScript Rules` with clear activation boundaries, foundational precedence, and no maintainer-only `references/*.md` authoring instructions.
- Both `skills/javascript/` and the updated `skills/typescript/` remain semantically aligned with their respective `raw-skills/` origins (`raw-skills/javascript-skill-canonical/` and `raw-skills/typescript-skill/` via `P-00005`), with every original item accounted for as retained, delegated across tiers (`pragmatic-functional-programming` -> `javascript` -> `typescript`), or intentionally excluded with rationale, as demonstrated by the combined semantic coverage record.
- TypeScript and TSX instructions load `pragmatic-functional-programming`, `javascript`, and `typescript` in order, and `skills/typescript/SKILL.md` declares both upstream prerequisites with matching precedence.
- Existing TypeScript ECMAScript runtime topics delegate to `javascript` without losing TypeScript-specific static, compiler, tooling, or runtime-compatibility consequences.
- The multi-step `async`/`await` preference retained by `P-00005` remains discoverable through the tiered guidance and has an explicit semantic-coverage mapping.
- `skills/typescript/references/async.md` accurately distinguishes the standard library's `PromiseRejectedResult.reason: any` declaration from the recommendation to treat or narrow rejected reasons as `unknown`.
- `skills/README.md` and `README.md` list the hierarchy in dependency order and link the JavaScript documentation.
- `tests/test_install.py` verifies `javascript` skill installation, reference files, manifest entries, link integrity, the structure and order of the installed TypeScript prerequisite declaration (not merely prerequisite-name occurrence), and managed `AGENTS.md` activation content.
- `python3 -m unittest discover tests` passes with zero failures or skipped tests.
- A durable verification record contains the baseline inventories and SHA-256 hashes, or links a repository artifact containing them, records the file count and exact-match result for each staging tree, and confirms that `raw-skills/javascript-skill-canonical/` and `raw-skills/typescript-skill/` remain unmodified against those baselines.

### Combined JavaScript and TypeScript semantic coverage record

#### 1. `raw-skills/javascript-skill-canonical/` -> `skills/javascript/` and `AGENTS.md`

| Origin Source | Original Item / Topic | Classification | Disposition / Mapping |
| --- | --- | --- | --- |
| `AGENTS.example.md` | Activation for `.js`, `.jsx`, `.mjs`, `.cjs`, JSDoc JS, pairing with TS/host/framework skills | Retained / Adapted | `AGENTS.md` (`## JavaScript Rules`), expanded for Tier 2 ECMAScript role under `D-00006` |
| `AGENTS.example.md` | Maintainer note (`references/*.md` self-contained ECMAScript examples) | Excluded from `AGENTS.md` | Omitted from distributed `AGENTS.md`; retained as skill-authoring constraint in `P-00006` |
| `SKILL.md` | Activation, Workflow (5 steps), Core Rules, Reference Routing, Completion Checklist | Retained / Delegated | `skills/javascript/SKILL.md`; adds `## Prerequisite and precedence` for `pragmatic-functional-programming` (Tier 1) and recasts general policy checks as cross-references |
| `values-and-validation.md` | `??` vs `\|\|`, `Object.hasOwn`, `===` vs `==`, `Object.is`, `Number.isSafeInteger`, `BigInt`, boundary parsing, prototype pollution, `RegExp.escape`, UTF-16/code points, `JSON.stringify` | Retained / Delegated | `skills/javascript/references/values-and-validation.md`; trust-boundary placement delegated to `pragmatic-functional-programming`, ECMAScript mechanics retained |
| `objects-and-collections.md` | Shallow spread aliasing, `WeakMap`/`WeakSet`, prototypes/internal slots/`Proxy`, `toSorted`/`toReversed`/`toSpliced`, `Iterator` helpers, `Map`/`Set` `SameValueZero` | Retained / Delegated | `skills/javascript/references/objects-and-collections.md`; mutation ownership policy delegated to `pragmatic-functional-programming`, ECMAScript mechanics retained |
| `functions-and-errors.md` | Destructured options, detached `this`, `map(parseInt)` arity, listener identity, `Error(..., { cause })`, `AggregateError`, `Error.isError`, `Promise.try`, no silent empty fallbacks | Retained / Delegated | `skills/javascript/references/functions-and-errors.md`; API-shape & error/fallback policy delegated to `pragmatic-functional-programming`, ECMAScript mechanics retained |
| `async-and-lifecycle.md` | `async forEach` hazard, `Promise.all`/`allSettled`/`any`/`race`, bounded worker pool, waterfalls, `return await` in `try/finally`, `using`/`await using`, cooperative cancellation, `async function*` | Retained / Delegated | `skills/javascript/references/async-and-lifecycle.md`; concurrency/cleanup policy delegated to `pragmatic-functional-programming`, ECMAScript mechanics retained |
| `modules-and-boundaries.md` | Strict mode, live read-only bindings, evaluation order, TDZ & TLA cycles, dynamic `import()`, import attributes, host adapter & feature detection | Retained / Delegated | `skills/javascript/references/modules-and-boundaries.md`; architectural boundary/effect isolation delegated to `pragmatic-functional-programming`, ES module mechanics retained |
| `verification-and-contracts.md` | JSDoc erasure vs. runtime guards, deterministic tests, regression checklist | Retained / Delegated | `skills/javascript/references/verification-and-contracts.md`; behavioral/invariant test scope delegated to `pragmatic-functional-programming`, JS regression cases retained |

#### 2. `raw-skills/typescript-skill/` (via `P-00005`) -> `skills/typescript/` aligned with `D-00006`

All items previously audited in `P-00005` remain accounted for; the following `skills/typescript/` sections were aligned from `P-00005` to delegate Tier 1/Tier 2 concerns while retaining TypeScript-specific consequences:

| `skills/typescript/` Location | Topic | Canonical Owner | Retained TypeScript Consequence |
| --- | --- | --- | --- |
| `SKILL.md` | Prerequisite & precedence | `AGENTS.md` & `D-00006` | Requires `pragmatic-functional-programming` (Tier 1) and `javascript` (Tier 2) in order before TypeScript; preserves `P-00005` modeling & fallback safety rules |
| `references/functions.md` | Parameter objects for ambiguous options | `pragmatic-functional-programming` (API shape); `javascript` `functions-and-errors` (destructuring) | Explicit `interface` contract typing (`UserSearchOptions`) |
| `references/functions.md` | `??` vs `\|\|` | `javascript` `values-and-validation` | Narrowing `T \| null \| undefined` to `T` while preserving falsy literals |
| `references/functions.md` | `Error(..., { cause })` & catch-rethrow | `javascript` `functions-and-errors` | `useUnknownInCatchVariables` (`unknown`) narrowing under `strict: true` |
| `references/functions.md` & `async.md` | `return await` inside `try/catch` / `try/finally` | `javascript` `async-and-lifecycle` | `Promise<T>` signature delegation & `@typescript-eslint/return-await` alignment |
| `references/async.md` | `async`/`await` for clear multi-step sequencing and error flow | `pragmatic-functional-programming` (readability decision); `javascript` `async-and-lifecycle` (ECMAScript mechanism) | `Promise<T>` return-type inference across linear `await` steps, with routing to `javascript` `async-and-lifecycle` |
| `references/async.md` | `Promise.all` & `Promise.allSettled` runtime semantics | `javascript` `async-and-lifecycle` | Tuple type inference & discriminated `PromiseSettledResult<T>` narrowing |
| `references/async.md` | `Promise.race` timeout vs. `AbortSignal` cancellation | `javascript` `async-and-lifecycle` | `signal?: AbortSignal` typing & `tsconfig.json` `lib`/`target` compatibility |
| `references/modules.md` | Barrel exports & circular initialization | `pragmatic-functional-programming` (architecture); `javascript` `modules-and-boundaries` (runtime cycles) | `import type`, `moduleResolution` / `.js` extensions, compiler dependency graphs, & minimal public type surface |
| `references/type-design.md` | Non-mutating array copying (`toSorted()`) | `javascript` `objects-and-collections` | `readonly T[]` / `ReadonlyArray<T>` compile-time checks & `ES2023+` target compatibility |
| `references/data-modeling.md` | Runtime parsing & coercion at trust boundaries | `pragmatic-functional-programming` (boundary trust); `javascript` `values-and-validation` (parsing/coercion) | `unknown` boundary typing, type erasure, semantic interfaces, & `exactOptionalPropertyTypes` |

### Raw-skills read-only verification record

Both gitignored staging trees were inventoried and hashed with `shasum -a 256` before implementation and re-verified after all edits:

- **`raw-skills/javascript-skill-canonical/`**: 8 regular files, 8/8 exact SHA-256 matches (unmodified).
- **`raw-skills/typescript-skill/`**: 12 regular files, 12/12 exact SHA-256 matches (unmodified).

| Staging Tree | File | Baseline & Final SHA-256 | Match |
| --- | --- | --- | --- |
| `javascript-skill-canonical` | `AGENTS.example.md` | `ac0c8c551271bfbe906897c65794ea27ff9da0bfc845f7f03cd4f2e057b40a44` | Exact |
| `javascript-skill-canonical` | `javascript/SKILL.md` | `0a1637c73cf6b421a6e34fa7a045d93b67e5dd709d71874f02fdbc83632dc35d` | Exact |
| `javascript-skill-canonical` | `javascript/references/async-and-lifecycle.md` | `2f353df6dff322bf4d9866197c4762bbd4e6481446392e55bcd15c0154f55bcf` | Exact |
| `javascript-skill-canonical` | `javascript/references/functions-and-errors.md` | `ca1f58bfc723119f3108a9fac93c39b27ec4b1341fe54aa6db1fc1da77689aca` | Exact |
| `javascript-skill-canonical` | `javascript/references/modules-and-boundaries.md` | `1f2a62ff57d5ce3e4109a47cf488f26f9fca02731244dccb65fa0f9f6dd92a4c` | Exact |
| `javascript-skill-canonical` | `javascript/references/objects-and-collections.md` | `d63d43a61e11c8066f1db0fe9fd9e45cd575f536fd00e6f3cfeb2b91778cdef3` | Exact |
| `javascript-skill-canonical` | `javascript/references/values-and-validation.md` | `02cd6ee2bb30cc42dc9095085c817dfab44bcf217b70ddb94c0395dd852a3413` | Exact |
| `javascript-skill-canonical` | `javascript/references/verification-and-contracts.md` | `5b9f8c1f5dba53a704d2bca20bb7cda1291585fe17db8036ad87d15a3cba7697` | Exact |
| `typescript-skill` | `README.md` | `4bc79ec1ec1891f6a5def4ecfde4dfc70ff02a4ad906a38f33c9571118921011` | Exact |
| `typescript-skill` | `SKILL.md` | `1030cdd8f4a72e20392403e0b400842b86dfefcb3d4ca991bf87dd1a0405f5e0` | Exact |
| `typescript-skill` | `integrations/AGENTS.example.md` | `ded3f4b6074c32f5e66a98b4b89b57901e4f1fa5ca141a4096a07186dbbeef84` | Exact |
| `typescript-skill` | `integrations/README.md` | `ac44982ce249c92aa75315c19221f89fa53b97aa2ed383306377696a2be144cb` | Exact |
| `typescript-skill` | `references/async.md` | `3804fa27f2088408d216d9e8ab9936bffcef549843e9ef815f45afaa6be9e36c` | Exact |
| `typescript-skill` | `references/data-modeling.md` | `a4664a763c7b19d0409618e00daa83c30d85ce1ab1b4f221cdd178341f1c8367` | Exact |
| `typescript-skill` | `references/functions.md` | `081424cd7851be3cd8496536a12db094648cb1133710169536624499aacde010` | Exact |
| `typescript-skill` | `references/modules.md` | `e202e533f187eced3b7fd8947f695d3e8e2fb0bbf000822f2d12616f14b99770` | Exact |
| `typescript-skill` | `references/patterns.md` | `90234f39fdd06a55003776dcbe5b279b8fc2fd9ec45f11ab58f4040878603d50` | Exact |
| `typescript-skill` | `references/tooling.md` | `e8c5c4770d371e8bc7fd53a06bb3411ee7e6bd56f316968550d891c7c2c6503c` | Exact |
| `typescript-skill` | `references/type-design.md` | `917c115827b66922b75cba9aa0f44dde9a87ad10d826f6d04f468be586678ab4` | Exact |
| `typescript-skill` | `references/type-safety.md` | `ff049eeeb0acc7d26ac1ae058ff9c172918bdd78a76a16bd5297593e25ef6bd4` | Exact |

## Open questions

None.
