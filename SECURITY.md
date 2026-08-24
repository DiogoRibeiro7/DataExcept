# Security Policy

## Supported versions

DataExcept is pre-1.0. Security fixes are applied to the latest released
version only.

| Version | Supported |
| --- | --- |
| 0.3.x | ✅ |
| < 0.3 | ❌ |

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

Values that are inherently credentials never appear in a message or on the
exception, whatever you pass in:

| Class | Redacted |
| --- | --- |
| `InvalidTokenError` | the token, replaced by a non-reversible fingerprint |
| `DatabaseConnectionError` | any username and password in the URL |
| `WebhookError` | userinfo and sensitive query parameters in the URL |
| `ApiError` | userinfo and sensitive query parameters in the endpoint |

A redacted secret is rendered as `***(1a2b3c4d)`. The fingerprint is a
truncated SHA-256, so the *same* bad credential failing repeatedly stays
recognisable in a log without the credential being in it. Host, port and path
are preserved, because those are what make the error actionable.

### What is not redacted

Everything else is echoed deliberately — a field name, a column, a file path, a
model name — because that is the point of the library.

**`QueryExecutionError` embeds the SQL you give it**, including any literal
values in it. It is not redacted, because a normalised query is often useless
for debugging. If your queries carry personal data in literals, pass a
parameterised or normalised statement rather than the interpolated one.

Treat all of this as data you control: if you log exceptions where untrusted
parties can read them, or return exception text in an API response, review what
those messages carry. A report showing DataExcept disclosing something a caller
could not reasonably expect — particularly a credential — is in scope.
