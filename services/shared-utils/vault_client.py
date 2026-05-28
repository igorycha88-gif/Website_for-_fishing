from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class VaultClient:
    _instance: Optional['VaultClient'] = None
    _client: Optional[object] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.vault_addr = os.getenv('VAULT_ADDR', 'http://vault:8200')
        self.role_id = os.getenv('VAULT_ROLE_ID')
        self.secret_id = os.getenv('VAULT_SECRET_ID')
        self._token: Optional[str] = None

        if not self.role_id or not self.secret_id:
            logger.warning("VAULT_ROLE_ID or VAULT_SECRET_ID not set, Vault client will not authenticate")
            self._initialized = True
            return

        try:
            import hvac
            self._client = hvac.Client(url=self.vault_addr)
            self._authenticate()
            self._initialized = True
        except ImportError:
            logger.error("hvac library not installed. Install with: pip install hvac")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            self._initialized = True

    def _authenticate(self) -> None:
        if not self._client:
            return

        try:
            auth_response = self._client.auth.approle.login(
                role_id=self.role_id,
                secret_id=self.secret_id
            )
            self._token = auth_response.get('auth', {}).get('client_token')
            logger.info("Successfully authenticated with Vault")
        except Exception as e:
            logger.error(f"Failed to authenticate with Vault: {e}")
            raise

    def get_secret(self, path: str) -> dict:
        if not self._client:
            raise RuntimeError("Vault client not initialized")

        try:
            response = self._client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point='secret'
            )
            return response['data']['data']
        except Exception as e:
            logger.error(f"Failed to get secret at {path}: {e}")
            raise

    def get_database_credentials(self) -> tuple:
        try:
            secret = self.get_secret('fishmap/database/postgres')
            password = secret.get('password')
            username = os.getenv('POSTGRES_USER', 'postgres')
            return (username, password)
        except Exception as e:
            logger.error(f"Failed to get database credentials: {e}")
            raise

    def get_jwt_secret(self) -> str:
        try:
            secret = self.get_secret('fishmap/auth/jwt')
            return secret.get('secret_key')
        except Exception as e:
            logger.error(f"Failed to get JWT secret: {e}")
            raise

    def get_smtp_password(self) -> str:
        try:
            secret = self.get_secret('fishmap/email/smtp')
            return secret.get('password')
        except Exception as e:
            logger.error(f"Failed to get SMTP password: {e}")
            raise

    def get_weather_api_key(self) -> str:
        try:
            secret = self.get_secret('fishmap/external/weather')
            return secret.get('api_key')
        except Exception as e:
            logger.error(f"Failed to get weather API key: {e}")
            raise

    def get_stripe_keys(self) -> dict:
        try:
            secret = self.get_secret('fishmap/payment/stripe')
            return {
                'secret_key': secret.get('secret_key'),
                'webhook_secret': secret.get('webhook_secret')
            }
        except Exception as e:
            logger.error(f"Failed to get Stripe keys: {e}")
            raise

    def get_cloudinary_secret(self) -> str:
        try:
            secret = self.get_secret('fishmap/storage/cloudinary')
            return secret.get('api_secret')
        except Exception as e:
            logger.error(f"Failed to get Cloudinary secret: {e}")
            raise

    def get_mapbox_api_key(self) -> str:
        try:
            secret = self.get_secret('fishmap/external/mapbox')
            return secret.get('api_key')
        except Exception as e:
            logger.error(f"Failed to get Mapbox API key: {e}")
            raise

    def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            return self._client.sys.is_initialized()
        except Exception:
            return False

    def is_available(self) -> bool:
        return self._client is not None and self._token is not None


_vault_client: Optional[VaultClient] = None


def get_vault_client() -> VaultClient:
    global _vault_client
    if _vault_client is None:
        _vault_client = VaultClient()
    return _vault_client


def reset_vault_client():
    global _vault_client
    _vault_client = None
    VaultClient._instance = None
    VaultClient._client = None
    VaultClient._initialized = False
