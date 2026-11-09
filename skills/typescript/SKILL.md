---
name: typescript
description: >
  Apply pragmatic, maintainable TypeScript practices for type modeling,
  safety, runtime boundaries, async execution, modules, and tooling. Requires
  the pragmatic-functional-programming skill as a foundation and is not intended
  for standalone use.
---
# Pragmatic TypeScript

Apply this guidance to TypeScript and TSX code, including new code, modifications, bug fixes, type definitions, and code reviews. This skill is a dependent language specialization; it supplies TypeScript-specific mechanisms, explanations, and tooling that build on foundational engineering principles.

## Prerequisite and precedence

1. **Prerequisite**: For every TypeScript or TSX coding task, load and apply `pragmatic-functional-programming` first as the foundation for data, calculations, actions, mutation ownership, effects, dependencies, domain modeling, error policy, and general testing.
2. **Precedence**: `pragmatic-functional-programming` is authoritative and has higher priority wherever both skills address the same concern. This skill refines how a general principle is expressed in TypeScript, but does not relax, override, or independently redefine foundational principles. TypeScript-specific guidance remains authoritative where the foundational skill has no language-specific rule.
3. **Missing prerequisite**: If `pragmatic-functional-programming` cannot be loaded, report that the TypeScript skill's required foundation is unavailable. Do not apply or claim to have applied the TypeScript skill or its TypeScript fallback rules. Continue only under higher-priority instructions and ordinary project guidance.

## Policy alignment

Mandatory policies for interfaces, type aliases, `Omit`, utility types, trust boundaries, and floating promises are canonically owned by `AGENTS.md` under `## TypeScript Rules`. This skill provides TypeScript-specific explanations, mechanisms, permitted exceptions, and examples that support those policies.

## TypeScript workflow

1. Inspect `tsconfig.json`, package scripts, module settings, and project lint/typecheck configuration.
2. Identify type contracts: exported API surfaces, public interfaces, trust boundaries identified by the foundational skill, and runtime compatibility constraints.
3. Choose the least complex type-safe design in alignment with `AGENTS.md` policy and the references below.
4. Read only the references pertinent to the task.
5. Implement focused changes: rely on local inference, type public boundaries explicitly, and avoid unnecessary type-level machinery.
6. Run available typecheck (`tsc --noEmit`) or lint commands. Disclose what was not run and why if commands are unavailable.
7. Review changes using the checklist below.

## Reference selection

Read only the references relevant to the task:

- [Type design](references/type-design.md) — TypeScript mechanisms for interfaces, type aliases, discriminated unions, utility types, readonly collections, and generics.
- [Type safety and narrowing](references/type-safety.md) — TypeScript narrowing mechanisms, `unknown`, user-defined type guards, avoiding assertions, `satisfies`, and `as const`.
- [Functions, signatures, and flow](references/functions.md) — signature typing, return inference, exhaustive union handling with `never`, and async returns.
- [Domain models and runtime boundaries](references/data-modeling.md) — runtime type erasure, parsing `unknown` payloads, schema validation, and optional-property semantics.
- [Async, concurrency, and cancellation](references/async.md) — observable semantics of `Promise.all` and `Promise.allSettled`, floating promise detection, `AbortSignal`, and `return await`.
- [Modules and dependency boundaries](references/modules.md) — `import type`, module-resolution conventions, barrel exports, and minimal public type surface.
- [Tooling, tests, and verification](references/tooling.md) — compiler strictness options, type-aware linting, compile-time type tests, and script discovery.

## Completion checklist

- [ ] Interfaces, type aliases, `Omit`, and model composition follow canonical `AGENTS.md` policy under `## TypeScript Rules`.
- [ ] Trust boundary values, compiler suppressions, and floating promises comply with `AGENTS.md` safety and fallback rules under `## TypeScript Rules`.
- [ ] Type design applies TypeScript mechanisms (discriminated unions, `never`, `readonly`) without unnecessary type machinery.
- [ ] Non-null assertions (`!`) and type assertions (`as`) are avoided or justified at unavoidable boundaries.
- [ ] Available typecheck (`tsc --noEmit`) and lint commands were executed, or limitations disclosed.
