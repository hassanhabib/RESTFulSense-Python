# RESTFulSense for Python

One exception per HTTP status, with the response's problem details carried as data. The Python port
of [RESTFulSense](https://github.com/hassanhabib/RESTFulSense), the library
[The Standard](https://github.com/hassanhabib/The-Standard) uses so a foundation service can
localize an external failure by its type.

The C# library decides the behaviour; this package decides how it reads in Python. It uses only the
standard library (`urllib`), plus [xeption](https://github.com/hassanhabib/Xeption-Python), which
every exception here derives from, as RESTFulSense depends on Xeption in C#.

```bash
python -m pip install restfulsense
```

## Posting content

```python
from restfulsense import RESTFulApiFactoryClient

client = RESTFulApiFactoryClient(
    base_url="https://api.example.com/v1/",
    headers={"Authorization": "Bearer ..."},
    timeout_seconds=30)

result = await client.post_content("students", {"name": "Ada"})
```

The relative address joins the base address by RFC 3986, as .NET's `HttpClient` does: a base
address without a trailing slash drops its last segment. The content goes as compact JSON with
`Content-Type: application/json; charset=utf-8`; the response is returned as parsed JSON, or `{}`
for an empty body. The request runs on a worker thread, so the event loop is never blocked.

The opener is the transport, as the `HttpClient` is in C#. A caller that owns its handler (a
proxy, a recorder, a test double) hands over an opener built on it, and every request goes through
it:

```python
import urllib.request

client = RESTFulApiFactoryClient(
    base_url="https://api.example.com/v1/",
    opener=urllib.request.build_opener(my_handler))
```

Without one, the client builds a bare opener that sends no `User-Agent`, as `HttpClient` sends none
of its own.

## Failing responses

A failing status raises the exception for that status, carrying `status_code` and `content`:

```python
from restfulsense import (
    HttpRequestException,
    HttpResponseBadRequestException,
    HttpResponseUrlNotFoundException)

try:
    await client.post_content("students", student)
except HttpResponseBadRequestException as bad_request_exception:
    print(bad_request_exception.message, bad_request_exception.data)
except HttpResponseUrlNotFoundException:
    ...
except HttpRequestException:
    ...
```

- When the body is problem details (it names both a `"type":` and a `"title":`), the message is
  the title and `data` holds the `errors`, so a foundation can copy them onto its own exception.
  Otherwise the message is the body.
- A 404 whose response declares no `Content-Type` is `HttpResponseUrlNotFoundException`: an address
  nothing answers at. A 404 with one is `HttpResponseNotFoundException`.
- A status with no exception type of its own (any 2xx or 3xx, and 4xx or 5xx codes such as 418)
  is not a failure.
- No answer at all (refused, unresolved, reset, timed out) raises `HttpRequestException`. As in
  .NET it is not a Xeption.

`validate_http_response` and `read_as_string` in `restfulsense.validation_service` are the same
rules on their own, for a caller that does its own I/O.

## Exception types

`HttpResponseException` is the base of all of them. One per status: 400 `BadRequest`,
401 `Unauthorized`, 402 `PaymentRequired`, 403 `Forbidden`, 404 `NotFound` and `UrlNotFound`,
405 `MethodNotAllowed`, 406 `NotAcceptable`, 407 `ProxyAuthenticationRequired`,
408 `RequestTimeout`, 409 `Conflict`, 410 `Gone`, 411 `LengthRequired`, 412 `PreconditionFailed`,
413 `RequestEntityTooLarge`, 414 `RequestUriTooLong`, 415 `UnsupportedMediaType`,
416 `RequestedRangeNotSatisfiable`, 417 `ExpectationFailed`, 421 `MisdirectedRequest`,
422 `UnprocessableEntity`, 423 `Locked`, 424 `FailedDependency`, 426 `UpgradeRequired`,
428 `PreconditionRequired`, 429 `TooManyRequests`, 431 `RequestHeaderFieldsTooLarge`,
451 `UnavailableForLegalReasons`, 500 `InternalServerError`, 501 `NotImplemented`,
502 `BadGateway`, 503 `ServiceUnavailable`, 504 `GatewayTimeout`, 505 `HttpVersionNotSupported`,
506 `VariantAlsoNegotiates`, 507 `InsufficientStorage`, 508 `LoopDetected`, 510 `NotExtended`,
511 `NetworkAuthenticationRequired`. Each is named `HttpResponse<Name>Exception`, as in C#.

### Not ported yet

This version ports RESTFulSense 3.2.0's `ValidationService` and the `PostContentAsync` routine of
`RESTFulApiFactoryClient`. The rest of the C# library has no Python counterpart yet: the GET, PUT
and DELETE routines, custom serialization, streams and forms, cancellation, `RESTFulApiClient`,
and the ASP.NET controller and attribute types.

## Contributing

See [CONTRIBUTING.md](https://github.com/hassanhabib/RESTFulSense-Python/blob/main/CONTRIBUTING.md).

## License

[The Standard Software License (TSSL) v1.1](https://github.com/hassanhabib/RESTFulSense-Python/blob/main/LICENSE.txt).
