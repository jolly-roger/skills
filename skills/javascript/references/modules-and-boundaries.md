# ES modules and host boundaries

This reference explains ES module runtime semantics, initialization cycles, dynamic loading, and feature detection. Architectural module-boundary decisions (such as whether a curated public barrel is appropriate) and effect isolation are governed by `pragmatic-functional-programming`.

## Understand ES module semantics

- **Strict mode by default:** Every ES module executes in strict mode (`this` at top level is `undefined`, undeclared assignments throw `ReferenceError`, duplicate parameter names are syntax errors).
- **Live read-only bindings:** Named exports expose live bindings to the exporting module's binding, not static value copies. Importers always observe the exporter's current value, and importers cannot reassign an imported binding directly.
- **Static graph & evaluation order:** Static `import` declarations are hoisted and resolved before module body execution. Modules evaluate depth-first in post-order, and each module executes at most once per module graph regardless of how many files import it.

```js
// counter.js
export let count = 0
export function increment() {
  count += 1
}

// consumer.js: importing `count` observes live updates after `increment()`
```

## Avoid circular dependencies and top-level `await` hazards

- **Synchronous cycles:** Circular static imports (including re-exporting barrel files that create cycles) can leave imported `let`/`const` bindings in the Temporal Dead Zone (`ReferenceError: Cannot access '...' before initialization`, or `undefined` under transpiled semantics) if accessed during top-level evaluation. Break cycles by importing directly from leaf modules, extracting shared primitives into a leaf module, or deferring access inside functions.
- **Top-level `await` (TLA) cycles:** A cycle containing top-level `await` is not automatically invalid. Depending on the dependency and evaluation graph, it may complete, expose a binding before initialization, or create async dependencies that never resolve. Keep top-level `await` at application entry leaves when practical, or expose explicit initialization functions so ordering and ownership are visible.

## Dynamic `import()` and import attributes

- Use dynamic `import(specifier)` when loading optional modules conditionally, breaking synchronous dependency cycles, or deferring heavy code until needed. Handle rejection from `import()` just like any promise.
- Use standard import attributes (`import data from './config.json' with { type: 'json' }`) when importing non-JavaScript artifacts supported by the host loader, rather than assuming implicit format sniffing.

## Isolate host capabilities behind explicit boundaries

When a module is intended to be reusable across hosts, keep the portable core separate from host adapters as established by `pragmatic-functional-programming`:

- **Make host dependencies explicit:** Use an adapter, parameter, or factory for clocks, storage, logging, transport, and similar capabilities when portability or deterministic testing requires it. Do not impose this architecture on host-specific modules that already follow clear project conventions.
- **Preserve public export shapes:** Maintain existing named exports, default exports, and subpath entry points when refactoring internal module structure.
- **Guard feature detection when required:** If a thin adapter must detect an optional language or host capability at runtime, check `typeof globalThis.Feature !== 'undefined'` explicitly rather than assuming its presence.

## Sources

- [MDN JavaScript modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [MDN `import()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/import)
- [MDN Import attributes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import/with)
