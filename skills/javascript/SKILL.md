---
name: javascript
description: >
  Write, modify, test, debug, or review ECMAScript / JavaScript (.js, .jsx, .mjs,
  .cjs) in any host environment, and provide canonical ECMAScript runtime semantics
  for TypeScript (.ts, .tsx) and JavaScript-ecosystem specializations. Trigger for
  JavaScript language semantics, JSDoc-typed JS, runtime input validation, equality
  and coercion, object and collection ownership, prototypes and classes, error
  boundaries, promises and async generators, explicit resource management (`using`),
  or ES module graphs. Builds on `pragmatic-functional-programming` as Tier 1
  foundation.
---

# Canonical JavaScript

This skill is the Tier 2 canonical ECMAScript specification. It defines JavaScript language semantics and runtime mechanisms for plain JavaScript, JSDoc-typed JavaScript, and derived specializations such as `typescript`.

## Prerequisite and precedence

1. **Prerequisite**: Load and apply `pragmatic-functional-programming` first for general engineering decisions (data vs. calculations vs. actions, trust-boundary placement, mutation ownership, error and fallback policy, concurrency/cancellation policy, and behavioral test scope).
2. **Precedence**: `pragmatic-functional-programming` has higher priority wherever both skills address general engineering decisions. `javascript` is authoritative for ECMAScript language semantics and runtime mechanisms, and serves as the Tier 2 runtime base for Tier 3 specializations (`typescript`, host runtimes, frameworks).
3. **Missing prerequisite**: If `pragmatic-functional-programming` cannot be loaded, report that the required foundational skill is unavailable and do not apply or claim to have applied `javascript`.

## Workflow

1. **Identify language baseline & host:** Check the project's supported ECMAScript features, actual runtime or build target, framework/loader behavior, and existing code conventions before selecting syntax or APIs.
2. **Map observable contracts:** Check accepted inputs and outputs, optional vs. omitted keys, mutable data ownership, callback receiver and argument arity, and how callers observe errors or completion.
3. **Trace state & lifecycles:** Identify who starts, awaits, cancels, and cleans up (`finally` or `using`) each operation. Preserve behavior on success, failure, and retry unless changing the contract.
4. **Route to the right reference:** Load only the reference file(s) matching the task before making non-trivial edits.
5. **Verify contracts & edge cases:** Exercise deterministic tests covering falsy values, omission, mutation ownership, async ordering, and error paths, and run the project's existing checks.

## Core Rules

- **Boundary validation:** At trust boundaries identified by `pragmatic-functional-programming`, parse and normalize external data once using ECMAScript-safe checks. Preserve valid falsy values (`0`, `false`, `""`) with `??`, distinguish omitted properties from `undefined`/`null` with `Object.hasOwn`, and guard dynamic property writes against prototype pollution.
- **Ownership & collections:** Where `pragmatic-functional-programming` requires preserving caller-owned inputs, copy only the nested levels a change mutates and avoid in-place `sort`/`reverse`/`splice` on shared arrays.
- **Functions & errors:** Bind or wrap detached methods before passing as callbacks. Following `pragmatic-functional-programming`'s error policy, enrich wrapped failures with `new Error(msg, { cause })` or `AggregateError`, and avoid converting failed operations into silent empty fallbacks unless explicitly contracted.
- **Async & lifecycle:** Never pass an `async` callback to `forEach`. When `pragmatic-functional-programming` permits concurrent execution, choose Promise combinator failure semantics deliberately, bound concurrency, propagate cooperative cancellation, and release resources via `return await` inside `try / finally` or supported `using` / `await using` blocks.
- **ES modules & portability:** Respect live read-only ES module bindings and module evaluation order. Treat cycles that access uninitialized bindings or create unresolved async dependencies as hazards. Isolate host-specific APIs behind explicit boundaries when a module is intended to be portable.

## Reference Routing

| Symptom or Task | Reference File |
| --- | --- |
| Defaults (`\|\|` vs `??`), `==` coercion, `Object.is`, `BigInt`, UTF-16 vs code points, `RegExp.escape`, prototype pollution, JSON semantics | [references/values-and-validation.md](references/values-and-validation.md) |
| Shallow copy aliasing, `WeakMap`/`WeakSet` tracking, class/private-field/`Proxy` behavior, mutating vs copying array methods, `Map`/`Set` operations, `Iterator` helpers | [references/objects-and-collections.md](references/objects-and-collections.md) |
| Detached `this`, `map(parseInt)` hazards, callback identity, error wrapping (`cause`), `AggregateError`, `Error.isError`, `Promise.try` | [references/functions-and-errors.md](references/functions-and-errors.md) |
| `async forEach`, waterfalls, `Promise.all` vs `allSettled`, `try/finally` return traps, `using` disposal, cooperative cancellation, async generators | [references/async-and-lifecycle.md](references/async-and-lifecycle.md) |
| ES module live bindings, evaluation order, top-level `await` cycles, dynamic `import()`, import attributes, host capability injection | [references/modules-and-boundaries.md](references/modules-and-boundaries.md) |
| Deterministic unit verification, JSDoc type contracts vs runtime guards, regression test checklists | [references/verification-and-contracts.md](references/verification-and-contracts.md) |

## Completion Checklist

- [ ] Input, output, error, and mutation contracts are preserved (unless explicitly changed).
- [ ] Syntax and built-ins match the supported language baseline and actual host environment.
- [ ] Async work is awaited or supervised by its owner and resources are released on all exit paths.
- [ ] Edge cases (falsy values, omission, duplicates, empty inputs, rejections) are verified with deterministic assertions.
