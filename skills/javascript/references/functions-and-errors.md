# Functions and errors

This reference covers ECMAScript function receiver/arity mechanics and error-wrapping primitives. Error propagation, recovery, fallback policy, and when parameter objects improve API clarity are governed by `pragmatic-functional-programming`.

## Make call contracts clear

- When `pragmatic-functional-programming` favors a parameter object for multiple optional or same-typed parameters, use a single destructured options object (`fn({ timeout, retries } = {})`).
- Preserve existing public function signatures and return shapes during focused fixes.
- When passing a method as a callback, preserve its receiver (`id => formatter.format(id)` or `formatter.format.bind(formatter)`). A detached method runs with `this === undefined` in strict mode / ES modules.
- Wrap callbacks when the caller supplies extra positional arguments that the callee interprets (such as `Array.prototype.map` passing `(value, index, array)` to `Number.parseInt`, where `index` becomes the radix).
- When a registry removes listeners by function identity, store the exact bound or wrapped reference used during registration; calling `.bind()` twice creates two distinct function objects.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

const formatter = {
  prefix: '#',
  format(id) {
    return this.prefix + id
  },
}

let detachedFailed = false
try { [1, 2].map(formatter.format) } catch (err) { detachedFailed = err instanceof TypeError }
assert(detachedFailed)

const formatted = [1, 2].map(id => formatter.format(id))
assert(formatted[0] === '#1' && formatted[1] === '#2')

const badRadix = ['10', '10', '10'].map(Number.parseInt)
assert(badRadix[0] === 10 && Number.isNaN(badRadix[1]) && badRadix[2] === 2)

const parsed = ['10', '10', '10'].map(value => Number.parseInt(value, 10))
assert(parsed[0] === 10 && parsed[1] === 10 && parsed[2] === 10)
```

## Preserve failure behavior and error chains

- Follow the existing codebase's error convention (thrown `Error` subclasses vs. explicit `{ ok, value, error }` result objects).
- Catch an error only when the current layer can recover, clean up resources, or enrich it with domain context.
- Preserve the underlying failure via `new Error('Contextual message', { cause })` so diagnostic chains remain intact.
- Use standard `new AggregateError(errors, 'Summary message')` when surfacing multiple independent failures together (such as rejected outcomes collected from `Promise.allSettled`).
- JavaScript allows throwing any value (strings, numbers, `null`, plain objects). Treat caught values as `unknown`/opaque unless verified, and always throw genuine `Error` instances for new failures.
- Use `Error.isError(value)` when the supported baseline provides it and errors must be classified across realms where `value instanceof Error` can return `false`; otherwise follow the project's compatibility approach.
- Where the supported baseline provides it, `Promise.try(() => fn())` can normalize callbacks that may either throw synchronously or return a rejected promise. Otherwise use the project's existing equivalent.
- Never convert a failed I/O or parse operation into a silent empty fallback (`[]` or `{}`) unless the contract explicitly defines degraded fallback behavior.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

async function loadConfig(parse, readSource) {
  let raw
  try {
    raw = await readSource()
  } catch (cause) {
    throw new Error('Failed to load configuration source', { cause })
  }
  return parse(raw)
}

const rootCause = new Error('storage offline')
let caught = null
try {
  await loadConfig(JSON.parse, async () => { throw rootCause })
} catch (err) {
  caught = err
}
assert(caught instanceof Error && caught.cause === rootCause)

const outcomes = await Promise.allSettled([
  Promise.resolve('ok'),
  Promise.reject(new Error('first failure')),
  Promise.reject(new Error('second failure')),
])
const errors = outcomes.filter(r => r.status === 'rejected').map(r => r.reason)
const summary = new AggregateError(errors, 'Batch failed')
assert(summary instanceof AggregateError && summary.errors.length === 2)
```

## Sources

- [MDN `this` operator](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this)
- [MDN `Error.prototype.cause`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/cause)
- [MDN `Error.isError`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/isError)
- [MDN `Promise.try`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/try)
