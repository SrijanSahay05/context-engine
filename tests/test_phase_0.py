import os
import unittest
from unittest.mock import Mock, patch

from pydantic import ValidationError

from core.config import Settings
from db.session import DatabaseSessionManager


class SettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_password_is_required_and_not_empty(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(_env_file=None)
        with self.assertRaises(ValidationError):
            Settings(_env_file=None, postgres_password="")

    def test_password_reaches_engine_unchanged(self) -> None:
        password = "p@ss:/?#% word"
        settings = Settings(_env_file=None, postgres_password=password)
        manager = DatabaseSessionManager(settings.database_url)
        self.addCleanup(manager.dispose)
        self.assertEqual(manager.engine.url.password, password)
        self.assertNotIn(password, repr(settings))

    def test_port_boundaries(self) -> None:
        for port in (0, -1, 65536):
            with self.subTest(port=port), self.assertRaises(ValidationError):
                Settings(_env_file=None, postgres_password="test", postgres_port=port)
        for port in (1, 65535):
            with self.subTest(port=port):
                settings = Settings(
                    _env_file=None, postgres_password="test", postgres_port=port
                )
                self.assertEqual(settings.database_url.port, port)

    def test_environment_is_loaded(self) -> None:
        with patch.dict(os.environ, POSTGRES_PASSWORD="test", POSTGRES_PORT="5433"):
            settings = Settings(_env_file=None)
        self.assertEqual(settings.database_url.password, "test")
        self.assertEqual(settings.database_url.port, 5433)


class SessionTests(unittest.TestCase):
    def test_commit_rollback_and_close(self) -> None:
        settings = Settings(_env_file=None, postgres_password="test")
        manager = DatabaseSessionManager(settings.database_url)
        self.addCleanup(manager.dispose)
        for failure in (None, "operation", "commit"):
            with self.subTest(failure=failure):
                session = Mock()
                if failure == "commit":
                    session.commit.side_effect = ValueError("commit failed")
                with patch.object(manager, "_session_factory", return_value=session):
                    if failure:
                        with self.assertRaises(ValueError):
                            with manager.session():
                                if failure == "operation":
                                    raise ValueError("operation failed")
                    else:
                        with manager.session() as actual:
                            self.assertIs(actual, session)
                self.assertEqual(session.commit.call_count, failure != "operation")
                self.assertEqual(session.rollback.call_count, failure is not None)
                session.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
