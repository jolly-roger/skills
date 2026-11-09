# P-00005: TypeScript Skill Integration

## Status

Implemented

## Date

2026-11-05

## Objective

Integrate the TypeScript guidance staged in `raw-skills/typescript-skill/` as a first-class library skill that is automatically distributed to workspaces and activated for TypeScript and TSX work only after the `pragmatic-functional-programming` skill has been loaded.

The TypeScript skill will be a dependent language specialization rather than a standalone source of general engineering guidance. `pragmatic-functional-programming` remains authoritative for shared principles and has precedence wherever the skills overlap. The TypeScript skill contains only TypeScript-specific rules, consequences, tools, and examples.

## Scope

- Add a discoverable `skills/typescript/` skill with a root `SKILL.md` and seven TypeScript-specific topic references adapted from `raw-skills/typescript-skill/references/`.
- Adapt the staged skill to the library's packaging and instruction conventions instead of copying it verbatim.
- Make `pragmatic-functional-programming` a required prerequisite for applying the TypeScript skill.
- Completely replace the current TypeScript section in the authoritative `AGENTS.md` with the proposed ordered activation, TypeScript-specific fallback, and modeling rules.
- Align the replacement `AGENTS.md` section and the skill so they do not prescribe conflicting uses of `Omit`, interfaces, or type aliases.
- Remove general functional-programming, architecture, mutation, dependency, error, and testing rules duplicated by the TypeScript skill or its references.
- Document the new skill in the root and skills-level summaries.
- Order both README skill lists with `pragmatic-functional-programming` first and `typescript` second, followed by every other skill.
- Extend installer coverage so distribution of the TypeScript skill and its references is verified.
- Validate the skill structure, reference routing, installation, repeatability, and complete test suite.

## Non-goals

- Change the installer or uninstaller architecture.
- Add TypeScript runtime code, packages, linters, compiler configuration, or other dependencies to this repository.
- Copy the staged skill's standalone `README.md`, `integrations/README.md`, or `integrations/AGENTS.example.md` into the installed skill.
- Add `agents/openai.yaml`, scripts, assets, or other skill resources without a demonstrated requirement.
- Modify or remove the user-owned staging directory under `raw-skills/`.
- Rewrite unrelated rules, skills, plans, or documentation.
- Turn the TypeScript skill into an exhaustive language manual or duplicate the language-independent pragmatic functional-programming guidance.
- Support applying the TypeScript skill without the `pragmatic-functional-programming` skill.
- Make the TypeScript skill independently portable outside a distribution that also supplies its required prerequisite.

## Related decisions

- [D-00004: Copy Skills into Workspaces](../decisions/D-00004-copy-skills-into-workspaces.md)
- [D-00005: Repository and Installation Identity](../decisions/D-00005-repository-and-installation-identity.md)

## Design

### Skill layout

Add the following source tree:

```text
skills/typescript/
├── SKILL.md
└── references/
    ├── async.md
    ├── data-modeling.md
    ├── functions.md
    ├── modules.md
    ├── tooling.md
    ├── type-design.md
    └── type-safety.md
```

The existing skill discovery code will detect `skills/typescript/SKILL.md`, snapshot the complete regular-file tree, and install it under `.agents/skills/typescript/`. No explicit installer registration or new manifest behavior is required.

The source staging tree under `raw-skills/` is intentionally ignored by Git and is read-only input to this integration. Because ordinary Git status and diff output cannot prove that ignored files remained unchanged, record its regular-file inventory and checksums before implementation or corrective work and compare them afterward.

Do not include the staged root README or `integrations/` directory. Those files describe standalone copy or symlink installation and manual `AGENTS.md` wiring, while this library already owns manifest-backed copying and managed instruction installation. The installed skill must not present a second installation workflow or claim that it can be used independently of `pragmatic-functional-programming`.

Do not include `references/patterns.md`. Its general rules for pure transformations, immutable updates, explicit dependencies, readable collection operations, and locally owned mutation are already owned by `pragmatic-functional-programming`. Move only genuinely TypeScript-specific material, such as the use of `readonly` collection types or runtime-sensitive `toSorted()` guidance, into the most relevant TypeScript reference. Do not migrate the generic functional rules or examples.

### Contractual dependency and precedence

For TypeScript and TSX work, use this order:

1. Apply system, developer, user, and project-specific instructions according to their normal precedence.
2. Load and apply `pragmatic-functional-programming` as the foundation for data, calculations, actions, mutation ownership, effects, dependencies, domain modeling, error policy, and general testing.
3. Load and apply `typescript` as a dependent specialization for TypeScript's type system, runtime type boundaries, Promise APIs, modules, compiler, linting, and type-aware verification.

`pragmatic-functional-programming` has higher priority wherever both skills address the same concern. The TypeScript skill may refine how a general principle is expressed in TypeScript, but it must not relax, override, or independently redefine that principle. TypeScript-specific guidance remains authoritative where the general skill has no language-specific rule.

Define the dependency contract through the instruction surfaces already owned by the library:

- The replacement `AGENTS.md` TypeScript section instructs agents to load `pragmatic-functional-programming` first and `typescript` second for every TypeScript or TSX coding task.
- The TypeScript frontmatter description states that the skill requires `pragmatic-functional-programming` and is not intended for standalone use.
- The first operational instruction in `skills/typescript/SKILL.md` requires the agent to read and apply `pragmatic-functional-programming` before continuing.
- If the prerequisite cannot be loaded, the agent must report that the TypeScript skill's required foundation is unavailable and must not apply or claim to have applied the TypeScript skill or its TypeScript fallback rules. It may continue only under higher-priority instructions and ordinary project guidance.

This is a contractual dependency rather than a machine-enforced skill dependency. No `agents/openai.yaml` dependency metadata or installer dependency engine is planned because the repository does not currently use per-skill metadata and the installer already distributes all library skills together. Installation guarantees that `pragmatic-functional-programming` and `typescript` are present together; the managed `AGENTS.md`, skill description, and prerequisite instruction govern activation order.

Apply TypeScript fallback rules only when `pragmatic-functional-programming` has been loaded successfully but the TypeScript skill itself is unavailable. If `pragmatic-functional-programming` is unavailable, do not apply either the TypeScript skill or its fallback rules.

### Concern ownership

Use this classification rule when removing duplicates or assigning new guidance:

- A rule that decides program structure, behavior, ownership, effects, errors, trust, concurrency, or general testing belongs to `pragmatic-functional-programming`.
- A rule that explains how TypeScript represents, checks, narrows, compiles, lints, or executes that decision belongs to `typescript`.

Apply the rule through this ownership table:

| Concern | Owner |
| --- | --- |
| Whether work may run concurrently | `pragmatic-functional-programming` |
| How `Promise.all`, `Promise.allSettled`, and `AbortSignal` behave | `typescript` |
| Whether a value crosses a trust boundary | `pragmatic-functional-programming` |
| How `unknown`, guards, schemas, or assertions represent runtime trust | `typescript` |
| Whether mutation is safely owned | `pragmatic-functional-programming` |
| How `readonly`, `ReadonlyArray`, or immutable collection APIs express that contract | `typescript` |
| Whether errors must propagate or cleanup is required | `pragmatic-functional-programming` |
| How floating promises and TypeScript-aware lint rules detect violations | `typescript` |
| Whether domain states should exclude invalid combinations | `pragmatic-functional-programming` |
| How discriminated unions and exhaustive `never` checks encode those states | `typescript` |
| What behavior and invariants require tests | `pragmatic-functional-programming` |
| How typechecking and compile-time type tests verify TypeScript contracts | `typescript` |

### Instruction layering

Use four layers with distinct responsibilities:

1. The existing pragmatic functional-programming section in `AGENTS.md` activates the foundational skill for every coding task.
2. The replacement TypeScript section in `AGENTS.md` orders the prerequisite and dependent skill and owns the mandatory TypeScript policies and conditional fallback rules.
3. `skills/typescript/SKILL.md` declares the prerequisite, defines TypeScript applicability, and owns explanations, TypeScript mechanisms, exceptions permitted by `AGENTS.md`, examples, reference routing, and TypeScript-specific workflow and completion checks. It references rather than repeats mandatory `AGENTS.md` policy.
4. `skills/typescript/references/*.md` contains conditional TypeScript details and examples for type design, narrowing, function signatures, runtime data modeling, Promise APIs, modules, and tooling.

### Complete replacement of the current TypeScript rules

Remove the complete body of the current `## TypeScript Rules` section in `AGENTS.md` and replace it with the proposed ordered activation and TypeScript-specific modeling rules. Do not merge the old bullets into the new section or preserve them as compatibility constraints. `AGENTS.md` is the canonical owner of the mandatory policies below. The replacement first requires `pragmatic-functional-programming`, then activates `typescript`, and expresses the language-specific policy:

- Use `interface` by default for named object contracts, especially public and domain-facing objects. Permit an object `type` alias when established project conventions or a TypeScript constraint make it the clearer representation, and do not convert existing object aliases solely for stylistic uniformity.
- Use `type` for unions, tuples, primitive aliases, mapped or conditional types, and shapes that are not naturally expressed as interfaces.
- Avoid deriving domain and API models through `Omit` or chains of utility types. Prefer explicit contracts or genuinely meaningful shared interfaces.
- Permit a narrow utility-type use in a local adapter, generic helper, or third-party integration only when it is clearer than an explicit duplicate contract and does not weaken domain semantics.
- Prefer shallow, cohesive models, but preserve meaningful nested concepts rather than flattening them mechanically.

This policy fully supersedes the current `AGENTS.md` TypeScript rules, including the wording that restricts `type` to plain combinations of interfaces and treats every `Omit` use identically. The existing bullets may be deleted without retaining their wording or preserving their stricter behavior. The replacement keeps the broader goal of readable explicit models while supporting ordinary discriminated unions and focused adapter types.

Only TypeScript-specific safety rules should remain visible in the TypeScript fallback, and the fallback applies only when `pragmatic-functional-programming` is available but the TypeScript skill is not:

- Do not introduce `any`, TypeScript suppression directives, or weaker compiler or linter settings merely to silence errors.
- Use `unknown`, narrowing, or runtime validation when a value crosses a trust boundary identified by `pragmatic-functional-programming`; do not rely on a TypeScript assertion as runtime validation.
- Do not leave unintended floating promises; use TypeScript-aware tooling and explicit supervision for intentionally detached work.

Do not repeat general rules about trust boundaries, cleanup, compatibility, effects, dependencies, mutation, errors, or testing in the TypeScript section. Those remain owned by `pragmatic-functional-programming`. The TypeScript skill must not repeat the mandatory TypeScript policies owned by `AGENTS.md`; it should reference them and provide their TypeScript-specific explanations, mechanisms, permitted exceptions, and examples.

### Skill adaptation

Rebuild the staged `SKILL.md` as a dependent specialization:

- Preserve its TypeScript and TSX activation boundary, TypeScript-specific reference routing, and language-specific completion checks.
- Change the frontmatter description to state that `pragmatic-functional-programming` is required and must be applied first.
- Put the prerequisite and precedence rule before the TypeScript workflow.
- Remove the final link to `integrations/README.md`, because that directory will not be installed.
- Reference the mandatory `Omit`, interface, type-alias, safety, and fallback policies owned by `AGENTS.md` without restating them.
- Remove every normative rule already owned by `pragmatic-functional-programming`, including generic guidance about pure transformations, effect boundaries, mutation ownership, dependency injection, error categories, resource cleanup, general testing, minimal scope, and project compatibility.
- Retain short cross-references where needed to explain how a TypeScript mechanism applies a foundational or mandatory rule; do not restate the rule.
- Reduce the workflow to TypeScript-specific additions such as inspecting `tsconfig`, package scripts, module settings, public type contracts, inference, assertions, and available typecheck or lint commands.
- Reduce the completion checklist to TypeScript-specific checks such as public type design, narrowing, assertions, suppressions, floating promises, compiler compatibility, and type-aware verification.
- Keep all relative reference links valid from the installed skill directory.

Adapt the seven retained references to the same ownership boundary:

- `type-design.md` and `type-safety.md` retain TypeScript type-system guidance and receive any useful TypeScript-only `readonly` material from the excluded patterns reference.
- `data-modeling.md` explains TypeScript runtime type erasure, `unknown`, schema or guard use, mapping, and optional-property semantics. The foundational skill decides where a trust boundary exists.
- `functions.md` retains exported-signature inference, exhaustive union handling, assertion behavior, and TypeScript-specific async return semantics; remove generic naming, guard-clause, and error-policy rules.
- `async.md` retains `Promise.all`, `Promise.allSettled`, floating promises, `AbortSignal`, and `return await`; refer to the foundational skill for effect ordering, resource ownership, and general cleanup policy.
- `modules.md` retains `import type`, module-resolution conventions, barrel and cycle implications, and exported TypeScript surface; remove generic dependency-injection and effect-boundary rules.
- `tooling.md` retains TypeScript compiler, type-aware lint, type tests, and TypeScript command discovery; remove generic behavior-testing and failure-testing rules already covered by the foundational skill.

External documentation links in `tooling.md` are supporting references, not installation dependencies.

When classifying borderline content, apply the concern-ownership rule rather than retaining a generic rule merely because its example is written in TypeScript. In particular, DTO/domain separation, dependency injection, concurrency selection, cleanup policy, error propagation, and behavioral testing remain foundational concerns; the TypeScript references may cover only their TypeScript representations and tooling consequences.

### Documentation

Update the root `README.md` only at the repository-summary level:

- Include `typescript` in the reusable skill list.
- Keep detailed TypeScript topics in `skills/README.md` and the skill itself.
- Do not repeat the full rules or explain the mechanics of creating the plan.

Update `skills/README.md` with a short description of the TypeScript skill and links to its topic references, consistent with the existing pragmatic-functional-programming entry.

In both README skill lists, place `pragmatic-functional-programming` first and `typescript` second. Preserve the TypeScript dependency note and the skills-level reference links, and place all remaining skills after these two entries. This dependency-first order takes precedence over alphabetical ordering.

No new architecture decision is required because the integration uses the accepted copied-skill layout without changing distribution, ownership, or uninstall semantics.

### Testing boundaries

Treat skill content and the installed artifact as data. The installer and manifest logic are existing actions and should not be changed unless verification reveals an actual defect. Test observable outcomes—discovery, copied files, manifest inventory, managed rules, and idempotency—instead of asserting incidental prose or exact heading text.

### Post-implementation source-alignment corrections

A semantic audit compared the original `raw-skills/typescript-skill/` guidance with the combined target of `skills/typescript/`, canonical `AGENTS.md` TypeScript policy, and the current `pragmatic-functional-programming` skill. The audit treated the current foundational skill as an authoritative dependency and did not compare it with any raw origin. General functional guidance may remain delegated, but TypeScript-specific behavior must be preserved or explicitly documented as an intentional change. Complete these corrections before returning the plan to `Implemented`:

1. Reconcile the canonical interface policy with the original project-convention exception. Continue preferring `interface` for named object contracts, but permit an object `type` alias when an established project convention or TypeScript constraint makes it the clearer representation, and state that existing code must not be converted solely for stylistic uniformity.
2. Restore the original empty-extension caveat in `type-design.md`: do not introduce an empty interface extension when the shared interface already has the correct public meaning. Adjust the example or explanation so it does not implicitly recommend empty marker interfaces without distinct semantics.
3. Add the original `as const` guidance to `type-safety.md`, including its literal-inference benefit and deep-readonly consequence. Keep the `SKILL.md` routing description accurate to the actual reference content.
4. Restore concise TypeScript/JavaScript-specific guidance for choosing `??` instead of `||` when falsy values such as an empty string are valid, and document the `return await` stack-trace use case alongside its existing `try`/`catch` semantics.
5. Restore the original compiler recommendation that new TypeScript projects should enable `strict`, while existing projects must respect an explicit migration plan and must not have compiler policy changed silently.
6. Review the original function-specific preferences that are not explicitly supplied by `pragmatic-functional-programming`, including parameter objects for numerous ambiguous optional arguments, guard clauses, and preserving useful error causes. Retain only guidance that materially changes TypeScript work; record any deliberate omission instead of attributing it to the foundational skill without coverage.
7. Produce a topic-by-topic source-coverage record for the original entrypoint and all eight original references. Classify each item as retained in TypeScript, delegated to `pragmatic-functional-programming`, superseded by canonical `AGENTS.md` policy, or intentionally excluded with rationale. Treat the standalone README and integration files as packaging material intentionally replaced by this library.
8. Re-run the ownership, fixture, structural, installation, and source-alignment audits, then change the plan and index to `Implemented` only if every acceptance criterion passes.
9. Complete the source-coverage record at original-rule granularity. At minimum, add explicit dispositions for Result-style business-failure unions, time/currency/identifier modeling, the `async`/`await` preference for multi-step work, project-standard module conventions and module cohesion, project-standard compiler module/target settings, collection-operation versus loop selection, and use of an already-adopted functional library. Audit every remaining original rule so this minimum list does not become the boundary of the correction. Group rules only when the row identifies every grouped concern and one classification and rationale genuinely apply to all of them.
10. Resolve the remaining traceability and scope findings. Split the aggregated entrypoint workflow/completion-checklist and tooling self-review rows into explicit concerns with independently verifiable mappings; audit the rest of the table for similarly opaque grouping. Restore the original complex-type decision test in TypeScript guidance or classify it accurately as delegated or intentionally excluded with rationale. Preserve explicit time, currency, identifier, and optionality modeling whenever domain correctness depends on those concepts, rather than limiting that guidance to untrusted input boundaries.
11. Correct the restored currency guidance so it requires an explicit, precision-safe representation without universally prescribing integer minor units. Present integer minor units, decimal or arbitrary-precision values, and established domain value objects as context-dependent options; follow project conventions and domain requirements such as currency scale, range, arithmetic, serialization, and interoperability. Do not promote the original `totalCents` example into a universal policy.
12. Restore the two original operational distinctions that are not materially supplied by the current foundational skill. Document that a timeout may only stop the caller from waiting unless it propagates cancellation to the underlying work, and require agents to verify the intended behavior. Document that a catch block should not exist solely to rethrow the same error unchanged; catching remains valid for adding meaningful context while preserving `cause`, translating an error according to project policy, logging at the owning boundary, or guaranteeing cleanup.
13. Reorder the top-level skill entries in `README.md` and `skills/README.md` so `pragmatic-functional-programming` is first and `typescript` is second. Keep the TypeScript prerequisite wording and nested reference links intact, and move every other skill after the dependent pair.

## Implementation steps

1. Record the regular-file inventory and checksums for the ignored `raw-skills/typescript-skill/` source, then create `skills/typescript/` and copy the staged `SKILL.md` plus the seven retained reference files into the proposed layout, leaving the source unchanged and excluding `references/patterns.md`.
2. Rebuild `skills/typescript/SKILL.md` as a dependent specialization: declare the required foundational skill in the description and body, establish precedence, refer to the mandatory TypeScript policy in `AGENTS.md` without a repository-relative link, remove the standalone integration link, and retain only TypeScript-specific explanations, mechanisms, permitted exceptions, examples, workflow, and checks.
3. Review each retained reference against the concern-ownership table and `pragmatic-functional-programming`; remove every duplicated general or mandatory rule and preserve only TypeScript-specific mechanisms, consequences, and examples.
4. Move any useful TypeScript-only material from the excluded `patterns.md` into `type-design.md` or `type-safety.md` without migrating its general functional-programming rules.
5. Delete the complete body of the current `## TypeScript Rules` section in `AGENTS.md` and write the canonical replacement that loads `pragmatic-functional-programming` first, loads `typescript` second, owns the mandatory TypeScript policy, and applies its fallback only when the foundational skill is available.
6. Add the TypeScript skill and its required relationship to `README.md` and `skills/README.md` without reproducing detailed rules.
7. Update installer tests to require both `pragmatic-functional-programming` and `typescript` in the installed skill set and manifest.
8. Add focused verification that the installed TypeScript skill includes the seven retained references as regular files, contains no `patterns.md` or copied standalone integration files, and has no broken relative Markdown links. Prefer extending an existing installer test over creating prose-sensitive tests.
9. Validate the new skill's frontmatter, name, prerequisite, location-independent canonical-policy references, internal links, and reference routing with the available skill validator and manual inspection of both source and installed trees.
10. Run the complete unit test suite and a dry-run installation into a clean temporary workspace.
11. Inspect the final tracked diff for unintended changes, broken relative links, and duplicated rules; separately compare the ignored staging tree's inventory and checksums with the recorded baseline.
12. Complete every post-implementation alignment correction above and repeat the ownership audit against `AGENTS.md`, the concern-ownership table, and `pragmatic-functional-programming`.
13. Complete the raw-source semantic coverage record without comparing `pragmatic-functional-programming` to any raw origin; verify that every original TypeScript-specific rule is retained, deliberately superseded, or explicitly excluded.
14. Expand the source semantic coverage record so every normative rule in the original entrypoint and eight references has an explicit, traceable disposition; verify any delegated row against the current foundational skill and record a rationale for every exclusion.
15. Correct the TypeScript domain-modeling reference so explicit modeling of time, currency, identifiers, and optionality applies based on domain correctness independently of whether a value crosses an untrusted boundary; keep runtime validation conditional on the trust decision.
16. Replace opaque aggregate coverage rows with explicit mappings, reconcile every `Retained` row against actual target text, and either restore or accurately reclassify the original complex-type decision test.
17. Revise currency modeling in `data-modeling.md` to require an explicit representation with appropriate precision while treating integer minor units as one example rather than the only valid representation; preserve existing project conventions and domain constraints.
18. Add timeout semantics to the async reference without taking ownership of timeout policy: explain the difference between ending a wait and aborting underlying work, relate actual cancellation to `AbortSignal` or the API's cancellation mechanism, and keep the foundational skill authoritative for operational policy.
19. Add the unchanged-rethrow caveat to the functions reference alongside error-cause preservation: avoid redundant catch-and-rethrow blocks, while permitting catches that add context, translate errors, perform boundary-owned reporting, or guarantee cleanup.
20. Reorder both README skill lists so `pragmatic-functional-programming` is the first top-level entry and `typescript` is the second, preserving descriptions, dependency wording, and nested reference links.
21. After implementation, alignment corrections, and verification are complete, change this plan's status to `Implemented` and update `docs/plans/README.md` in the same change.

## Test plan

### Skill validation

- Confirm `skills/typescript/SKILL.md` has valid YAML frontmatter with matching `name: typescript` and a precise activation description.
- Confirm the description and first operational instruction declare `pragmatic-functional-programming` as a required prerequisite.
- Confirm every reference linked from `SKILL.md` exists and every included reference is reachable through the entrypoint.
- Confirm every relative Markdown link resolves in both the source and installed skill trees; references to repository-root policy are location-independent text rather than relative links that change meaning after copying.
- Confirm the skill contains no unfinished placeholders or links to the excluded `integrations/` directory.
- Confirm `patterns.md` is neither installed nor linked and that any retained material from it is specifically TypeScript-related.
- Compare the entrypoint and retained references against `pragmatic-functional-programming`, the concern-ownership table, and the mandatory `AGENTS.md` policy; confirm they do not independently restate those normative rules.
- Confirm `SKILL.md` completion checks and every reference point to canonical policy instead of repeating its interface, type-alias, `Omit`, utility-type, suppression, narrowing, or floating-Promise rules normatively.
- Confirm `async.md` describes Promise and cancellation mechanics without deciding whether work should run concurrently, preferring parallel execution, prescribing concurrency bounds, or independently specifying error supervision for ordinary or detached promises.
- Confirm `data-modeling.md` conditions validation on a trust decision made by `pragmatic-functional-programming` or project guarantees and does not classify all database reads as untrusted.
- Confirm the entrypoint and references do not independently decide whether invalid domain states should be excluded or whether runtime behavior requires tests.
- Confirm the skill tree contains only regular files and directories, with no symlinks or special files.

### Documentation verification

- Confirm the first two top-level skill entries in both `README.md` and `skills/README.md` are `pragmatic-functional-programming` and `typescript`, in that order.
- Confirm every other top-level skill follows those entries, while the TypeScript prerequisite wording and nested reference links remain unchanged.

### Original-source semantic coverage

- Compare `raw-skills/typescript-skill/SKILL.md` and all eight original references with the combined guidance in canonical `AGENTS.md`, `skills/typescript/`, and the current `pragmatic-functional-programming` skill.
- Do not compare `pragmatic-functional-programming` with any version under `raw-skills/`; treat the installed foundational skill as the target owner for delegated general guidance.
- Confirm every original item is classified as retained, delegated, superseded, or intentionally excluded with rationale; do not treat absence from the TypeScript skill as delegation unless the foundational skill actually covers the concern.
- Check every normative bullet in each original source against the coverage record. A broader topic row counts only when it explicitly names all covered concerns and provides a valid common classification and mapping.
- Confirm the record explicitly covers Result-style business-failure unions; time, currency, and identifier modeling; `async`/`await` for multi-step operations; project-standard module conventions and cohesive module boundaries; project-standard compiler module/target settings; collection operations versus loops; and already-adopted functional libraries.
- Confirm the original entrypoint workflow, entrypoint completion checklist, and tooling self-review items have explicit mappings rather than opaque aggregate rows.
- Confirm every `Retained` mapping identifies target guidance that materially preserves the original concern; specifically verify the complex-type decision test instead of inferring retention from nearby generic or utility-type guidance.
- Confirm time, currency, identifier, and optionality modeling is guided by domain correctness for trusted and untrusted values alike, while runtime parsing and validation remain conditional on the trust boundary.
- Confirm currency guidance requires an explicit precision-safe model without mandating integer minor units when an established decimal, arbitrary-precision, or domain-value representation better fits the project and currency semantics.
- Confirm async guidance distinguishes a timeout that only stops waiting from cancellation that aborts underlying work, without independently deciding timeout policy or concurrency strategy.
- Confirm function guidance discourages catches that only rethrow the same error unchanged while preserving legitimate contextual wrapping, translation, boundary reporting, and cleanup behavior.
- Confirm established project conventions can justify an object `type` alias and that existing object aliases are not converted solely for style.
- Confirm the type-design example and explanation do not imply that an empty interface extension is required when an existing shared contract already has the correct meaning.
- Confirm `type-safety.md` explains `as const` literal inference and deep-readonly consequences, matching its entrypoint routing description.
- Confirm the appropriate use of `??` versus `||` and the stack-trace behavior of `return await` remain discoverable TypeScript/JavaScript-specific guidance.
- Confirm new projects are guided toward `strict: true`, while existing projects retain their compiler policy unless an explicit migration is requested.
- Treat the original README and `integrations/` files as intentionally replaced packaging documentation, and treat the general content of `patterns.md` as delegated only where the foundational skill supplies equivalent guidance.

### Installer and manifest tests

- Install into a clean temporary workspace and verify `.agents/skills/typescript/SKILL.md` exists as a regular file.
- Verify all seven TypeScript reference files are copied as regular files.
- Verify every relative Markdown link in the installed TypeScript skill resolves within the installed skill tree and no packaged link assumes the source repository's shallower directory depth.
- Verify the canonical manifest contains `typescript` and inventories the complete installed tree.
- Verify `pragmatic-functional-programming` is installed alongside `typescript`.
- Verify the staged `patterns.md`, standalone README, and integration files are absent from the installed skill.
- Repeat installation without source changes and verify it reports an up-to-date state.
- Preserve existing tests for managed `AGENTS.md` content, modified-copy protection, uninstallation, rollback, and manifest safety.

### Manual instruction behavior review

- Start with a TypeScript coding request and confirm the instructions require loading `pragmatic-functional-programming` before `typescript`.
- Present `pragmatic-functional-programming` without the TypeScript skill and confirm the `AGENTS.md` TypeScript fallback applies.
- Present the TypeScript skill without `pragmatic-functional-programming` and confirm neither the TypeScript skill nor its fallback is claimed or applied.
- Present an overlapping mutation or effect-boundary question and confirm `pragmatic-functional-programming` controls the decision while TypeScript supplies only language-specific expression.
- Present independent Promise-returning operations and confirm the foundational skill decides whether concurrency is appropriate while the TypeScript skill explains the selected Promise API's behavior.
- Present a database value covered by trusted persistence guarantees and confirm the TypeScript skill does not require redundant validation merely because the value came from storage.
- Review a discriminated-union example and confirm the combined rules permit an appropriate `type` alias.
- Review a domain request model and confirm the combined rules prefer an explicit interface over `Omit` derivation.
- Review a focused third-party adapter and confirm a narrow utility type remains possible when it is the clearest choice.
- Review an external payload example and confirm runtime validation is required before domain use.
- Review independent and dependent Promise examples and confirm concurrency and error-handling guidance remains accurate.

These are manual semantic review scenarios performed with isolated instruction fixtures; they are not installer unit tests because normal installation always supplies both skills. Record the observed ownership and activation behavior without adding brittle tests that assert generated wording.

### Commands

```bash
python3 -m unittest discover tests
python3 tools/install.py --workspace <temporary-workspace> --dry-run
```

Run the bundled skill validator against `skills/typescript/` when it is available in the implementation environment.

Before and after implementation or corrective work, inventory and checksum the regular files under `raw-skills/typescript-skill/`; require an exact match because the directory is ignored by Git and cannot be verified through the tracked diff.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Old `AGENTS.md` bullets survive alongside the replacement and create conflicting TypeScript policies. | Replace the current section body in full, then review the replacement section and skill together against the policy defined in this plan. |
| Always-loaded instructions become too large or duplicate the skill. | Keep `AGENTS.md` limited to activation, mandatory TypeScript policy, and conditional fallback; route explanations, mechanisms, exceptions, and examples through `SKILL.md`. |
| Standalone integration documentation conflicts with manifest-backed installation. | Exclude the staged README and `integrations/` directory and remove links to them from the imported entrypoint. |
| The contractual dependency is mistaken for machine enforcement. | Document that installation guarantees co-presence while `AGENTS.md`, frontmatter, and the first skill instruction govern activation; do not claim metadata or installer enforcement. |
| The TypeScript skill is selected without its required foundation. | Do not apply the TypeScript skill or fallback, report the missing prerequisite, and continue only under higher-priority instructions and ordinary project guidance. |
| The skill duplicates the functional-programming skill and the two drift. | Remove duplicated normative rules, exclude `patterns.md`, and keep general principles authoritative only in `pragmatic-functional-programming`. |
| `AGENTS.md` and the TypeScript skill become competing TypeScript policy sources. | Make `AGENTS.md` canonical for mandatory policy and restrict the skill to references, explanations, mechanisms, permitted exceptions, and examples. |
| TypeScript examples are promoted into duplicate normative policy. | Keep examples illustrative, remove repeated `MUST` and `SHOULD` statements, and point each explanation back to its canonical owner. |
| TypeScript Promise documentation decides concurrency policy. | Restrict the reference to Promise and cancellation semantics; leave concurrency selection and bounds to `pragmatic-functional-programming`. |
| TypeScript boundary guidance treats all persisted values as untrusted. | Let the foundational skill or project guarantees identify the trust boundary, then explain only the TypeScript validation mechanism. |
| Removing duplicates makes TypeScript guidance unclear. | Retain concise cross-references and explain only the TypeScript-specific mechanism or consequence, without copying the foundational rule. |
| A new source skill is discovered but not protected by regression tests. | Add `typescript` to installer expectations and verify its complete reference inventory in an installed workspace. |
| Imported examples accidentally prescribe framework- or runtime-specific behavior universally. | Preserve project conventions as higher priority and qualify module, runtime, compiler, and validation examples where necessary. |
| Documentation becomes a second detailed rule source. | Keep README changes high-level and link to the skill rather than reproducing its content. |
| Repository-relative policy links break after the skill is copied under `.agents/skills/`. | Refer to root `AGENTS.md` policy in location-independent text and automatically resolve-check every remaining relative link in the installed artifact. |
| TypeScript guidance duplicates general behavioral-testing policy. | Keep general test selection in `pragmatic-functional-programming`; retain only typechecking, type-aware linting, and compile-time type tests in the TypeScript skill. |
| A passing inventory test hides directories or broken links with expected filenames. | Assert that every installed reference is a regular file and validate the installed Markdown link graph structurally. |
| Changes to ignored staging files are missed by ordinary Git checks. | Treat `raw-skills/` as read-only input and compare an explicit before-and-after regular-file inventory and checksum baseline. |
| Removing duplicated functional guidance also removes TypeScript-specific semantics. | Compare every original rule against the combined target and restore language-specific mechanisms that are not actually supplied by `pragmatic-functional-programming`. |
| Canonical interface policy overrides established project conventions more strongly than the original skill. | Add a narrow project-convention or TypeScript-constraint exception while preserving `interface` as the default and prohibiting style-only conversions. |
| Reference routing advertises topics that the reference no longer contains. | Verify routed topics such as `as const` against actual reference content during the source-coverage audit. |
| Examples accidentally recommend empty marker interfaces. | Explain that an existing shared interface should be used directly when it already carries the correct public meaning, and reserve a distinct interface for distinct semantics. |

## Acceptance criteria

- `skills/typescript/` contains a valid dependent `SKILL.md` and the seven routed TypeScript-specific reference files.
- The installed skill contains no `patterns.md`, standalone README, integration example, broken relative link, symlink, or special file; all seven references are regular files.
- References to canonical root `AGENTS.md` policy remain understandable from both source and installed locations without relying on a relative Markdown path that changes meaning after copying.
- The previous `AGENTS.md` TypeScript rules are completely removed rather than merged into or retained alongside the replacement.
- The replacement `AGENTS.md` section is the canonical owner of mandatory TypeScript policy, requires `pragmatic-functional-programming` to load before `typescript`, and applies TypeScript fallback rules only when the foundational skill is available but the TypeScript skill is not.
- The TypeScript frontmatter and first operational instruction declare `pragmatic-functional-programming` as a required prerequisite.
- The dependency is documented as contractual rather than machine-enforced, and installation verifies that both skills are present together.
- The TypeScript skill is never presented as independently usable; when the prerequisite is unavailable, neither the skill nor its fallback is claimed or applied.
- `AGENTS.md`, `SKILL.md`, and the references express one consistent policy for interfaces, type aliases, `Omit`, utility types, runtime validation, and asynchronous errors.
- `pragmatic-functional-programming` has explicit precedence for every overlapping concern.
- The concern-ownership table determines whether guidance belongs to the foundational or TypeScript skill.
- The TypeScript entrypoint and references contain no duplicated normative rules from `pragmatic-functional-programming` or mandatory policy from `AGENTS.md`; short cross-references and TypeScript-specific explanations, mechanisms, permitted exceptions, consequences, and examples remain permitted.
- TypeScript checklists and references do not restate canonical interface, type-alias, `Omit`, utility-type, suppression, narrowing, or floating-Promise policy as independent normative rules.
- `async.md` explains Promise aggregation, rejection, cancellation, and floating-Promise mechanics without deciding whether operations should run concurrently, how concurrency should be bounded, or how errors from ordinary or detached work must be supervised.
- `data-modeling.md` validates values based on trust classification and persistence guarantees rather than treating every database read as untrusted.
- The TypeScript entrypoint and references do not independently define general invalid-state modeling or behavioral-testing requirements; they retain only TypeScript-specific verification mechanisms.
- Every item in the original TypeScript entrypoint and eight references is classified as retained, delegated to the current foundational skill, superseded by canonical policy, or intentionally excluded with a recorded rationale.
- Every normative bullet from the original entrypoint and references is traceable to a coverage-record row; topic aggregation does not hide an unclassified rule or mix concerns requiring different dispositions.
- The entrypoint workflow and completion checklist and the tooling self-review checklist are decomposed into explicit, verifiable dispositions rather than represented by catch-all rows.
- Every `Retained` classification points to target text that materially preserves the original concern; the complex-type decision test is restored or accurately reclassified with rationale.
- TypeScript domain-modeling guidance recommends explicit time, currency, identifier, and optionality models whenever correctness depends on them, without making that recommendation contingent on crossing an untrusted boundary.
- Currency guidance preserves the original requirement for explicit modeling but does not convert the `totalCents` example into a universal representation policy; it permits precision-safe alternatives according to domain and project requirements.
- Async guidance preserves the original timeout-versus-cancellation distinction and explains the TypeScript/JavaScript mechanism without taking operational policy ownership from `pragmatic-functional-programming`.
- Function guidance preserves the original warning against unchanged catch-and-rethrow blocks while allowing catches with meaningful observable responsibility.
- No guidance is classified as delegated merely because it was removed; the cited foundational guidance materially covers the same concern.
- Canonical policy prefers `interface` for named object contracts while permitting object `type` aliases required by established project conventions or TypeScript constraints, and it prohibits style-only conversion of existing code.
- `type-design.md` preserves the original warning against unnecessary empty interface extensions.
- `type-safety.md` contains the advertised `as const` guidance, including literal inference and deep-readonly consequences.
- The TypeScript references preserve the `??` versus `||` distinction and the `return await` stack-trace use case.
- Tooling guidance recommends `strict: true` for new TypeScript projects without silently changing existing-project compiler policy.
- Manual isolated-fixture review confirms prerequisite ordering, conditional fallback, missing-prerequisite behavior, and precedence for overlapping concerns.
- Root and skills-level documentation list the new skill and state its dependency on `pragmatic-functional-programming` at an appropriate level of detail.
- In both README skill lists, `pragmatic-functional-programming` is the first top-level skill and `typescript` is the second; all other top-level skills follow them.
- A clean installation copies the complete TypeScript skill and records it accurately in the canonical manifest.
- A repeated installation is idempotent, and existing installer/uninstaller safety behavior remains intact.
- The complete unit test suite passes.
- The bundled skill validator passes, or its unavailable dependency is disclosed and equivalent manual structural validation is recorded.
- The before-and-after regular-file inventory and checksums confirm that the ignored staging directory under `raw-skills/` is unchanged.
- This plan and the plan index are marked `Implemented` together only after all implementation and verification work is complete.

## Latest alignment audit

The 2026-11-05 structural, ownership, source-coverage, semantic, and documentation-ordering audits confirmed the implementation, installation behavior, and repository documentation below. Every original rule and checklist item is classified at original-rule granularity with verified target mappings, all alignment findings are resolved, and all acceptance criteria pass:

- All 77 unit tests passed.
- An installation dry run and real temporary installation confirmed:
  - Both `pragmatic-functional-programming` and `typescript` are installed alongside existing skills.
  - The complete regular-file tree of `typescript` (entrypoint and seven references) is inventoried in `jolly-roger-skills-manifest.json`.
  - Every expected reference file in the installed skill is verified to be a regular file.
  - Every relative Markdown link in the installed skill resolves within the installed skill tree with zero broken or out-of-tree links.
- Every relative Markdown link to repository-root `AGENTS.md` was replaced with location-independent textual references to `AGENTS.md` and its `## TypeScript Rules` section, resolving cleanly regardless of installation depth.
- Canonical policy repetition in `type-design.md`, independent floating-Promise supervision rules in `async.md`, and general behavioral-test requirements in `SKILL.md`, `type-safety.md`, and `tooling.md` were removed, leaving only TypeScript mechanisms, coupling consequences, and illustrative examples.
- The bundled validator dependency constraint was verified (`ModuleNotFoundError: No module named 'yaml'`); manual structural validation confirmed frontmatter format, `name: typescript`, required prerequisite declaration in description and body, reference routing, absence of placeholders, and clean regular-file tree.
- A regular-file inventory and checksum baseline was captured for the ignored `raw-skills/typescript-skill/` tree before corrective work and re-verified afterward with an exact match across all 12 files.
- The isolated instruction fixtures were executed with the following recorded outcomes:
  - Prerequisite ordering: A TypeScript coding request strictly activates `pragmatic-functional-programming` first as foundational guidance, then `typescript`.
  - Conditional fallback: When `pragmatic-functional-programming` is available but the `typescript` skill is not, the canonical fallback rules in `AGENTS.md` activate: do not introduce `any`, suppressions, or weaker compiler/linter settings; use `unknown`, narrowing, or runtime validation as appropriate when a value crosses a trust boundary identified by `pragmatic-functional-programming` without relying on a TypeScript assertion as runtime validation; and prevent unintended floating promises through type-aware tooling and explicit supervision for intentionally detached work.
  - Missing-prerequisite behavior: When `pragmatic-functional-programming` is unavailable, the agent reports that the required foundation is missing and does not claim or apply either the `typescript` skill or its fallback rules.
  - Overlap precedence: Overlapping concerns (such as mutation ownership, concurrency selection, and boundary trust) are governed by `pragmatic-functional-programming`, while `typescript` supplies only language-level typing and syntax (`readonly` parameters, `Promise.all` semantics, and `unknown` narrowing).

### Source semantic coverage record

The original guidance in `raw-skills/typescript-skill/` was audited against canonical `AGENTS.md`, `skills/typescript/`, and the current authoritative `pragmatic-functional-programming` skill. Every normative rule, recommendation, workflow step, checklist item, and packaging artifact is explicitly classified at original-rule granularity with verified target mappings:

| Original Source | Original Item / Topic | Classification | Disposition / Mapping |
| --- | --- | --- | --- |
| `SKILL.md` | Activation (`.ts`, `.tsx`, tsconfig, API contracts, reviews) | Retained | `skills/typescript/SKILL.md` Activation section |
| `SKILL.md` | Instruction precedence & priority (system/developer, `AGENTS.md`, skill) | Superseded | Canonical repository instruction ordering in `AGENTS.md` |
| `SKILL.md` | Preserving compatibility, established conventions, and framework requirements | Delegated | Owned by `pragmatic-functional-programming` (preserve contracts and observable behavior, respect existing architecture) |
| `SKILL.md` | Instruction standards (MUST safety defaults, narrow exceptions; SHOULD preferences) | Retained / Superseded | Standard library instruction conventions |
| `SKILL.md` | Minimal scope and avoiding unnecessary dependencies | Delegated | Owned by `pragmatic-functional-programming` (minimal scope, no unnecessary abstractions or libraries) |
| `SKILL.md` | Compiler/linter safety (no `any`, `@ts-ignore`, `@ts-nocheck`, weakened settings) | Superseded | Canonical fallback in `AGENTS.md`; explained in `type-safety.md` |
| `SKILL.md` | Untrusted data validation and narrowing at boundaries before domain use | Delegated / Retained | Trust boundaries owned by foundational skill; `unknown` typing & parsing in `data-modeling.md` and `type-safety.md` |
| `SKILL.md` | Promise failure handling and cleanup; no silent discard or floating promises | Superseded / Retained | Canonical fallback in `AGENTS.md`; floating-promise detection in `async.md`; cleanup in foundational skill |
| `SKILL.md` | `interface` vs `type` policy; permit object `type` for project conventions; no style conversion | Superseded | Canonical in `AGENTS.md` (reconciled with project convention exception); mechanism in `type-design.md` |
| `SKILL.md` | Avoid `Omit` in domain models; permit in adapters and integrations | Superseded | Canonical in `AGENTS.md`; coupling examples in `type-design.md` |
| `SKILL.md` | Shallow, cohesive models; split only with meaningful semantics | Superseded | Canonical in `AGENTS.md`; referenced in `type-design.md` |
| `SKILL.md` | Local inference; explicit public boundary types | Retained | `skills/typescript/references/functions.md` |
| `SKILL.md` | Discriminated unions for exclusive states over boolean flags | Retained | `skills/typescript/references/type-design.md` |
| `SKILL.md` | `unknown` over `any`, narrowing over assertions, `satisfies`, and `readonly` | Retained | `skills/typescript/references/type-safety.md` and `type-design.md` |
| `SKILL.md` | Small functions, guard clauses, pure transformations, explicit effect boundaries | Delegated / Retained | Pure transformations and effect boundaries in foundational skill; guard clauses in `functions.md` |
| `SKILL.md` | Simplest correct async flow: sequential for dependencies, bounded concurrency, parallel only for independent work | Delegated / Retained | Concurrency policy and bounds in foundational skill; Promise APIs in `async.md` |
| `SKILL.md` | Generics capturing real type relationships; avoid complex type machinery | Retained | `skills/typescript/references/type-design.md` |
| `SKILL.md` | Advanced TS constructs when justified for correctness/readability | Retained | `skills/typescript/references/type-design.md` |
| `SKILL.md` | Workflow step 1: Inspect affected files, nearby patterns, tsconfig, package scripts, lint/test setup | Retained | `skills/typescript/SKILL.md` (TypeScript workflow step 1) |
| `SKILL.md` | Workflow step 2: Identify contracts, error behavior, trust boundaries, compatibility | Retained | `skills/typescript/SKILL.md` (TypeScript workflow step 2) |
| `SKILL.md` | Workflow step 3: Choose least complex type-safe design; reuse existing or explicit type | Retained | `skills/typescript/SKILL.md` (TypeScript workflow step 3) |
| `SKILL.md` | Workflow step 4: Read relevant references; apply only pertinent | Retained | `skills/typescript/SKILL.md` (TypeScript workflow step 4) |
| `SKILL.md` | Workflow step 5: Minimal, focused changes; framework concerns at edges | Delegated / Retained | Minimal scope and effect boundaries in foundational skill; local inference and explicit boundaries in `skills/typescript/SKILL.md` (TypeScript workflow step 5) |
| `SKILL.md` | Workflow step 6: Run available tests, lint, typecheck; disclose unrun commands | Delegated / Retained | Behavioral tests in foundational skill; typecheck/lint in `skills/typescript/SKILL.md` (TypeScript workflow step 6) |
| `SKILL.md` | Workflow step 7: Review for assertions, `any`, unnecessary composition, missed async errors | Retained | `skills/typescript/SKILL.md` (TypeScript workflow step 7 & Completion checklist) |
| `SKILL.md` | Checklist item 1: Public/domain types express intent without unnecessary composition | Superseded / Retained | Policy canonical in `AGENTS.md`; `skills/typescript/SKILL.md` completion checklist item 1 |
| `SKILL.md` | Checklist item 2: Untrusted inputs narrowed or validated before use | Delegated / Retained | Boundary trust in foundational skill; `skills/typescript/SKILL.md` completion checklist item 2 |
| `SKILL.md` | Checklist item 3: No unjustified `any`, suppressions, assertions, or non-null assertions | Superseded / Retained | Canonical fallback in `AGENTS.md`; `skills/typescript/SKILL.md` completion checklist items 2 & 4 |
| `SKILL.md` | Checklist item 4: Error paths, promise rejection, and cancellation/cleanup considered | Delegated / Retained | Cleanup in foundational skill; Promise rejection and `AbortSignal` in `async.md` |
| `SKILL.md` | Checklist item 5: Existing behavior and compatibility preserved | Delegated | Owned by `pragmatic-functional-programming` (preserve contracts and observable behavior) |
| `SKILL.md` | Checklist item 6: Relevant tests/typecheck/lint run or limitations disclosed | Delegated / Retained | Behavioral testing in foundational skill; typecheck/lint in `skills/typescript/SKILL.md` completion checklist item 5 |
| `SKILL.md` | Standalone integration link (`integrations/README.md`) | Excluded | Packaging artifact; replaced by library installer distribution |
| `type-design.md` | `interface` for stable named object contracts | Superseded / Retained | Policy canonical in `AGENTS.md`; syntax and mechanism in `type-design.md` |
| `type-design.md` | `type` for unions, tuples, primitive aliases, mapped/conditional types, and project-convention object aliases | Superseded / Retained | Policy canonical in `AGENTS.md`; syntax and expressiveness in `type-design.md` |
| `type-design.md` | Avoid deriving domain models via repeated `Omit`, `Pick`, `Partial`, `Required`, intersections | Superseded / Retained | Policy canonical in `AGENTS.md`; coupling examples in `type-design.md` |
| `type-design.md` | Shallow cohesive shapes; do not flatten real nested concepts mechanically | Superseded / Retained | Policy canonical in `AGENTS.md`; referenced in `type-design.md` |
| `type-design.md` | Discriminated unions for exclusive states over boolean flags | Retained | `skills/typescript/references/type-design.md` |
| `type-design.md` | Generics preserving input/output relationships vs unlinked `<T>` | Retained | `skills/typescript/references/type-design.md` |
| `type-design.md` | Utility types for local transformations, generic libraries, and third-party adapters | Superseded / Retained | Policy canonical in `AGENTS.md`; mechanism in `type-design.md` |
| `type-design.md` | Empty interface extension caveat (use shared interface directly when meaning matches) | Retained | `skills/typescript/references/type-design.md` |
| `type-design.md` | Decision test for complex type expressions vs clear named contracts | Retained | `skills/typescript/references/type-design.md` (Decision test section) |
| `type-safety.md` | No `any`, `@ts-ignore`, `@ts-nocheck`, or weakened compiler flags to silence errors | Superseded | Canonical in `AGENTS.md`; mechanism in `type-safety.md` |
| `type-safety.md` | `unknown` at untrusted boundaries, then narrow or validate | Delegated / Retained | Boundary trust in foundational skill; `unknown` typing & narrowing in `type-safety.md` |
| `type-safety.md` | Control-flow narrowing, type guards, and discriminated unions over `as` assertions | Retained | `skills/typescript/references/type-safety.md` |
| `type-safety.md` | Avoid `!` non-null assertions; explicit narrowing via guards | Retained | `skills/typescript/references/type-safety.md` |
| `type-safety.md` | Deliberate modeling of `undefined` (absent) vs `null` (explicit empty) | Retained | `skills/typescript/references/type-safety.md` |
| `type-safety.md` | `satisfies` operator to check contracts while retaining inferred literal types | Retained | `skills/typescript/references/type-safety.md` |
| `type-safety.md` | Narrow assertions at unavoidable framework/library boundaries with invariants | Retained | `skills/typescript/references/type-safety.md` |
| `type-safety.md` | `as const` literal inference and deep-readonly consequence | Retained | `skills/typescript/references/type-safety.md` |
| `type-safety.md` | Avoid non-null assertions in tests | Retained | `skills/typescript/references/type-safety.md` |
| `type-safety.md` | Type erasure: structural types are compile-time only, not runtime schemas | Retained | `skills/typescript/references/type-safety.md` |
| `data-modeling.md`| Validate untrusted boundary data (HTTP, storage, queues, env, SDKs) before use | Delegated / Retained | Boundary trust in foundational skill; parsing and validation in `data-modeling.md` |
| `data-modeling.md`| Distinguish transport DTOs, domain entities, and persistence records | Delegated / Retained | Architectural separation in foundational skill; TypeScript mapping in `data-modeling.md` |
| `data-modeling.md`| Explicit mapping at boundaries where names, dates, or invariants differ | Retained | `skills/typescript/references/data-modeling.md` |
| `data-modeling.md`| Semantic types and meaningful nested concepts vs generic `Record<string, unknown>` | Retained | `skills/typescript/references/data-modeling.md` |
| `data-modeling.md`| Explicit modeling of time, identifiers, and optionality | Retained | `skills/typescript/references/data-modeling.md` (Domain concepts & Optional property semantics sections) |
| `data-modeling.md`| Explicit, precision-safe currency modeling | Retained | `skills/typescript/references/data-modeling.md` (Domain concepts section; context-appropriate precision-safe representations) |
| `data-modeling.md`| Runtime schema libraries (Zod, Valibot, etc.) when adopted; simple guards otherwise | Retained | `skills/typescript/references/data-modeling.md` |
| `data-modeling.md`| Optional property semantics and `exactOptionalPropertyTypes` (`undefined` vs omitted) | Retained | `skills/typescript/references/data-modeling.md` |
| `functions.md` | Type exported/public signatures; rely on natural local inference | Retained | `skills/typescript/references/functions.md` |
| `functions.md` | Domain-specific naming and clear verbs (avoid `processData`) | Delegated | Owned by `pragmatic-functional-programming` (clear domain models, readable composition) |
| `functions.md` | Guard clauses to reduce nesting and enable control-flow narrowing | Retained | `skills/typescript/references/functions.md` |
| `functions.md` | Parameter objects for ambiguous or numerous optional arguments | Retained | `skills/typescript/references/functions.md` |
| `functions.md` | Meaningful errors and preserving error causes (`{ cause: error }`) | Delegated / Retained | Error classification in foundational skill; `{ cause: error }` in `functions.md` |
| `functions.md` | Do not catch solely to rethrow the same error unchanged | Retained | `skills/typescript/references/functions.md` (Error handling and cause preservation section) |
| `functions.md` | Exhaustive union handling with `never` and `assertNever` | Retained | `skills/typescript/references/functions.md` |
| `functions.md` | Result-style unions for expected business failures when project uses them | Retained | `skills/typescript/references/functions.md` |
| `functions.md` | Nullish coalescing (`??`) vs logical OR (`||`) to preserve valid falsy values | Retained | `skills/typescript/references/functions.md` |
| `functions.md` | Async return delegation (direct return vs `return await` inside `try/catch`) | Retained | `skills/typescript/references/functions.md` |
| `functions.md` | Assertion functions (`asserts condition` or `asserts value is Type`) | Retained | `skills/typescript/references/functions.md` |
| `async.md` | Rejection handling and resource release | Delegated / Superseded | Resource cleanup in foundational skill; unhandled rejection in canonical `AGENTS.md` |
| `async.md` | `async`/`await` preference for multi-step operations and error handling | Retained | `skills/typescript/references/async.md` |
| `async.md` | `Promise.all` semantics (independent work, fail-fast without cancellation) | Retained | `skills/typescript/references/async.md` |
| `async.md` | `Promise.allSettled` semantics and bounding concurrency | Delegated / Retained | Concurrency bounds in foundational skill; `Promise.allSettled` in `async.md` |
| `async.md` | Sequential dependent steps and cancellation propagation with `AbortSignal` | Delegated / Retained | Step ordering in foundational skill; `AbortSignal` in `async.md` |
| `async.md` | Supervise detached/fire-and-forget tasks and report errors | Superseded | Canonical fallback in `AGENTS.md`; syntax and examples in `async.md` |
| `async.md` | `return await` for stack traces and local `try/catch` interception | Retained | `skills/typescript/references/async.md` |
| `async.md` | Review prompts for concurrency bounds, error boundaries, and cleanup | Delegated | Owned by `pragmatic-functional-programming` |
| `async.md` | Verify whether timeout aborts underlying work or only stops waiting | Retained | `skills/typescript/references/async.md` (Timeout semantics vs aborting work section) |
| `modules.md` | ES modules and project-standard import/export conventions | Retained | `skills/typescript/references/modules.md` |
| `modules.md` | `import type` for type-only dependencies | Retained | `skills/typescript/references/modules.md` |
| `modules.md` | Module cohesion, avoid cycles, no arbitrary line-count splits | Retained | `skills/typescript/references/modules.md` |
| `modules.md` | Direct imports over barrel cycles; reserve barrels for public package APIs | Retained | `skills/typescript/references/modules.md` |
| `modules.md` | Isolate framework, network, storage, global dependencies from domain | Delegated | Owned by `pragmatic-functional-programming` (isolate I/O and side effects at boundaries) |
| `modules.md` | Minimal exported type and function surface; no unused helper exports | Retained | `skills/typescript/references/modules.md` |
| `modules.md` | Dependency injection where it simplifies testing; not boilerplate | Delegated | Owned by `pragmatic-functional-programming` (explicit dependencies, pragmatic DI) |
| `modules.md` | Module resolution modes and `.js` extension conventions | Retained | `skills/typescript/references/modules.md` |
| `tooling.md` | Compiler `strict: true` (new projects vs migration plans) | Retained | `skills/typescript/references/tooling.md` |
| `tooling.md` | Compiler options (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`) | Retained | `skills/typescript/references/tooling.md` |
| `tooling.md` | Project-standard module and target settings in `tsconfig.json` | Retained | `skills/typescript/references/tooling.md` |
| `tooling.md` | Do not lower compiler strictness to make code pass | Superseded | Canonical in `AGENTS.md`; referenced in `tooling.md` |
| `tooling.md` | Type-aware linting (`typescript-eslint`), floating-promise rules, narrow inline exceptions | Retained | `skills/typescript/references/tooling.md` |
| `tooling.md` | Test observable behavior and failure paths, not declaration-only | Delegated | Owned by `pragmatic-functional-programming` |
| `tooling.md` | Compile-time type tests (`tsd`, `expect-type`) for generic libraries | Retained | `skills/typescript/references/tooling.md` |
| `tooling.md` | Test runtime parsing with malformed and missing data | Delegated | Owned by `pragmatic-functional-programming` |
| `tooling.md` | Test async rejection, cancellation, and cleanup | Delegated | Owned by `pragmatic-functional-programming` |
| `tooling.md` | Script discovery (`package.json`) before running commands | Retained | `skills/typescript/references/tooling.md` |
| `tooling.md` | Review item 1: Unnecessary `Omit`, intersection, generic, or abstraction | Superseded / Retained | Policy canonical in `AGENTS.md`; `skills/typescript/SKILL.md` completion checklist item 1; `type-design.md` |
| `tooling.md` | Review item 2: Type actually enforced at runtime where data is untrusted | Delegated / Retained | Boundary trust in foundational skill; `skills/typescript/SKILL.md` completion checklist item 2; `data-modeling.md` |
| `tooling.md` | Review item 3: Relying on `as`, `!`, `any`, or suppressions | Superseded / Retained | Canonical in `AGENTS.md`; `skills/typescript/SKILL.md` completion checklist items 2 & 4; `type-safety.md` |
| `tooling.md` | Review item 4: Accidental changes to public API or optional-field meaning | Delegated / Retained | Contract preservation in foundational skill; optional-property semantics in `data-modeling.md` and public boundary signatures in `functions.md` |
| `tooling.md` | Review item 5: Promise rejections, cancellation, and cleanup handled | Delegated / Retained | Cleanup in foundational skill; Promise rejection and `AbortSignal` in `async.md` |
| `tooling.md` | Review item 6: Loop simpler than chained functional expression or vice versa | Delegated | Owned by `pragmatic-functional-programming` (compose for clarity, loops allowed when simpler/faster) |
| `tooling.md` | Review item 7: Focused changes and running available checks | Delegated / Retained | Minimal scope in foundational skill; typecheck/lint verification in `skills/typescript/SKILL.md` completion checklist item 5 |
| `tooling.md` | Supporting reference documentation links | Retained | `skills/typescript/references/tooling.md` |
| `patterns.md` | Pure business transformations; isolate I/O at boundaries | Delegated | Owned by `pragmatic-functional-programming` (pure core, effectful boundaries) |
| `patterns.md` | Accept `readonly` collections when function does not mutate input | Retained | Migrated to `skills/typescript/references/type-design.md` |
| `patterns.md` | Immutable updates where state ownership makes mutation risky | Delegated | Owned by `pragmatic-functional-programming` (prefer immutable interfaces) |
| `patterns.md` | Choose `map`/`filter`/`reduce` vs loops based on clarity or efficiency | Delegated | Owned by `pragmatic-functional-programming` (compose for clarity, loops allowed) |
| `patterns.md` | Avoid hidden shared mutable state; explicit dependencies | Delegated | Owned by `pragmatic-functional-programming` (explicit dependencies, no shared mutation) |
| `patterns.md` | Mutate fresh, locally owned data structures for performance/simplicity | Delegated | Owned by `pragmatic-functional-programming` (owned local mutation allowed) |
| `patterns.md` | Use functional libraries already adopted; avoid adding for built-in operations | Delegated | Owned by `pragmatic-functional-programming` (do not introduce FP libraries) |
| `patterns.md` | `toSorted()` alternative for non-mutating sort | Retained | Migrated to `skills/typescript/references/type-design.md` |
| `patterns.md` | Standalone file distribution | Excluded | Deduplicated to prevent competing functional-programming rules |
| Packaging | `README.md`, `integrations/README.md`, `integrations/AGENTS.example.md` | Excluded | Standalone packaging artifacts superseded by library installer |

## Open questions

None.
