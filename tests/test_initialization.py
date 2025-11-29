"""Tests for Mail initialization and configuration."""

from __future__ import annotations

import pytest

from fastapi_mailman import Mail
from fastapi_mailman.config import ConnectionConfig
from fastapi_mailman.globals import _get_global_mailman, set_mailman


class TestMailInitialization:
    """Tests for Mail class initialization."""

    def test_mail_creation(self) -> None:
        """Test basic Mail instance creation."""
        config = ConnectionConfig(
            MAIL_USERNAME="test@example.com",
            MAIL_PASSWORD="password",
            MAIL_SERVER="smtp.example.com",
        )
        mail = Mail(config)

        assert mail.server == "smtp.example.com"
        assert mail.username == "test@example.com"
        assert mail.password == "password"
        assert mail.backend == "smtp"

        # Cleanup
        set_mailman(None)

    def test_mail_sets_global(self) -> None:
        """Test that Mail sets itself as global mailman."""
        config = ConnectionConfig(
            MAIL_USERNAME="test@example.com",
            MAIL_PASSWORD="password",
            MAIL_SERVER="smtp.example.com",
        )
        mail = Mail(config)

        assert _get_global_mailman() is mail

        # Cleanup
        set_mailman(None)

    def test_mail_repr(self) -> None:
        """Test Mail string representation."""
        config = ConnectionConfig(
            MAIL_USERNAME="test@example.com",
            MAIL_PASSWORD="password",
            MAIL_SERVER="smtp.example.com",
            MAIL_PORT=465,
        )
        mail = Mail(config)

        assert "smtp.example.com" in repr(mail)
        assert "465" in repr(mail)

        # Cleanup
        set_mailman(None)


class TestConnectionConfig:
    """Tests for ConnectionConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ConnectionConfig(
            MAIL_USERNAME="test@example.com",
            MAIL_PASSWORD="password",
            MAIL_SERVER="smtp.example.com",
        )

        assert config.MAIL_PORT == 587
        assert config.MAIL_USE_TLS is False
        assert config.MAIL_USE_SSL is False
        assert config.MAIL_BACKEND == "smtp"
        assert config.MAIL_DEFAULT_CHARSET == "utf-8"

    def test_default_sender_from_username(self) -> None:
        """Test that default sender is set from username."""
        config = ConnectionConfig(
            MAIL_USERNAME="test@example.com",
            MAIL_PASSWORD="password",
            MAIL_SERVER="smtp.example.com",
        )

        assert config.MAIL_DEFAULT_SENDER == "test@example.com"

    def test_explicit_default_sender(self) -> None:
        """Test explicit default sender."""
        config = ConnectionConfig(
            MAIL_USERNAME="test@example.com",
            MAIL_PASSWORD="password",
            MAIL_SERVER="smtp.example.com",
            MAIL_DEFAULT_SENDER="sender@example.com",
        )

        assert config.MAIL_DEFAULT_SENDER == "sender@example.com"

    def test_tls_ssl_mutual_exclusion(self) -> None:
        """Test that TLS and SSL cannot both be enabled."""
        with pytest.raises(ValueError, match="mutually exclusive"):
            ConnectionConfig(
                MAIL_USERNAME="test@example.com",
                MAIL_PASSWORD="password",
                MAIL_SERVER="smtp.example.com",
                MAIL_USE_TLS=True,
                MAIL_USE_SSL=True,
            )

    def test_template_engine_without_folder(self) -> None:
        """Test template_engine raises without TEMPLATE_FOLDER."""
        config = ConnectionConfig(
            MAIL_USERNAME="test@example.com",
            MAIL_PASSWORD="password",
            MAIL_SERVER="smtp.example.com",
        )

        with pytest.raises(ValueError, match="TEMPLATE_FOLDER"):
            config.template_engine()
