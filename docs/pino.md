# Pino Interoperability

A Python service raises a DataExcept exception. A Node.js service downstream
reads the failure off a queue, an HTTP response or a log stream — and its
logger has opinions. [Pino](https://getpino.io)'s error serializer emits
`type`, `message` and `stack`, and everything after it — pino-pretty,
transports, error trackers — keys on those names.

The **Pino profile** is DataExcept's answer to that: a projection of the
[envelope](envelope_schema.md) onto the value Pino logs under its error key.

- **Profile:** [`pino-1.0.0.json`](schema/pino-1.0.0.json)
- **`$id`:** `https://diogoribeiro7.github.io/DataExcept/schema/pino-1.0.0.json`
- **Projected from:** envelope schema 1.0.0

The envelope stays canonical. Pino's shape does not get to decide what
DataExcept records, and nothing here is a dependency: no Node.js, no Pino, no
JavaScript anywhere in the Python package.

## What the projection changes

Three things, and nothing else.

Envelope | Pino profile | Why
-------- | ------------ | ---
`exceptions` | `errors` | What JavaScript's `AggregateError` calls the same thing.
— | `stack` | Emitted **only** when a real stack representation exists. Never invented.
`attributes` | `attributes` | Deliberately *not* spread onto the error. Spreading is the obvious move, and it is how an attribute called `type` or `stack` silently overwrites the fields the consumer keys on.

`type` and `message` already agree — Pino's own serializer emits the
constructor name under `type`, which is what the envelope carries. `module`,
`failure`, `cause`, `context`, `cycle` and `truncated` come through unchanged,
with the redaction already applied to them intact.

## From Python

```python
from dataexcept import exception_to_pino

try:
    ingest(batch)
except DataExceptError as exc:
    logger.error({"err": exception_to_pino(exc), "msg": "ingest failed"})
```

`include_stack=True` renders the exception's own traceback, redacted like any
other exported string. It is omitted, not fabricated, when the exception was
never raised and so has no traceback:

```python
from dataexcept import exception_to_pino

record = exception_to_pino(exc, include_stack=True)
```

If you already hold an envelope — one that arrived over a boundary, say —
project that instead, optionally supplying a stack you were given:

```python
from dataexcept import envelope_to_pino

record = envelope_to_pino(envelope, stack=received_stack)
```

## From JavaScript

A Node service that receives the **envelope** can project it itself. The rules
are small enough to restate, and this is the whole of them:

```js
const CARRIED = [
  'type', 'module', 'message', 'attributes', 'failure', 'cycle', 'truncated',
]

const isRecord = (value) =>
  value !== null && typeof value === 'object' && !Array.isArray(value)

export function envelopeToPino (node) {
  if (!isRecord(node)) return { truncated: true }

  const record = {}
  for (const field of CARRIED) {
    if (field in node) record[field] = node[field]
  }
  for (const field of ['cause', 'context']) {
    if (isRecord(node[field])) record[field] = envelopeToPino(node[field])
  }
  if (Array.isArray(node.exceptions)) {
    record.errors = node.exceptions.filter(isRecord).map(envelopeToPino)
  }
  return record
}
```

Then hand it to Pino. The value is already in the shape Pino's serializer
produces, so it needs no serializer of its own:

```js
import pino from 'pino'

const logger = pino()

logger.error({ err: envelopeToPino(envelope) }, 'ingest failed')
```

If the Python side already projected, pass it through unchanged:

```js
logger.error({ err: payload.err }, 'ingest failed')
```

In TypeScript, the profile is a small recursive type:

```ts
type PinoNode = TruncationMarker | CycleRecord | ErrorRecord

interface TruncationMarker { truncated: true }

interface CycleRecord {
  type: string
  module: string
  message: string
  cycle: true
}

interface ErrorRecord {
  type: string
  module: string
  message: string
  stack?: string
  attributes?: Record<string, unknown>
  failure?: {
    kind: 'transient' | 'permanent' | 'unknown'
    retryable: boolean | null
    retry_after_seconds: number | null
  }
  cause?: PinoNode
  context?: PinoNode
  errors?: PinoNode[]
}
```

## Testing your implementation against ours

Every published envelope fixture has its projection published beside it, under
the same name:

```text
docs/schema/fixtures/redaction.json         <- what DataExcept emits
docs/schema/fixtures/pino/redaction.json    <- what Pino should receive
```

Neither file is written by hand: one is the serializer's output for a real
exception, the other is that output run through the projection. So a reader in
another language can check itself against the pair rather than against prose:

```js
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readdirSync, readFileSync } from 'node:fs'

const read = (path) => JSON.parse(readFileSync(path, 'utf8'))

for (const file of readdirSync('fixtures').filter((f) => f.endsWith('.json'))) {
  test(`projects ${file}`, () => {
    assert.deepEqual(
      envelopeToPino(read(`fixtures/${file}`)),
      read(`fixtures/pino/${file}`),
    )
  })
}
```

The eight cases are the ones listed on the
[envelope schema](envelope_schema.md#fixtures) page: an ordinary exception, an
explicit cause, failure metadata, an implicit context, nested exception groups,
redaction, truncation and a cycle.

## Three nodes, not one

Like the envelope, a projected node is one of three kinds, and they are
mutually exclusive by shape:

- an **error record**, with `type`, `module` and `message`;
- a **cycle record**, which adds `cycle: true` and carries nothing else, so
  following `cause` always terminates;
- a **truncation marker**, `{ "truncated": true }` and nothing more, standing
  in for a child past the envelope's depth budget.

The markers are carried through rather than dressed up as errors. A projection
that invented a `type` and `message` for them would be reporting a failure that
never happened, which is a worse answer than a node the consumer has to check
for.

## What is deliberately not here

- **No Node.js dependency**, in either direction. The Python package gains
  nothing but a JSON document and a function that renames one field.
- **No npm package.** A published adapter would be a separate artifact with its
  own release cycle; the profile and its fixtures are what make one writable in
  an afternoon.
- **No fabricated stacks.** A missing `stack` means none was available — not
  that the failure had none. Pino consumers treat that field as ground truth,
  which is exactly why it must not be guessed.
