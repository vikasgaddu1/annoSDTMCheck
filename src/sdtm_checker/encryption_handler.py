"""
Encryption and decryption handler for configuration files.
"""

import os
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


class EncryptionHandler:
    """Handles encryption and decryption of configuration files."""

    def __init__(self, key_path: str = "config/secret.key"):
        """
        Initialize the encryption handler.

        Args:
            key_path: Path to the encryption key file
        """
        self.key_path = key_path
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        """Load the encryption key from a file or generate a new one."""
        try:
            if os.path.exists(self.key_path):
                with open(self.key_path, 'rb') as f:
                    return f.read()
            else:
                key = Fernet.generate_key()
                with open(self.key_path, 'wb') as f:
                    f.write(key)
                return key
        except Exception as e:
            logger.error(f"Error loading or generating encryption key: {e}")
            raise

    def encrypt(self, data: str) -> bytes:
        """
        Encrypt data.

        Args:
            data: The data to encrypt (as a string)

        Returns:
            The encrypted data (as bytes)
        """
        try:
            return self.fernet.encrypt(data.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise

    def decrypt(self, encrypted_data: bytes) -> str:
        """
        Decrypt data.

        Args:
            encrypted_data: The data to decrypt (as bytes)

        Returns:
            The decrypted data (as a string)
        """
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise
