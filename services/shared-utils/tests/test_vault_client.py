import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vault_client import VaultClient, get_vault_client, reset_vault_client


class TestVaultClientInit:
    def test_init_without_credentials(self, monkeypatch):
        reset_vault_client()
        monkeypatch.delenv('VAULT_ROLE_ID', raising=False)
        monkeypatch.delenv('VAULT_SECRET_ID', raising=False)
        
        client = VaultClient()
        
        assert client.role_id is None
        assert client.secret_id is None
        assert client._client is None

    def test_init_with_credentials(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ADDR', 'http://vault:8200')
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            
            assert client.role_id == 'test-role-id'
            assert client.secret_id == 'test-secret-id'
            mock_hvac.Client.assert_called_once_with(url='http://vault:8200')

    def test_init_authentication_failure(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ADDR', 'http://vault:8200')
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.side_effect = Exception("Auth failed")
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            assert client._client is not None
            assert client._token is None
            assert client.is_available() is False

    def test_singleton_pattern(self, monkeypatch):
        reset_vault_client()
        monkeypatch.delenv('VAULT_ROLE_ID', raising=False)
        monkeypatch.delenv('VAULT_SECRET_ID', raising=False)
        
        client1 = VaultClient()
        client2 = VaultClient()
        
        assert client1 is client2


class TestVaultClientGetSecret:
    def test_get_secret_success(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {'password': 'secret123'}
            }
        }
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.get_secret('fishmap/database/postgres')
            
            assert result == {'password': 'secret123'}
            mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
                path='fishmap/database/postgres',
                mount_point='secret'
            )

    def test_get_secret_failure(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Secret not found")
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            
            with pytest.raises(Exception, match="Secret not found"):
                client.get_secret('invalid/path')

    def test_get_secret_without_client(self, monkeypatch):
        reset_vault_client()
        monkeypatch.delenv('VAULT_ROLE_ID', raising=False)
        monkeypatch.delenv('VAULT_SECRET_ID', raising=False)
        
        client = VaultClient()
        
        with pytest.raises(RuntimeError, match="Vault client not initialized"):
            client.get_secret('any/path')


class TestVaultClientMethods:
    def test_get_database_credentials(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        monkeypatch.setenv('POSTGRES_USER', 'custom_user')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {'password': 'db_password'}
            }
        }
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            username, password = client.get_database_credentials()
            
            assert username == 'custom_user'
            assert password == 'db_password'

    def test_get_jwt_secret(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {'secret_key': 'my-jwt-secret-key'}
            }
        }
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.get_jwt_secret()
            
            assert result == 'my-jwt-secret-key'

    def test_get_smtp_password(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {'password': 'smtp_password_123'}
            }
        }
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.get_smtp_password()
            
            assert result == 'smtp_password_123'

    def test_get_weather_api_key(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {'api_key': 'weather_api_key_xyz'}
            }
        }
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.get_weather_api_key()
            
            assert result == 'weather_api_key_xyz'

    def test_get_stripe_keys(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {
                    'secret_key': 'sk_test_123',
                    'webhook_secret': 'whsec_456'
                }
            }
        }
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.get_stripe_keys()
            
            assert result == {
                'secret_key': 'sk_test_123',
                'webhook_secret': 'whsec_456'
            }

    def test_get_cloudinary_secret(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {'api_secret': 'cloudinary_secret_789'}
            }
        }
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.get_cloudinary_secret()
            
            assert result == 'cloudinary_secret_789'

    def test_get_mapbox_api_key(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {'api_key': 'mapbox_key_abc'}
            }
        }
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.get_mapbox_api_key()
            
            assert result == 'mapbox_key_abc'


class TestVaultClientHealthCheck:
    def test_health_check_initialized(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.sys.is_initialized.return_value = True
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.health_check()
            
            assert result is True

    def test_health_check_not_initialized(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.sys.is_initialized.return_value = False
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.health_check()
            
            assert result is False

    def test_health_check_exception(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        mock_client.sys.is_initialized.side_effect = Exception("Connection error")
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.health_check()
            
            assert result is False

    def test_health_check_no_client(self, monkeypatch):
        reset_vault_client()
        monkeypatch.delenv('VAULT_ROLE_ID', raising=False)
        monkeypatch.delenv('VAULT_SECRET_ID', raising=False)
        
        client = VaultClient()
        result = client.health_check()
        
        assert result is False


class TestVaultClientIsAvailable:
    def test_is_available_true(self, monkeypatch):
        reset_vault_client()
        monkeypatch.setenv('VAULT_ROLE_ID', 'test-role-id')
        monkeypatch.setenv('VAULT_SECRET_ID', 'test-secret-id')
        
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client
        mock_client.auth.approle.login.return_value = {
            'auth': {'client_token': 'test-token'}
        }
        
        with patch.dict('sys.modules', {'hvac': mock_hvac}):
            client = VaultClient()
            result = client.is_available()
            
            assert result is True

    def test_is_available_false_no_client(self, monkeypatch):
        reset_vault_client()
        monkeypatch.delenv('VAULT_ROLE_ID', raising=False)
        monkeypatch.delenv('VAULT_SECRET_ID', raising=False)
        
        client = VaultClient()
        result = client.is_available()
        
        assert result is False


class TestGetVaultClient:
    def test_get_vault_client_singleton(self, monkeypatch):
        reset_vault_client()
        monkeypatch.delenv('VAULT_ROLE_ID', raising=False)
        monkeypatch.delenv('VAULT_SECRET_ID', raising=False)
        
        client1 = get_vault_client()
        client2 = get_vault_client()
        
        assert client1 is client2

    def test_reset_vault_client(self, monkeypatch):
        reset_vault_client()
        monkeypatch.delenv('VAULT_ROLE_ID', raising=False)
        monkeypatch.delenv('VAULT_SECRET_ID', raising=False)
        
        client1 = get_vault_client()
        reset_vault_client()
        client2 = get_vault_client()
        
        assert client1 is not client2
