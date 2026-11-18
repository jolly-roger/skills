# Values and runtime validation

This reference covers ECMAScript coercion, equality, precision, and runtime validation mechanics. Where trust boundaries exist is governed by `pragmatic-functional-programming`.

## Default according to the contract

Use `??` when both `null` and `undefined` mean absent. A destructuring default covers only `undefined`. Avoid replacing valid `0`, `false`, or `""` through a truthiness default (`||`). Use a truthiness test only when the contract intentionally treats all falsy values as absent.

In a patch API, check whether a property is own-present when omission and an explicitly supplied `undefined` or `null` have different effects. Use `Object.hasOwn` rather than `in`, which also matches inherited prototype properties.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

const configuredRetries = 0
assert((configuredRetries || 3) === 3)
assert((configuredRetries ?? 3) === 0)

function applyLabelPatch(record, patch) {
  if (!Object.hasOwn(patch, 'label')) return record
  return { ...record, label: patch.label }
}

const omitted = applyLabelPatch({ label: 'draft' }, {})
assert(omitted.label === 'draft')

const cleared = applyLabelPatch({ label: 'draft' }, { label: null })
assert(cleared.label === null)
```

## Equality and numeric precision

- Prefer `===` over loose equality (`==`), which applies implicit `ToPrimitive` and numeric conversions (`"" == 0`, `false == "0"`, `[0] == false`). Use `== null` only when intentionally matching both `null` and `undefined`, and use `Object.is(a, b)` when `NaN` must equal itself or when `-0` must differ from `+0`.
- Guard objects passed into arithmetic, string templates, or relational comparisons (`<`, `>`), where implicit `Symbol.toPrimitive`, `valueOf()`, or `toString()` coercion can throw or produce unexpected strings.
- `Number.isNaN(x)` and `Number.isFinite(x)` do not coerce non-numbers (unlike global `isNaN` and `isFinite`).
- Check `Number.isSafeInteger(n)` before performing integer arithmetic on IDs, counters, or currency minor units; use `BigInt` when values can exceed `Number.MAX_SAFE_INTEGER` (`9007199254740991`), or preserve external identifiers as strings.

## Parse and validate at the entry boundary

At untrusted entry boundaries identified by `pragmatic-functional-programming`, treat parsed JSON, serialized messages, and configuration strings according to their source contract and convert values explicitly before passing them to internal logic.

- `JSON.parse` can return a primitive, an array, `null`, or a plain object. Verify `typeof value === 'object' && value !== null && !Array.isArray(value)` before reading object properties.
- Optional chaining (`?.`) handles absent values; using it on a required field can mask malformed input.
- Validate string syntax before numeric conversion when empty strings (`Number('') === 0`), whitespace, trailing characters (`Number.parseInt('4ms', 10) === 4`), or hex prefixes (`Number('0x10') === 16`) are invalid.
- Parse boolean configuration explicitly; `Boolean('false')` evaluates to `true`.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

function parseRetries(raw) {
  if (raw === undefined) return 3
  if (typeof raw !== 'string' || !/^[0-9]+$/.test(raw)) {
    throw new TypeError('RETRIES must contain decimal digits')
  }

  const retries = Number(raw)
  if (!Number.isSafeInteger(retries) || retries > 10) {
    throw new RangeError('RETRIES must be between 0 and 10')
  }
  return retries
}

assert(Number('') === 0)
assert(Number.parseInt('4ms', 10) === 4)
assert(parseRetries('0') === 0)
assert(parseRetries(undefined) === 3)

for (const invalid of ['', ' ', '4ms', '0x2', '1.5', '11', '9007199254740993']) {
  let threw = false
  try { parseRetries(invalid) } catch { threw = true }
  assert(threw, `Expected failure for ${JSON.stringify(invalid)}`)
}
```

## Guard dynamic keys and regular expressions

- **Prototype pollution:** Never assign untrusted property paths to ordinary objects without validation. `__proto__` can alter an object's prototype, while `constructor` and `prototype` can participate in nested pollution paths or collide with inherited members. Use a `Map`, a null-prototype object (`Object.create(null)`), or an explicit key allowlist.
- **Dynamic regular expressions:** Do not interpolate untrusted text as regular-expression syntax. When the input is intended to be literal text, escape it with `RegExp.escape(input)` where supported or the project's established compatibility helper. If callers intentionally supply patterns, validate complexity and constrain input separately.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

const FORBIDDEN_KEYS = new Set(['__proto__', 'constructor', 'prototype'])

function setSafeEntry(dict, key, value) {
  if (typeof key !== 'string' || FORBIDDEN_KEYS.has(key)) {
    throw new TypeError(`Unsafe property key: ${String(key)}`)
  }
  dict[key] = value
}

const safeDict = Object.create(null)
setSafeEntry(safeDict, 'theme', 'dark')
assert(safeDict.theme === 'dark')
assert(safeDict.toString === undefined)

let polluted = false
try { setSafeEntry(safeDict, '__proto__', {}) } catch { polluted = true }
assert(polluted && ({}).polluted === undefined)
```

## Unicode strings and serialization semantics

- Standard `str.length` and `str.slice()` count UTF-16 code units and can split surrogate pairs (emoji, supplementary planes) or combining grapheme clusters. Iterate code points with `for (const cp of str)` / `[...str]`, or segment user-perceived characters with `Intl.Segmenter`.
- `JSON.stringify` omits object properties whose value is `undefined`, serializes `undefined` array elements as `null`, and throws `TypeError` if it encounters a `BigInt` or circular reference. Assert wire output directly when omission or explicit `null` matters.

## Sources

- [ECMA-262 Language Specification](https://tc39.es/ecma262/)
- [MDN Nullish coalescing (`??`)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing)
- [MDN `Object.hasOwn`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/hasOwn)
- [MDN `Object.is`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/is)
- [MDN `JSON.stringify`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify)
