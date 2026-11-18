# Objects and collections

This reference explains ECMAScript object copying, prototype/slot semantics, and collection/iterator behavior. Whether mutation is safely owned is governed by `pragmatic-functional-programming`.

## Respect ownership when updating data

Object and array spread (`{ ...obj }`, `[...arr]`) are shallow. Updating a nested property through a shallow copy mutates the caller's original nested object. When callers own the input, copy the affected path and reuse untouched subtrees when structural sharing is safe under the contract. Local mutation of an accumulator created inside a function is often clearer and faster than reallocating on every step. When derived metadata should follow the lifetime and identity of caller-owned objects, consider a `WeakMap` keyed by the object instead of attaching expando properties to the input. This avoids mutating the input and does not keep keys alive solely for the metadata cache. Similarly, use a `WeakSet` to track object references without mutating inputs or keeping them alive. A global visited set detects repeated references; when shared nodes are valid and only cycles should fail, track the active traversal path and remove each object when leaving that path.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

function updateWithAliasing(profile) {
  const next = { ...profile }
  next.preferences.email = false
  return next
}

function updateEmailPreference(profile, email) {
  return {
    ...profile,
    preferences: { ...profile.preferences, email },
  }
}

const shared = { preferences: { email: true } }
updateWithAliasing(shared)
assert(shared.preferences.email === false)

const original = { preferences: { email: true }, badges: ['member'] }
const updated = updateEmailPreference(original, false)
assert(original.preferences.email === true)
assert(updated.preferences.email === false)
assert(updated.badges === original.badges)
```

## Preserve prototypes, internal slots, and `Proxy` targets

- Spreading a class instance copies only own enumerable properties into a plain object, stripping prototype methods and private fields (`#field`). Copy instances through a constructor, clone method, or explicit factory.
- Built-in objects with internal slots (`Map`, `Set`, `Date`, `RegExp`, `TypedArray`) and classes with `#private` fields perform strict receiver brand checks. Calling a method through a `Proxy` whose `this` is the proxy instead of the underlying target throws `TypeError` unless methods are bound to the target.

## Match collection and iterator operations to intent

- Use `find` for the first match, `some` for existence, `every` for universal checks, `filter` for subsets, and `map` for 1-to-1 projections. Prefer a `for...of` loop for coupled state, early exit, or ordered side effects.
- `sort`, `reverse`, and `splice` mutate in place. Copy before sorting (`[...arr].sort(cmp)`) or use non-mutating `toSorted`, `toReversed`, and `toSpliced` when supported. Always provide a numeric comparator (`(a, b) => a - b`) when sorting numbers, because default `sort()` converts elements to UTF-16 strings.
- For large or lazy sequences, use `Iterator` helpers (`.filter()`, `.map()`, `.take()`, `.drop()`) to avoid allocating intermediate arrays when the supported baseline provides them.
- Prefer standard `Set` composition methods and `Object.groupBy()` / `Map.groupBy()` over ad-hoc reducer boilerplate when the supported baseline provides them and they make the intent clearer.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

const durations = [12, 2, 5]
const lexSorted = [...durations].sort()
assert(lexSorted[0] === 12 && lexSorted[1] === 2 && lexSorted[2] === 5)

const numSorted = [...durations].sort((a, b) => a - b)
assert(numSorted[0] === 2 && numSorted[1] === 5 && numSorted[2] === 12)
assert(durations[0] === 12)
```

## Index repeated lookups

Build a `Set` or `Map` index once when querying a collection repeatedly inside a loop (`O(N + M)` instead of `O(N * M)`).

- Use `map.has(key)` when `undefined` is a valid stored value, since `map.get(key)` returns `undefined` for both missing keys and keys mapped to `undefined`.
- `Map` and `Set` compare keys with `SameValueZero` (`NaN` equals `NaN`, `-0` equals `+0`).
- Preserve duplicate-key semantics when replacing a linear scan (`Array.prototype.find` keeps the first match, whereas `new Map(entries)` keeps the last).

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

function joinByIndex(orders, users) {
  const firstUserById = new Map()
  for (const user of users) {
    if (!firstUserById.has(user.id)) firstUserById.set(user.id, user)
  }
  return orders.map(order => ({ ...order, user: firstUserById.get(order.userId) }))
}

const users = [
  { id: 'u1', name: 'First' },
  { id: 'u1', name: 'Duplicate' },
]
const orders = [
  { id: 'o1', userId: 'missing' },
  { id: 'o2', userId: 'u1' },
]

const joined = joinByIndex(orders, users)
assert(joined[0].user === undefined)
assert(joined[1].user === users[0])
```

## Sources

- [MDN Spread syntax](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_syntax)
- [MDN `Array.prototype.sort`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort)
- [MDN `Map`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Map)
- [MDN `Set`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set)
- [MDN `Iterator` helpers](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Iterator)
