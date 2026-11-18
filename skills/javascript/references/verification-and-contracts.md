# Verification and contracts

This reference covers JSDoc type erasure vs. runtime guards and JavaScript-specific regression checks. What observable behavior and invariants require tests is governed by `pragmatic-functional-programming`.

## Separate static contracts from runtime guards

- **JSDoc contracts:** Use standard JSDoc annotations (`@typedef`, `@param`, `@returns`, `@template`) on public and shared module boundaries when the repository uses static type checking over JavaScript. Let inference handle straightforward local variables.
- **Runtime boundary validation:** Static JSDoc types are erased at runtime and provide zero protection against malformed external payloads. Always pair JSDoc contracts with explicit runtime checks at trust boundaries.

```js
/** @typedef {{ retries: number, enabled: boolean }} RetryPolicy */

/**
 * @param {RetryPolicy} policy
 * @returns {boolean}
 */
function shouldRetry({ retries, enabled }) {
  return enabled && Number.isFinite(retries) && retries > 0
}
```

## Write deterministic verification tests

- Keep unit tests focused on observable input-to-output behavior and error contracts rather than internal implementation details.
- Use the project's existing seams for fake clocks, deterministic PRNGs, and in-memory stubs. Introduce dependency parameters or adapters when they clarify a real boundary rather than solely to satisfy a test.
- Adapt test syntax to the repository's existing test runner and assertion library without introducing unrequested dependencies.

## Regression checklist by change category

| Change Category | Required Verification Cases |
| --- | --- |
| Defaults & coercion | Valid falsy inputs (`0`, `false`, `""`), `null` vs `undefined`, omitted keys, and malformed types. |
| Object & array updates | Returned value accuracy AND proof that caller-owned input objects/arrays were not mutated. |
| Callbacks & listeners | Correct `this` receiver binding, extra callback arguments ignored, and unregistration by identity. |
| Async & lifecycles | Completion ordering, rejection propagation, `Error.cause` preservation, cancellation, and `finally` cleanup. |
| Module boundaries | Public named/default export shapes, circular-dependency safety, and host APIs matching the intended runtime. |

## Sources

- [TypeScript JSDoc Reference](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html)
- [MDN Strict mode](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode)
