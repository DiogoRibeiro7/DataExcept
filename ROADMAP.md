# Roadmap

Where DataExcept is going, and what has already landed. For what is guaranteed
not to break, see the [stability policy](https://diogoribeiro7.github.io/DataExcept/stability/).

## Shipped in 0.1.0

The original 0.2–0.5 milestones are done:

- **Published to PyPI** — `pip install DataExcept`, released through OIDC
  trusted publishing with no long-lived token.
- **98 exception classes** across job, pipeline, data science, data
  engineering, pandas, database, network, I/O and security domains.
- **Logging helpers** — `log_exception`, `log_and_raise` and `log_then_raise`
  attach structured context and preserve tracebacks.
- **Full typing** — `py.typed` ships, and mypy runs clean in CI, so downstream
  type checkers get accurate annotations.
- **CI on every push** — lint, format, type check and tests across Python
  3.10–3.14, with coverage published alongside the docs.
- **Documentation** at
  [diogoribeiro7.github.io/DataExcept](https://diogoribeiro7.github.io/DataExcept/),
  with an API reference generated from the source.

## Shipped in 0.2.0

- **Security and complexity scanning** — CodeQL, pip-audit, and ruff's bandit
  and mccabe rule sets.
- **PEP 621 metadata** and a published
  [API stability policy](https://diogoribeiro7.github.io/DataExcept/stability/).
- **Stopped shadowing builtins.** `ConnectionError` and `TimeoutError` became
  `ServiceConnectionError` and `OperationTimeoutError`. The old names shared
  their names with Python builtins without inheriting from them, so
  `from dataexcept import ConnectionError` silently stopped
  `except ConnectionError:` catching real socket failures.
- **Resolved the duplicate names.** `datascience_exceptions.SerializationError`
  became `ModelSerializationError` (it is about model persistence) and
  `pipeline_exceptions.FeatureEngineeringError` became
  `FeaturePreprocessingError` (it derives from `PreprocessingError` and is keyed
  on a feature).
- Every old name still resolves, to the same class object, with a
  `DeprecationWarning` naming its replacement and 1.0.0 as its removal.

## Shipped in 0.3.0

- **The top level exports every exception.** All 98 classes are importable
  straight from `dataexcept`, so you no longer have to know which domain module
  a class lives in. The domain modules still export the same objects, so both
  spellings work and refer to the same classes.

  This was safe to do only because 0.2.0 removed the two things that made a flat
  namespace dangerous: there are now no duplicate names and nothing shadows a
  builtin. Both are enforced by tests, as is the rule that every exception the
  package defines must be exported.

## Shipped in 1.0.0

- **The public API is frozen** under the
  [stability policy](https://diogoribeiro7.github.io/DataExcept/stability/):
  nothing public is renamed or removed outside a major release, and anything
  that will be removed is deprecated first.
- `dataexcept.job_exceptions`, deprecated since 0.1.0, is removed.
- The four aliases introduced in 0.2.0 are removed, along with the deprecation
  machinery that served them.
- A [migration guide](https://diogoribeiro7.github.io/DataExcept/migration/)
  covering every rename between 0.1 and 1.0.

## Shipped in 1.1.0

- **`wrap` and `wrapping`** turn a third-party exception into a DataExcept one,
  passing the original to whichever constructor parameter takes a cause and
  setting `__cause__` either way — so a traceback shows both failures even for
  a class that records nothing.
- **Guidance on building a project-specific hierarchy** on these bases, in the
  advanced usage guide.

## Shipped in 1.2.0

- **Structured exception envelopes** — `exception_to_dict` and
  `exception_to_json` preserve exception identity, public attributes and
  bounded cause/context chains for APIs, queues, telemetry and structured logs.
- **Strict JSON-safe export** — non-finite floats, byte payloads and hostile or
  unserialisable caller state degrade safely instead of breaking error
  transport.
- **Stricter export redaction** — credential-bearing URL paths are removed as
  well as sensitive query and fragment values, including inside third-party
  causes and caller-supplied attributes.

## Shipped in 1.3.0 — Structured concurrent failures

- Preserve Python 3.11+ `ExceptionGroup` and `BaseExceptionGroup` trees under an
  `exceptions` field instead of flattening concurrent failures into one
  rendered message.
- Apply the same redaction, public-attribute, cycle and depth-limit guarantees
  to group members as to ordinary causes and contexts.
- Treat hostile or malformed exception-group member metadata as an export
  boundary failure: fall back to the ordinary exception record instead of
  raising from the serializer.
- Keep Python 3.10 support with no `exceptiongroup` backport or added runtime
  dependency.
- Keep the advanced usage guide aligned with the exact envelope shape and
  fallback semantics.

## Shipped in 1.4.0 — Cause and failure metadata

- **Canonical wrapped-exception causes** — `cause=` and `.cause` are the public
  contract for migrated operational exceptions, while legacy `original` and
  `original_exception` aliases remain compatible where already public.
- **Machine-readable recovery metadata** — every `DataExceptError` exposes
  `failure_kind`, `retryable`, `retry_after_seconds` and `failure_metadata`.
  Defaults stay conservative: validation and unchanged auth failures are
  permanent/non-retryable, while generic infrastructure failures remain
  unknown unless an integration has backend-specific evidence.
- **Backend-informed wrapping** — `wrap()` and `wrapping()` accept
  `failure_metadata=` without changing target exception constructor APIs.
- **Structured failure envelopes** — DataExcept records include a stable
  `failure` object, with hostile or malformed custom metadata falling back to
  the canonical unknown record rather than breaking serialization.
- **Simplified release architecture** — release preparation uses normal
  branches and pull requests; one permanent privileged Release workflow builds,
  verifies and publishes only a reviewed commit on protected `main`.

## Shipped in 1.5.0 — Envelope contract and safer parsing context

- **A versioned JSON Schema** covering the stable envelope fields — `type`,
  `module`, `message`, `attributes`, `failure`, `cause`, `context`,
  `exceptions`, `cycle` and `truncated`. It ships inside the package, reachable
  as `envelope_schema()`, and is published at its own `$id` so a consumer in
  another language needs nothing from PyPI.
- **Reference fixtures** for ordinary exceptions, explicit causes, failure
  metadata, implicit contexts, nested exception groups, redaction, truncation
  and cycles. Every one is produced by running the serializer over a real
  exception, so a published payload cannot describe an envelope the library
  does not emit.
- **Compatibility tests** that validate an emitted envelope against the schema
  for every exception class the package defines, and that reject malformed
  envelopes — a schema that accepts anything documents nothing.
- **No new runtime dependency and no change to the envelope itself.** The
  schema is versioned separately from the package, under the 1.x rule that
  fields may be added but an established field does not change meaning
  silently.
- **Redaction-safe parsing context** — `ParsingError` and
  `DeserializationError` can describe a failure with `source`, `format`, a
  bounded `preview` and `cause` instead of retaining the payload that caused
  it. Both payload arguments still work and still keep what they are given;
  they are simply no longer the only way to report the failure.
- **A bounded generated message** for a parsing failure, so a malformed
  megabyte no longer becomes a log line of the same size.

## Shipped in 1.6.0 — Pino interoperability and message brokers

Two additions, neither of which brings a dependency: DataExcept envelopes are
consumable from Node.js services using Pino, and broker failures have a
hierarchy of their own.

- **A projection with one rename in it** — `exceptions` becomes `errors`, which
  is what JavaScript's `AggregateError` calls the same thing. Identity, public
  attributes, failure metadata and the whole cause, context and member tree
  come through unchanged, as does the redaction already applied to them.
- **A versioned profile schema**, published beside the envelope schema and
  versioned apart from it, so either can gain a field without the other moving.
- **A stack only when there is one** — `include_stack=True` renders the
  exception's real traceback, redacted like any other exported string, and
  omits the field rather than inventing one for an exception that was never
  raised.
- **Attributes kept nested** rather than spread onto the error, so an attribute
  called `type` or `stack` cannot overwrite the fields a Pino consumer reads.
- **Fixture pairs** — every published envelope fixture has its projection
  beside it, neither written by hand, so an implementation in another language
  checks itself against files rather than against prose.
- **Documented JavaScript and TypeScript usage**, with the projection restated
  in JavaScript and a contract test over those pairs.
- **No Node.js dependency, in either direction**, and no npm package: an
  adapter belongs in a separate artifact with its own release cycle, and the
  profile is what makes one writable.
- **A message-broker hierarchy** — `MessageBrokerError` and the five failures
  beneath it name the operation that failed, and carry the topic, partition,
  offset and consumer group that say where. It fits Kafka, RabbitMQ, Pulsar and
  NATS because it describes the operation rather than the product, and the
  package still depends on no broker client.

## Ongoing

- Track new stable Python releases promptly; 3.14 is supported as of 0.4.1.
- Keep observability integrations optional and dependency-free. Sentry event
  enrichment is available without importing `sentry-sdk`; OpenTelemetry
  exception attributes follow the same boundary.
- Prioritise new exception domains by what users actually report reaching for
  generic exceptions to express. The message-broker family in 1.6.0 arrived
  that way, and is the shape a new domain should take: named by the operation
  that failed rather than by the product it failed in.

## Planned — observability integrations

MCP is one example of a broader problem. Any system where work crosses an
execution boundary needs failures to remain identifiable and correlated after
they leave the frame that raised them. DataExcept should provide one common
observability model and thin adapters for those environments, rather than a
separate logging design for each product or protocol.

The common contract is the existing redacted exception envelope plus failure
metadata. Logs, traces and error trackers should project that contract into the
shape their ecosystem expects without introducing mandatory runtime
integrations.

- **Common operation context** — define a small, product-neutral context for
  `system`, `component`, `operation`, `request_id`, `job_id` and similar
  identifiers. Adapters can map their own terminology onto it without changing
  the exception hierarchy.
- **Structured logging** — make the envelope easy to attach to Python logging,
  JSON loggers and external structured-log formats while preserving the rule
  that observability must never replace the original failure with a logging
  failure.
- **OpenTelemetry as the shared trace vocabulary** — reuse standard
  `exception.*` attributes and `dataexcept.failure.*` recovery metadata across
  services instead of inventing product-specific telemetry fields.
- **Trace and correlation continuity** — accept and propagate trace, request,
  job and correlation identifiers when a framework exposes them, but do not
  generate fake provenance when it does not.
- **Low-cardinality indexing** — keep operation type, failure kind and
  retryability filterable while keeping payloads, arguments, URLs and other
  high-cardinality or sensitive values inside the bounded redacted envelope.
- **No framework lock-in** — use plain mappings and structural interfaces so an
  adapter can work with a framework or protocol without making its SDK a
  DataExcept runtime dependency.
- **Contract tests for every adapter** — verify redaction, strict JSON safety,
  traceback preservation, correlation metadata and the never-throw
  observability boundary.

### Candidate environments

Prioritise integrations where an exception routinely crosses a process,
network, queue or orchestration boundary:

- **Web APIs and RPC services** — request IDs, endpoints/methods, status and
  trace correlation for HTTP, ASGI/WSGI-style services and RPC frameworks.
- **Background workers and task queues** — task/job IDs, retries, attempt
  numbers and worker context for asynchronous execution.
- **Workflow and data orchestrators** — run, workflow, DAG, step and task
  identifiers for scheduled or distributed pipelines.
- **Serverless runtimes** — invocation/request IDs, cold-start/runtime context
  and stderr-safe diagnostics without coupling to one cloud provider.
- **Message brokers and stream processors** — correlate broker exceptions with
  consumer, partition, offset and trace context across producer/consumer
  boundaries.
- **Distributed data and ML workloads** — preserve experiment, model, batch,
  stage and worker context when failures cross executors or remote workers.
- **Long-running services and daemons** — structured lifecycle and background
  task failures where stdout/stderr or process supervisors impose logging
  constraints.
- **Agent and tool protocols** — attach tool/resource/prompt or other operation
  context and preserve distributed trace continuity. MCP is the first concrete
  example here, not a special observability model of its own.

### MCP example

For current MCP implementations, follow the protocol architecture rather than
building new code around its deprecated Logging capability. Stdio diagnostics
belong on `stderr`, structured observability belongs in OpenTelemetry, and W3C
trace context carried through `_meta` should remain correlated across the host,
MCP server, tool call and downstream services.

- Attach MCP method and operation names such as a tool, resource or prompt name
  to the generic operation context.
- Never write diagnostics to stdout on stdio transports, because stdout belongs
  to the protocol stream.
- Preserve `traceparent`, `tracestate` and `baggage` when they are present.
- Keep arguments out of tags by default; the bounded redacted envelope is the
  place for structured failure context.
- Keep any legacy MCP logging-notification support as an explicit compatibility
  adapter during the deprecation window, not as the primary observability path.

## Known follow-ups

One repository-setting follow-up remains:

- The `wheel` job mirrors the release gate on every pull request but is not in
  the branch-protection required set, so it reports without blocking.
