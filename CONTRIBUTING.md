# Contributing

This library is built to [The Standard](https://github.com/hassanhabib/The-Standard). It is the
Python port of the C# [RESTFulSense](https://github.com/hassanhabib/RESTFulSense) library: the C# library
decides the behaviour, and Python conventions decide how the code reads.

## The shape of a change

- **One change per branch.** Name it `users/<github-username>/<CATEGORY>-<entity>-<action>`.
- **Categories** are The Standard's: `INFRA`, `DOCUMENTATION`, `CODE RUB`, `MINOR FIX`, and their
  `MAJOR` / `MEDIUM` / `MINOR` forms.
- **Pull request titles** are `CATEGORY: Description In Pascal Case`, for example
  `MINOR FIX: Read The Charset Of A Problem Details Body`.

## Test-first, in pairs

Every behaviour lands as two commits:

1. `test_should_... -> FAIL`: the new test and a stub that raises `NotImplementedError`. The test
   **must run and fail**; a collection error or an import error is not a failure.
2. `test_should_... -> PASS`: only the implementation that makes it pass, with **the whole suite**
   green.

A behaviour ported from the C# library cites the C# test it mirrors in its pull request.

## Tests

Until `xeption` is on PyPI, install it from its repository first:

```bash
python -m pip install "xeption @ git+https://github.com/hassanhabib/Xeption-Python@main"
python -m pip install -e ".[test]"
python -m pytest -q
```

The client tests stand up a local `http.server` and drive the client over a real socket, as the C#
acceptance tests do with WireMock. Nothing leaves the machine.

Tests follow Given / When / Then, use random values for anything the behaviour does not depend on,
and compare the whole result rather than one field at a time.

## Versioning

Releases follow The Standard's four-part version, `v<model>.<service>.<fix>.<build>`: a model change
increments the first segment, a service or routine change the second, a fix or configuration change
the third, an automated build the fourth, and a higher-order change resets every segment below it.

## Releasing

Publishing uses PyPI Trusted Publishing from `.github/workflows/publish.yml`; there is no token.
Running the workflow by hand uploads to TestPyPI. Publishing a GitHub release uploads to PyPI.
