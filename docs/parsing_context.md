# Parsing Context

Parsing fails on content you did not write. An API returns HTML where JSON was
promised, a queue delivers a truncated frame, a partner drops a file with the
wrong encoding. The obvious way to report that is to keep the offending payload
on the exception — and that payload is exactly the thing you cannot safely keep.

It may carry a token the service returned in an error body, personal data from
the record that failed, several megabytes of nothing useful, or arbitrary
binary. Whatever it carries goes wherever the exception goes: the message, the
log line, the structured envelope, the telemetry event.

`ParsingError` and `DeserializationError` therefore let you describe the failure
without holding the payload at all.

```python
from dataexcept import ParsingError

try:
    return response.json()
except ValueError as exc:
    raise ParsingError(
        source=response.url,      # redacted when it is a URL
        format="json",
        preview=response.text,    # bounded excerpt, not the whole body
        cause=exc,
    ) from exc
```

Field     | Purpose
--------- | -----------------------------------------------------------------------------------------
`source`  | Where the content came from — an endpoint, a path, a topic. Redacted when it is a URL, left alone when it is a file path.
`format`  | What the content was meant to be: `"json"`, `"avro"`, `"csv"`.
`preview` | A bounded excerpt, for when seeing the content is the point.
`cause`   | The underlying exception. Recorded as `.cause` and set as `__cause__`, so the traceback shows both failures.

## What `preview` guarantees

- **At most 200 characters** (`dataexcept._previews.MAX_PREVIEW_LENGTH`),
  counting the `...` that is appended when — and only when — something was cut.
  Pass less if you want less; there is deliberately no way to ask for more.
  The bound is on the payload: redaction runs over the excerpt afterwards, as
  over every attribute, so replacing a short credential can add a couple of
  characters.
- **Bytes are decoded** as UTF-8, with any undecodable byte rendered as `\xNN`.
  A malformed payload is the case this field exists for, so the excerpt stays
  printable and never fails where the parser already did.
- **URLs are redacted**, in the excerpt as everywhere else. An error body
  quoting a callback URL with a token in it does not keep the token.

## Three shapes of the same failure

=== "HTTP / API"

    ```python
    from dataexcept import ParsingError

    try:
        payload = response.json()
    except ValueError as exc:
        raise ParsingError(
            source=response.url,
            format="json",
            preview=response.text,
            cause=exc,
        ) from exc
    ```

    Renders as
    `Failed to parse json (https://api.example.com/v1/orders?token=***): Expecting value: line 1 column 1 (char 0)`.

=== "File"

    ```python
    from dataexcept import ParsingError

    try:
        rows = list(csv.reader(handle))
    except csv.Error as exc:
        raise ParsingError(source=str(path), format="csv", cause=exc) from exc
    ```

    A path is not a URL, so it is kept whole: it is what makes the error
    actionable, and there is no credential in it to lose.

=== "Message broker"

    ```python
    from dataexcept import DeserializationError

    try:
        event = avro_decoder.decode(record.value())
    except DecodeError as exc:
        raise DeserializationError(
            source=f"{record.topic()}[{record.partition()}]@{record.offset()}",
            format="avro",
            preview=record.value(),
            cause=exc,
        ) from exc
    ```

    `source` is free text, so a topic, partition and offset describe the
    failure precisely without the frame itself being retained.

## Keeping the payload

The original arguments still work, still take the same positions, and still
keep exactly what they are given:

```python
from dataexcept import DeserializationError, ParsingError

ParsingError("[1, 2,")                     # .text is kept verbatim
DeserializationError(frame_bytes, "avro")  # .data is kept verbatim
```

Passing one is now a decision rather than the only option. Two things are worth
knowing before you make it:

- The generated message is **bounded**, so a large payload no longer becomes a
  large log line. The payload itself is still kept in full on `.text`.
- `.data` is **raw bytes**, and redaction works on text. DataExcept does not
  decode or rewrite binary to search it, so a secret inside bytes you pass to
  `data` stays in `data` — it simply never reaches the message. If the payload
  is untrusted, describe it with `source`, `format` and `preview` instead of
  keeping it.

As always, a bare non-URL secret sitting in free text cannot be recognised and
is not redacted; see [the security policy](https://github.com/DiogoRibeiro7/DataExcept/blob/main/SECURITY.md)
for exactly what redaction does and does not cover.
