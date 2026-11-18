# Async and lifecycle

This reference explains ECMAScript Promise combinators, async iteration, `return await` behavior, and lexical disposal. Whether work may run concurrently, concurrency limits, and cleanup policy are governed by `pragmatic-functional-programming`.

## Wait for the work you start

Prefer `async`/`await` with `try`/`catch` for multi-step asynchronous operations over deeply nested `.then()` and `.catch()` chains, keeping control flow and error handling linear (with readability/composition governed by `pragmatic-functional-programming`).

Return or await promises when callers depend on their completion. Passing an `async` callback to `Array.prototype.forEach` creates promises that `forEach` discards; awaiting `forEach` resolves immediately while work is still in flight. Use `for...of` for sequential async work, or `Promise.all(items.map(...))` for concurrent work. Similarly, avoid starting an unawaited promise before validation gates or early `return` / `throw` branches—an abandoned promise that later rejects becomes an unhandled rejection.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

async function runInOrder(items, work) {
  for (const item of items) {
    await work(item)
  }
}

const log = []
let releaseFirst
const gate = new Promise(resolve => { releaseFirst = resolve })

const task = runInOrder([1, 2], async item => {
  if (item === 1) await gate
  log.push(item)
})

assert(log.length === 0)
releaseFirst()
await task
assert(log[0] === 1 && log[1] === 2)
```

## Choose concurrency and failure semantics

| Requirement | Standard ECMAScript Pattern |
| --- | --- |
| Sequential dependency between steps | `for (const item of items) { await step(item) }` |
| All results required; fail fast on first rejection | `await Promise.all(items.map(step))` |
| Inspect every outcome regardless of individual failures | `await Promise.allSettled(items.map(step))` |
| First fulfilled result wins; ignore rejections unless all fail | `await Promise.any(items.map(step))` |
| First settled outcome (fulfillment or rejection) wins | `await Promise.race(items.map(step))` |
| Bounded concurrency over a large queue | Worker pool loop pulling from a shared iterator |

`Promise.all`, `Promise.race`, and `Promise.any` do not automatically stop sibling promises that were already started; pair them with cooperative cancellation when in-flight work must halt. Note that `Promise.race` against a timer only stops waiting for a settlement—the underlying operation continues running unless cancelled via an explicit signal.

Do not parallelize merely because operations appear independent. Preserve authorization gates, ordering, rate limits, resource limits, and error precedence. Prefer the project's existing limiter or queue; otherwise keep the batch small or implement an explicitly bounded worker pool.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

async function mapWithConcurrency(items, limit, worker) {
  if (!Number.isInteger(limit) || limit < 1) {
    throw new RangeError('Concurrency limit must be a positive integer')
  }

  const results = new Array(items.length)
  const iterator = items.entries()
  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    for (const [index, item] of iterator) {
      results[index] = await worker(item, index)
    }
  })
  await Promise.all(runners)
  return results
}

let inFlight = 0
let maxInFlight = 0
const out = await mapWithConcurrency([10, 20, 30, 40], 2, async n => {
  inFlight += 1
  maxInFlight = Math.max(maxInFlight, inFlight)
  await Promise.resolve()
  inFlight -= 1
  return n * 2
})

assert(maxInFlight <= 2)
assert(out[0] === 20 && out[1] === 40 && out[2] === 60 && out[3] === 80)

let invalidLimitRejected = false
try {
  await mapWithConcurrency([1], 0, async n => n)
} catch (error) {
  invalidLimitRejected = error instanceof RangeError
}
assert(invalidLimitRejected)
```

## Remove accidental request waterfalls

Start independent async branches concurrently before awaiting them, chaining dependent calls immediately onto the branch that produces their input.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

async function loadDashboard(api) {
  const accountBranch = api.getAccount().then(async account => ({
    account,
    orders: await api.getOrders(account.id),
  }))

  const [{ account, orders }, preferences] = await Promise.all([
    accountBranch,
    api.getPreferences(),
  ])
  return { account, orders, preferences }
}

const order = []
const api = {
  async getAccount() { order.push('account'); return { id: 'u1' } },
  async getPreferences() { order.push('preferences'); return { dark: true } },
  async getOrders(id) { order.push(`orders:${id}`); return ['o1'] },
}

const data = await loadDashboard(api)
assert(order[0] === 'account' && order[1] === 'preferences' && order[2] === 'orders:u1')
assert(data.orders[0] === 'o1')
```

Verify failure and side-effect ordering constraints before parallelizing—if an authorization check must reject before another call executes, keep that gate sequential.

## Deterministic cleanup (`try / finally` and `using`)

- Inside a `try` block that owns cleanup or local `catch` interception, always `return await work(resource)` rather than `return work(resource)`. Returning an unawaited promise exits the `try` block immediately, running `finally` before the async work finishes and bypassing `catch` (and can truncate async stack frames). Outside `try` blocks, returning a promise directly is idiomatic when no local error handling is needed.
- When targeting ECMAScript runtimes that support Explicit Resource Management (`Symbol.dispose` and `Symbol.asyncDispose`), `using` and `await using` guarantee deterministic lexical disposal in reverse declaration order when a block exits normally or via exception.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

async function withResource(open, use) {
  const resource = await open()
  try {
    return await use(resource)
  } finally {
    await resource.close()
  }
}

const events = []
let failed = false
try {
  await withResource(
    async () => ({ close: async () => { events.push('close') } }),
    async () => {
      await Promise.resolve()
      events.push('use')
      throw new Error('boom')
    },
  )
} catch {
  failed = true
}
assert(failed && events[0] === 'use' && events[1] === 'close')
```

## Cooperative cancellation and async generators

- Pass an explicit cancellation token/controller (or host-provided signal at the boundary) into long-running operations so callers can stop pending work cleanly.
- Use `async function*` generators to stream paginated or incremental results lazily. Consuming with `for await...of` and exiting early via `break` or `return` invokes the generator's `.return()` method, executing any `finally` block inside the generator.

```js
const assert = (cond, msg = 'Assertion failed') => { if (!cond) throw new Error(msg) }

const events = []
async function* pages() {
  try {
    events.push('open')
    yield 'first'
    yield 'second'
  } finally {
    events.push('closed')
  }
}

for await (const item of pages()) {
  if (item === 'first') break
}
assert(events[0] === 'open' && events[1] === 'closed')
```

## Sources

- [MDN Using promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises)
- [MDN `Promise.allSettled`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled)
- [MDN `for await...of`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for-await...of)
- [MDN `using` declaration](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/using)
