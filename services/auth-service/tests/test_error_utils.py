import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException, status

from app.core.error_utils import (
    create_generic_error,
    GenericErrors,
    add_timing_jitter,
)


class TestCreateGenericError:
    def test_create_generic_error_basic(self):
        error = create_generic_error(
            error_code="TEST_ERROR",
            message="Test error message"
        )
        
        assert isinstance(error, HTTPException)
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.detail["code"] == "TEST_ERROR"
        assert error.detail["message"] == "Test error message"
        assert "details" not in error.detail

    def test_create_generic_error_with_custom_status(self):
        error = create_generic_error(
            error_code="NOT_FOUND",
            message="Resource not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
        
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.detail["code"] == "NOT_FOUND"

    def test_create_generic_error_with_log_details(self):
        with patch("app.core.error_utils.logger") as mock_logger:
            error = create_generic_error(
                error_code="LOGGED_ERROR",
                message="Error with logging",
                log_details={"email": "test@example.com", "reason": "test"}
            )
            
            mock_logger.warning.assert_called_once()
            assert error.detail["code"] == "LOGGED_ERROR"

    def test_create_generic_error_without_log_details(self):
        with patch("app.core.error_utils.logger") as mock_logger:
            error = create_generic_error(
                error_code="NO_LOG_ERROR",
                message="Error without logging"
            )
            
            mock_logger.warning.assert_not_called()
            assert error.detail["code"] == "NO_LOG_ERROR"


class TestGenericErrors:
    def test_registration_failed(self):
        error = GenericErrors.registration_failed(
            email="test@example.com",
            username="testuser",
            ip="192.168.1.1",
            reason="duplicate_email"
        )
        
        assert isinstance(error, HTTPException)
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.detail["code"] == "REGISTRATION_FAILED"
        assert error.detail["message"] == "Unable to complete registration. Please try with different credentials."
        assert "details" not in error.detail

    def test_registration_failed_with_duplicate_username(self):
        with patch("app.core.error_utils.logger") as mock_logger:
            error = GenericErrors.registration_failed(
                email="test@example.com",
                username="existinguser",
                ip="10.0.0.1",
                reason="duplicate_username"
            )
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "duplicate_username" in str(call_args)

    def test_registration_failed_with_none_ip(self):
        error = GenericErrors.registration_failed(
            email="test@example.com",
            username="testuser",
            ip=None,
            reason="duplicate_email"
        )
        
        assert error.detail["code"] == "REGISTRATION_FAILED"

    def test_verification_failed(self):
        error = GenericErrors.verification_failed(
            email="test@example.com",
            ip="192.168.1.1",
            attempts=1
        )
        
        assert isinstance(error, HTTPException)
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.detail["code"] == "INVALID_CODE"
        assert error.detail["message"] == "Invalid verification code"
        assert "details" not in error.detail

    def test_verification_failed_with_logging(self):
        with patch("app.core.error_utils.logger") as mock_logger:
            error = GenericErrors.verification_failed(
                email="test@example.com",
                ip="192.168.1.1",
                attempts=2
            )
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "remaining_attempts" in str(call_args)

    def test_verification_code_expired(self):
        error = GenericErrors.verification_code_expired()
        
        assert isinstance(error, HTTPException)
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.detail["code"] == "VERIFICATION_CODE_EXPIRED"
        assert error.detail["message"] == "Too many attempts. Please request a new verification code."


class TestAddTimingJitter:
    @pytest.mark.asyncio
    async def test_add_timing_jitter_adds_delay(self):
        start_time = time.time()
        await add_timing_jitter(min_ms=50, max_ms=100)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms >= 45
        assert elapsed_ms <= 150

    @pytest.mark.asyncio
    async def test_add_timing_jitter_custom_range(self):
        start_time = time.time()
        await add_timing_jitter(min_ms=10, max_ms=30)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms >= 5
        assert elapsed_ms <= 50

    @pytest.mark.asyncio
    async def test_add_timing_jitter_multiple_calls_vary(self):
        delays = []
        for _ in range(5):
            start_time = time.time()
            await add_timing_jitter(min_ms=10, max_ms=50)
            elapsed_ms = (time.time() - start_time) * 1000
            delays.append(elapsed_ms)
        
        assert len(set(delays)) > 1
