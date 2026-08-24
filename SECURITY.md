# Security Policy

## Supported versions

DataExcept is pre-1.0. Security fixes are applied to the latest released
version only.

| Version | Supported |
| --- | --- |
| 0.1.x | ✅ |
| < 0.1 | ❌ |

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

The most likely realistic issue is **information disclosure through exception
messages**: these exceptions embed the values that caused a failure, so a
message may contain data from your inputs. If you log exceptions where
untrusted parties can read them, or return exception text in an API response,
review what those messages carry first. That behaviour is intentional and
documented, not a vulnerability in itself — but a report showing DataExcept
leaking something a caller could not reasonably expect is in scope.
