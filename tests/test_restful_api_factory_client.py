# ---------------------------------------------------------------
# Copyright (c) Hassan Habib All rights reserved.
# Licensed under the The Standard Software License (TSSL)
# ---------------------------------------------------------------

# Ported from RESTFulSense.Tests.Acceptance/Tests/RestfulSenseApiFactoryTests.PostContent.cs. The
# C# tests stand WireMock up in front of the client; these stand up the standard library's
# http.server, so the client is driven over a real socket.

import asyncio
import json
import socket
import threading
import urllib.request
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from restfulsense import (
    HttpRequestException,
    HttpResponseBadRequestException,
    HttpResponseUrlNotFoundException,
    RESTFulApiFactoryClient)


@dataclass
class StubResponse:
    status_code: int = 200
    content_type: str | None = "application/json; charset=utf-8"
    body: bytes = b""


@dataclass
class RecordedRequest:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes


@dataclass
class StubServer:
    url: str
    response: StubResponse = field(default_factory=StubResponse)
    requests: list[RecordedRequest] = field(default_factory=list)


def create_random_string() -> str:
    return uuid.uuid4().hex


def create_random_content() -> dict:
    return {create_random_string(): create_random_string() for _ in range(3)}


@pytest.fixture
def stub_server() -> Iterator[StubServer]:
    server_state = StubServer(url="")

    class StubHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))

            server_state.requests.append(RecordedRequest(
                method=self.command,
                path=self.path,
                headers=dict(self.headers.items()),
                body=body))

            response = server_state.response
            self.send_response(response.status_code)

            if response.content_type is not None:
                self.send_header("Content-Type", response.content_type)

            self.send_header("Content-Length", str(len(response.body)))
            self.end_headers()
            self.wfile.write(response.body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), StubHandler)
    server_state.url = f"http://127.0.0.1:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield server_state

    server.shutdown()
    server.server_close()
    thread.join()


class StampingHandler(urllib.request.BaseHandler):
    """A caller's own handler: it stamps every request it sees, so the server can tell."""

    def __init__(self, stamp: str) -> None:
        self.stamp = stamp

    def http_request(self, request: urllib.request.Request) -> urllib.request.Request:
        request.add_unredirected_header("X-Stamp", self.stamp)

        return request


def find_closed_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))

        return probe.getsockname()[1]


class TestRESTFulApiFactoryClient:
    def test_should_post_content(self, stub_server: StubServer) -> None:
        # given
        random_header_value = create_random_string()
        input_content = create_random_content()
        expected_result = create_random_content()
        stub_server.response.body = json.dumps(expected_result).encode("utf-8")

        client = RESTFulApiFactoryClient(
            base_url=f"{stub_server.url}/api/",
            headers={"X-Random": random_header_value})

        # when
        actual_result = asyncio.run(client.post_content("tests", input_content))

        # then
        actual_request = stub_server.requests[0]
        assert actual_result == expected_result
        assert len(stub_server.requests) == 1
        assert actual_request.method == "POST"
        assert actual_request.path == "/api/tests"
        assert actual_request.headers["Content-Type"] == "application/json; charset=utf-8"
        assert actual_request.headers["X-Random"] == random_header_value
        assert "User-Agent" not in actual_request.headers
        assert json.loads(actual_request.body) == input_content

    def test_should_post_content_through_the_supplied_opener(
        self,
        stub_server: StubServer) -> None:

        # given
        random_stamp = create_random_string()
        input_opener = urllib.request.build_opener(StampingHandler(random_stamp))
        stub_server.response.body = b"{}"

        client = RESTFulApiFactoryClient(base_url=stub_server.url, opener=input_opener)

        # when
        asyncio.run(client.post_content("/tests", create_random_content()))

        # then
        assert stub_server.requests[0].headers["X-Stamp"] == random_stamp

    def test_should_drop_the_last_segment_of_a_base_url_without_a_trailing_slash(
        self,
        stub_server: StubServer) -> None:

        # given
        stub_server.response.body = b"{}"
        client = RESTFulApiFactoryClient(base_url=f"{stub_server.url}/api/v1")

        # when
        asyncio.run(client.post_content("tests", create_random_content()))

        # then
        assert stub_server.requests[0].path == "/api/tests"

    def test_should_return_empty_content_if_response_has_no_body(
        self,
        stub_server: StubServer) -> None:

        # given
        stub_server.response = StubResponse(status_code=204, content_type=None)
        client = RESTFulApiFactoryClient(base_url=stub_server.url)

        # when
        actual_result = asyncio.run(client.post_content("/tests", create_random_content()))

        # then
        assert actual_result == {}

    def test_should_raise_status_exception_with_problem_details_if_response_failed(
        self,
        stub_server: StubServer) -> None:

        # given
        random_title = create_random_string()
        random_errors = {create_random_string(): [create_random_string()]}

        stub_server.response = StubResponse(
            status_code=400,
            content_type="application/problem+json",
            body=json.dumps({
                "type": create_random_string(),
                "title": random_title,
                "errors": random_errors,
            }).encode("utf-8"))

        client = RESTFulApiFactoryClient(base_url=stub_server.url)

        # when
        with pytest.raises(HttpResponseBadRequestException) as exception_info:
            asyncio.run(client.post_content("/tests", create_random_content()))

        # then
        actual_exception = exception_info.value
        assert (actual_exception.message, actual_exception.data) == (random_title, random_errors)

    def test_should_raise_url_not_found_exception_if_404_has_no_content_type(
        self,
        stub_server: StubServer) -> None:

        # given
        random_body = create_random_string()

        stub_server.response = StubResponse(
            status_code=404,
            content_type=None,
            body=random_body.encode("utf-8"))

        client = RESTFulApiFactoryClient(base_url=stub_server.url)

        # when
        with pytest.raises(HttpResponseUrlNotFoundException) as exception_info:
            asyncio.run(client.post_content("/tests", create_random_content()))

        # then
        assert exception_info.value.content == random_body

    def test_should_raise_http_request_exception_if_no_answer_arrives(self) -> None:
        # given
        client = RESTFulApiFactoryClient(base_url=f"http://127.0.0.1:{find_closed_port()}")

        # when
        with pytest.raises(HttpRequestException) as exception_info:
            asyncio.run(client.post_content("/tests", create_random_content()))

        # then
        assert exception_info.value.__cause__ is not None

    @pytest.mark.parametrize("base_url, timeout_seconds", [
        ("tests/relative", 100.0),
        ("http://127.0.0.1", 0.0),
        ("http://127.0.0.1", -1.0),
    ])
    def test_should_raise_value_error_if_base_url_or_timeout_is_invalid(
        self,
        base_url: str,
        timeout_seconds: float) -> None:

        # when
        with pytest.raises(ValueError):
            RESTFulApiFactoryClient(base_url=base_url, timeout_seconds=timeout_seconds)
