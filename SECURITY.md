# Security Policy

## Supported versions

DataExcept is pre-1.0. Security fixes are applied to the latest released
version only.

| Version | Supported |
| --- | --- |
| 0.4.x | ✅ |
| < 0.4 | ❌ |

## Reporting a vulnerability

**Please do not report security issues through public GitHub issues.**

Use GitHub's private vulnerability reporting instead:

1. Go to the [Security tab](https://github.com/DiogoRibeiro7/DataExcept/security).
2. Choose **Report a vulnerability**.

That opens a private advisory visible only to you and the maintainers. If you
cannot use it, email <diogo.debastos.ribeiro@gmail.com> instead.

Please include enough detail to reproduce the issue: the affected version, a
minimal example, and what an attacker could achieve.

## What to expect

- An acknowledgement within **5 working days**.
- An assessment, and a fix or an explanation of why it is not a vulnerability,
  within **30 days**.
- Credit in the advisory and the changelog, unless you would rather stay
  anonymous.

This is a volunteer-maintained project, so please treat those as good-faith
targets rather than a contractual SLA.

## Scope

DataExcept is a library of exception classes and logging helpers. It performs
no network or filesystem I/O and has one conditional runtime dependency
(`tomli`, on Python < 3.11).

The realistic issue is **information disclosure through exception messages**.
These exceptions embed the values that caused a failure, and
`log_exception` logs `str(exc)`, so a message can reach a log.

### What is redacted

Values the library is *given* as credentials never appear in a message or on
the exception:

| Class | Redacted |
| --- | --- |
| `InvalidTokenError` | the token, replaced by a non-reversible fingerprint |
| `DatabaseConnectionError` | any username and password in the URL |
| `WebhookError` | userinfo, sensitive parameters **and the path** |
| `ApiError` | userinfo and sensitive parameters in the endpoint |

`WebhookError` drops the path because that *is* the credential for Slack,
Discord and others, which document the whole webhook URL as a secret.

Beyond those classes, **any URL is redacted wherever it appears**:

- in a `message` you supplied yourself;
- in the text of a wrapped exception that quotes the original URL;
- in fields such as `DataLoadingError.source` that may hold a path *or* a URL —
  ordinary file paths are left untouched.

A URL keeps its scheme, host, port and non-sensitive parameters, because those
are what make the error actionable. It loses userinfo, any query or fragment
parameter whose name contains `token`, `secret`, `key`, `password`, `auth`,
`credential`, `sig` or `session` — so `X-Amz-Signature`, `auth_token` and an
OAuth `#access_token=` fragment are all covered.

A redacted secret renders as `***(1a2b3c4d)`, a truncated SHA-256, so the
*same* bad credential failing repeatedly stays recognisable in a log without
the credential being in it.

### The wrapped exception is not ours to rewrite

DataExcept redacts what *it* renders. A wrapped third-party exception renders
itself: an HTTP client's error may quote the credential-bearing URL it was
called with, and that string belongs to that library.

`log_exception` handles this — when the exception chain contains a URL it
formats the traceback and scrubs it, rather than handing logging an `exc_info`
that would print the chain verbatim. Ordinary exceptions keep the structured
`exc_info` path, so nothing changes for them.

**Outside `log_exception`, the raw object is still reachable.** These all
render the wrapped exception's own text:

```python
traceback.print_exc()          # your own traceback formatting
repr(exc.__dict__)             # the wrapped exception is stored as an attribute
str(exc.original_exception)    # reading it directly
logger.error("failed", exc_info=True)
```

If a third-party exception in your stack carries a credential, route it through
`log_exception` or scrub it yourself with
`dataexcept.redaction.redact_urls_in_text`.

### What is not redacted

**A bare, non-URL secret written into free-form text.** If you pass
`message="the key is AKIAIOSFODNN7"`, the library has no way to know that
string is a credential and it will be logged. The one exception is a value the
library was explicitly handed as a secret — `InvalidTokenError`'s token is
removed from your message too, provided it is at least 8 characters, below
which substring replacement would corrupt ordinary words.

Everything else is echoed deliberately — a field name, a column, a model name,
a file path — because that is the point of the library.

**`QueryExecutionError` embeds the SQL you give it**, including any literal
values in it. It is not redacted, because a normalised query is often useless
for debugging. If your queries carry personal data in literals, pass a
parameterised or normalised statement rather than the interpolated one.

Treat all of this as data you control: if you log exceptions where untrusted
parties can read them, or return exception text in an API response, review what
those messages carry. A report showing DataExcept disclosing something a caller
could not reasonably expect — particularly a credential — is in scope.
