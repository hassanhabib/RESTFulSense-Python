# ---------------------------------------------------------------
# Copyright (c) Hassan Habib All rights reserved.
# Licensed under the The Standard Software License (TSSL)
# ---------------------------------------------------------------

# Ported from RESTFulSense.Tests/Services/ValidationServiceTests.Raw.cs and
# ValidationServiceTests.ProblemDetails.cs: one C# test per status becomes one parameter here.

import json
import random
import uuid

import pytest

from restfulsense import (
    HttpResponseBadGatewayException,
    HttpResponseBadRequestException,
    HttpResponseConflictException,
    HttpResponseException,
    HttpResponseExpectationFailedException,
    HttpResponseFailedDependencyException,
    HttpResponseForbiddenException,
    HttpResponseGatewayTimeoutException,
    HttpResponseGoneException,
    HttpResponseHttpVersionNotSupportedException,
    HttpResponseInsufficientStorageException,
    HttpResponseInternalServerErrorException,
    HttpResponseLengthRequiredException,
    HttpResponseLockedException,
    HttpResponseLoopDetectedException,
    HttpResponseMethodNotAllowedException,
    HttpResponseMisdirectedRequestException,
    HttpResponseNetworkAuthenticationRequiredException,
    HttpResponseNotAcceptableException,
    HttpResponseNotExtendedException,
    HttpResponseNotFoundException,
    HttpResponseNotImplementedException,
    HttpResponsePaymentRequiredException,
    HttpResponsePreconditionFailedException,
    HttpResponsePreconditionRequiredException,
    HttpResponseProxyAuthenticationRequiredException,
    HttpResponseRequestedRangeNotSatisfiableException,
    HttpResponseRequestEntityTooLargeException,
    HttpResponseRequestHeaderFieldsTooLargeException,
    HttpResponseRequestTimeoutException,
    HttpResponseRequestUriTooLongException,
    HttpResponseServiceUnavailableException,
    HttpResponseTooManyRequestsException,
    HttpResponseUnauthorizedException,
    HttpResponseUnavailableForLegalReasonsException,
    HttpResponseUnprocessableEntityException,
    HttpResponseUnsupportedMediaTypeException,
    HttpResponseUpgradeRequiredException,
    HttpResponseUrlNotFoundException,
    HttpResponseVariantAlsoNegotiatesException)
from restfulsense.validation_service import (
    DEFAULT_PROBLEM_TITLE,
    read_as_string,
    validate_http_response)

# The C# tests give the 404 that means "not found" a Content-Type and leave every other response
# without one, as StreamContent does.
FAILING_RESPONSES = [
    (400, None, HttpResponseBadRequestException),
    (401, None, HttpResponseUnauthorizedException),
    (402, None, HttpResponsePaymentRequiredException),
    (403, None, HttpResponseForbiddenException),
    (404, "text/json", HttpResponseNotFoundException),
    (404, None, HttpResponseUrlNotFoundException),
    (405, None, HttpResponseMethodNotAllowedException),
    (406, None, HttpResponseNotAcceptableException),
    (407, None, HttpResponseProxyAuthenticationRequiredException),
    (408, None, HttpResponseRequestTimeoutException),
    (409, None, HttpResponseConflictException),
    (410, None, HttpResponseGoneException),
    (411, None, HttpResponseLengthRequiredException),
    (412, None, HttpResponsePreconditionFailedException),
    (413, None, HttpResponseRequestEntityTooLargeException),
    (414, None, HttpResponseRequestUriTooLongException),
    (415, None, HttpResponseUnsupportedMediaTypeException),
    (416, None, HttpResponseRequestedRangeNotSatisfiableException),
    (417, None, HttpResponseExpectationFailedException),
    (421, None, HttpResponseMisdirectedRequestException),
    (422, None, HttpResponseUnprocessableEntityException),
    (423, None, HttpResponseLockedException),
    (424, None, HttpResponseFailedDependencyException),
    (426, None, HttpResponseUpgradeRequiredException),
    (428, None, HttpResponsePreconditionRequiredException),
    (429, None, HttpResponseTooManyRequestsException),
    (431, None, HttpResponseRequestHeaderFieldsTooLargeException),
    (451, None, HttpResponseUnavailableForLegalReasonsException),
    (500, None, HttpResponseInternalServerErrorException),
    (501, None, HttpResponseNotImplementedException),
    (502, None, HttpResponseBadGatewayException),
    (503, None, HttpResponseServiceUnavailableException),
    (504, None, HttpResponseGatewayTimeoutException),
    (505, None, HttpResponseHttpVersionNotSupportedException),
    (506, None, HttpResponseVariantAlsoNegotiatesException),
    (507, None, HttpResponseInsufficientStorageException),
    (508, None, HttpResponseLoopDetectedException),
    (510, None, HttpResponseNotExtendedException),
    (511, None, HttpResponseNetworkAuthenticationRequiredException),
]


def create_random_string() -> str:
    return uuid.uuid4().hex


def create_random_errors() -> dict[str, list[str]]:
    return {
        create_random_string(): [
            create_random_string() for _ in range(random.randint(1, 9))
        ]
        for _ in range(random.randint(1, 9))
    }


def raise_validation(
    status_code: int,
    content_type: str | None,
    content: str) -> HttpResponseException:

    with pytest.raises(HttpResponseException) as exception_info:
        validate_http_response(status_code, content_type, content)

    return exception_info.value


class TestValidationService:
    @pytest.mark.parametrize("status_code, content_type, exception_type", FAILING_RESPONSES)
    def test_should_raise_status_exception_if_response_failed(
        self,
        status_code: int,
        content_type: str | None,
        exception_type: type[HttpResponseException]) -> None:

        # given
        content = create_random_string()

        expected_exception = {
            "type": exception_type,
            "message": content,
            "status_code": status_code,
            "content": content,
            "data": {},
        }

        # when
        actual_exception = raise_validation(status_code, content_type, content)

        # then
        assert {
            "type": type(actual_exception),
            "message": actual_exception.message,
            "status_code": actual_exception.status_code,
            "content": actual_exception.content,
            "data": actual_exception.data,
        } == expected_exception

    @pytest.mark.parametrize("status_code, content_type, exception_type", FAILING_RESPONSES)
    def test_should_raise_status_exception_with_problem_details_if_response_failed(
        self,
        status_code: int,
        content_type: str | None,
        exception_type: type[HttpResponseException]) -> None:

        # given
        random_title = create_random_string()
        random_errors = create_random_errors()

        content = json.dumps({
            "type": create_random_string(),
            "title": random_title,
            "errors": random_errors,
        })

        expected_exception = {
            "type": exception_type,
            "message": random_title,
            "content": content,
            "data": random_errors,
        }

        # when
        actual_exception = raise_validation(status_code, content_type, content)

        # then
        assert {
            "type": type(actual_exception),
            "message": actual_exception.message,
            "content": actual_exception.content,
            "data": actual_exception.data,
        } == expected_exception

    def test_should_use_default_title_if_problem_details_title_is_null(self) -> None:
        # given
        content = json.dumps({"type": create_random_string(), "title": None})

        # when
        actual_exception = raise_validation(400, None, content)

        # then
        assert actual_exception.message == DEFAULT_PROBLEM_TITLE

    @pytest.mark.parametrize("status_code", [200, 201, 204, 302, 418, 499])
    def test_should_not_raise_if_status_has_no_exception_type(self, status_code: int) -> None:
        # given
        content = create_random_string()

        # when
        actual_result = validate_http_response(status_code, None, content)

        # then
        assert actual_result is None


class TestReadAsString:
    def test_should_read_utf8_if_no_charset_is_given(self) -> None:
        # given
        content = "café " + create_random_string()

        # when
        actual_content = read_as_string(content.encode("utf-8"), "application/json")

        # then
        assert actual_content == content

    def test_should_read_with_the_charset_of_the_content_type(self) -> None:
        # given
        content = "café " + create_random_string()

        # when
        actual_content = read_as_string(
            content.encode("latin-1"),
            'text/plain; charset="iso-8859-1"')

        # then
        assert actual_content == content

    def test_should_let_a_byte_order_mark_decide_over_the_charset(self) -> None:
        # given
        content = "café " + create_random_string()
        body = b"\xff\xfe" + content.encode("utf-16-le")

        # when
        actual_content = read_as_string(body, "text/plain; charset=utf-8")

        # then
        assert actual_content == content

    def test_should_read_utf8_if_the_charset_is_unknown(self) -> None:
        # given
        content = "café " + create_random_string()

        # when
        actual_content = read_as_string(content.encode("utf-8"), "text/plain; charset=nonsense")

        # then
        assert actual_content == content
