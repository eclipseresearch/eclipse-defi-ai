#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Core Security Module
Author: ECLIPSEMOON
"""

import os
import base64
import hashlib
import hmac
import json
import logging
import secrets
from typing import Dict, List, Optional, Union, Any, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption
)

# Setup logger
logger = logging.getLogger("core.security")


class SecurityManager:
    """Manager for security and encryption utilities."""
    
    def __init__(self, keys_dir: Optional[str] = None):
        """
        Initialize the security manager.
        
        Args:
            keys_dir: Directory to store keys (if None, use default)
        """
        self.keys_dir = keys_dir or os.path.join(os.path.expanduser("~"), ".eclipsemoon", "keys")
        self.encryption_keys: Dict[str, bytes] = {}
        
        # Ensure keys directory exists
        os.makedirs(self.keys_dir, exist_ok=True)
    
    def generate_encryption_key(self, key_id: str) -> bytes:
        """
        Generate a new encryption key.
        
        Args:
            key_id: ID for the key
            
        Returns:
            bytes: Generated key
        """
        logger.info(f"Generating encryption key: {key_id}")
        
        # Generate a new Fernet key
        key = Fernet.generate_key()
        
        # Save key
        self.encryption_keys[key_id] = key
        
        # Save to file
        key_path = os.path.join(self.keys_dir, f"{key_id}.key")
        
        with open(key_path, 'wb') as f:
            f.write(key)
        
        logger.info(f"Encryption key {key_id} generated successfully")
        return key
    
    def load_encryption_key(self, key_id: str) -> Optional[bytes]:
        """
        Load an encryption key.
        
        Args:
            key_id: ID of the key to load
            
        Returns:
            Optional[bytes]: Loaded key if successful, None otherwise
        """
        logger.info(f"Loading encryption key: {key_id}")
        
        # Check if key is already loaded
        if key_id in self.encryption_keys:
            return self.encryption_keys[key_id]
        
        # Load from file
        key_path = os.path.join(self.keys_dir, f"{key_id}.key")
        
        if not os.path.exists(key_path):
            logger.error(f"Encryption key {key_id} not found")
            return None
        
        try:
            with open(key_path, 'rb') as f:
                key = f.read()
            
            self.encryption_keys[key_id] = key
            logger.info(f"Encryption key {key_id} loaded successfully")
            return key
        
        except Exception as e:
            logger.error(f"Error loading encryption key {key_id}: {str(e)}")
            return None
    
    def encrypt_data(
        self,
        data: Union[str, bytes],
        key_id: str,
    ) -> Optional[bytes]:
        """
        Encrypt data using a key.
        
        Args:
            data: Data to encrypt
            key_id: ID of the key to use
            
        Returns:
            Optional[bytes]: Encrypted data if successful, None otherwise
        """
        logger.info(f"Encrypting data using key {key_id}")
        
        # Load key if not loaded
        key = self.load_encryption_key(key_id)
        
        if not key:
            logger.error(f"Encryption key {key_id} not found")
            return None
        
        try:
            # Convert data to bytes if it's a string
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Create Fernet cipher
            cipher = Fernet(key)
            
            # Encrypt data
            encrypted_data = cipher.encrypt(data)
            
            logger.info("Data encrypted successfully")
            return encrypted_data
        
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            return None
    
    def decrypt_data(
        self,
        encrypted_data: bytes,
        key_id: str,
    ) -> Optional[bytes]:
        """
        Decrypt data using a key.
        
        Args:
            encrypted_data: Data to decrypt
            key_id: ID of the key to use
            
        Returns:
            Optional[bytes]: Decrypted data if successful, None otherwise
        """
        logger.info(f"Decrypting data using key {key_id}")
        
        # Load key if not loaded
        key = self.load_encryption_key(key_id)
        
        if not key:
            logger.error(f"Encryption key {key_id} not found")
            return None
        
        try:
            # Create Fernet cipher
            cipher = Fernet(key)
            
            # Decrypt data
            decrypted_data = cipher.decrypt(encrypted_data)
            
            logger.info("Data decrypted successfully")
            return decrypted_data
        
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            return None
    
    def generate_key_pair(self, key_id: str, key_size: int = 2048) -> Tuple[bytes, bytes]:
        """
        Generate a new RSA key pair.
        
        Args:
            key_id: ID for the key pair
            key_size: Size of the key in bits
            
        Returns:
            Tuple[bytes, bytes]: Private key and public key
        """
        logger.info(f"Generating RSA key pair: {key_id}")
        
        # Generate a new RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )
        
        # Save keys
        private_key_path = os.path.join(self.keys_dir, f"{key_id}_private.pem")
        public_key_path = os.path.join(self.keys_dir, f"{key_id}_public.pem")
        
        with open(private_key_path, 'wb') as f:
            f.write(private_pem)
        
        with open(public_key_path, 'wb') as f:
            f.write(public_pem)
        
        logger.info(f"RSA key pair {key_id} generated successfully")
        return private_pem, public_pem
    
    def load_private_key(self, key_id: str) -> Optional[rsa.RSAPrivateKey]:
        """
        Load a private key.
        
        Args:
            key_id: ID of the key to load
            
        Returns:
            Optional[rsa.RSAPrivateKey]: Loaded key if successful, None otherwise
        """
        logger.info(f"Loading private key: {key_id}")
        
        # Load from file
        key_path = os.path.join(self.keys_dir, f"{key_id}_private.pem")
        
        if not os.path.exists(key_path):
            logger.error(f"Private key {key_id} not found")
            return None
        
        try:
            with open(key_path, 'rb') as f:
                private_pem = f.read()
            
            private_key = load_pem_private_key(
                private_pem,
                password=None
            )
            
            logger.info(f"Private key {key_id} loaded successfully")
            return private_key
        
        except Exception as e:
            logger.error(f"Error loading private key {key_id}: {str(e)}")
            return None
    
    def load_public_key(self, key_id: str) -> Optional[rsa.RSAPublicKey]:
        """
        Load a public key.
        
        Args:
            key_id: ID of the key to load
            
        Returns:
            Optional[rsa.RSAPublicKey]: Loaded key if successful, None otherwise
        """
        logger.info(f"Loading public key: {key_id}")
        
        # Load from file
        key_path = os.path.join(self.keys_dir, f"{key_id}_public.pem")
        
        if not os.path.exists(key_path):
            logger.error(f"Public key {key_id} not found")
            return None
        
        try:
            with open(key_path, 'rb') as f:
                public_pem = f.read()
            
            public_key = load_pem_public_key(public_pem)
            
            logger.info(f"Public key {key_id} loaded successfully")
            return public_key
        
        except Exception as e:
            logger.error(f"Error loading public key {key_id}: {str(e)}")
            return None
    
    def encrypt_with_public_key(
        self,
        data: Union[str, bytes],
        key_id: str,
    ) -> Optional[bytes]:
        """
        Encrypt data using a public key.
        
        Args:
            data: Data to encrypt
            key_id: ID of the key to use
            
        Returns:
            Optional[bytes]: Encrypted data if successful, None otherwise
        """
        logger.info(f"Encrypting data using public key {key_id}")
        
        # Load public key
        public_key = self.load_public_key(key_id)
        
        if not public_key:
            logger.error(f"Public key {key_id} not found")
            return None
        
        try:
            # Convert data to bytes if it's a string
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Encrypt data
            encrypted_data = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            logger.info("Data encrypted successfully")
            return encrypted_data
        
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            return None
    
    def decrypt_with_private_key(
        self,
        encrypted_data: bytes,
        key_id: str,
    ) -> Optional[bytes]:
        """
        Decrypt data using a private key.
        
        Args:
            encrypted_data: Data to decrypt
            key_id: ID of the key to use
            
        Returns:
            Optional[bytes]: Decrypted data if successful, None otherwise
        """
        logger.info(f"Decrypting data using private key {key_id}")
        
        # Load private key
        private_key = self.load_private_key(key_id)
        
        if not private_key:
            logger.error(f"Private key {key_id} not found")
            return None
        
        try:
            # Decrypt data
            decrypted_data = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            logger.info("Data decrypted successfully")
            return decrypted_data
        
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            return None
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Hash a password using PBKDF2.
        
        Args:
            password: Password to hash
            salt: Salt to use (if None, generate a new one)
            
        Returns:
            Tuple[bytes, bytes]: Password hash and salt
        """
        logger.info("Hashing password")
        
        # Generate salt if not provided
        if salt is None:
            salt = os.urandom(16)
        
        # Create PBKDF2 KDF
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        
        # Hash password
        password_hash = kdf.derive(password.encode('utf-8'))
        
        logger.info("Password hashed successfully")
        return password_hash, salt
    
    def verify_password(
        self,
        password: str,
        password_hash: bytes,
        salt: bytes,
    ) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: Password to verify
            password_hash: Hash to verify against
            salt: Salt used for hashing
            
        Returns:
            bool: True if password is correct, False otherwise
        """
        logger.info("Verifying password")
        
        # Create PBKDF2 KDF
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        
        try:
            # Verify password
            kdf.verify(password.encode('utf-8'), password_hash)
            
            logger.info("Password verified successfully")
            return True
        
        except Exception:
            logger.info("Password verification failed")
            return False
    
    def generate_token(self, length: int = 32) -> str:
        """
        Generate a secure random token.
        
        Args:
            length: Length of the token in bytes
            
        Returns:
            str: Generated token
        """
        logger.info(f"Generating token of length {length}")
        
        # Generate random bytes
        token_bytes = secrets.token_bytes(length)
        
        # Convert to URL-safe base64
        token = base64.urlsafe_b64encode(token_bytes).decode('utf-8').rstrip('=')
        
        logger.info("Token generated successfully")
        return token
    
    def create_hmac(
        self,
        data: Union[str, bytes],
        key: Union[str, bytes],
    ) -> bytes:
        """
        Create an HMAC for data.
        
        Args:
            data: Data to create HMAC for
            key: Key to use for HMAC
            
        Returns:
            bytes: HMAC
        """
        logger.info("Creating HMAC")
        
        # Convert data and key to bytes if they're strings
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if isinstance(key, str):
            key = key.encode('utf-8')
        
        # Create HMAC
        h = hmac.new(key, data, hashlib.sha256)
        
        logger.info("HMAC created successfully")
        return h.digest()
    
    def verify_hmac(
        self,
        data: Union[str, bytes],
        key: Union[str, bytes],
        hmac_digest: bytes,
    ) -> bool:
        """
        Verify an HMAC for data.
        
        Args:
            data: Data to verify HMAC for
            key: Key to use for HMAC
            hmac_digest: HMAC to verify against
            
        Returns:
            bool: True if HMAC is valid, False otherwise
        """
        logger.info("Verifying HMAC")
        
        # Create HMAC
        calculated_hmac = self.create_hmac(data, key)
        
        # Compare HMACs
        is_valid = hmac.compare_digest(calculated_hmac, hmac_digest)
        
        logger.info(f"HMAC verification {'successful' if is_valid else 'failed'}")
        return is_valid


# Singleton instance of SecurityManager
_security_manager = None


def get_security_manager(keys_dir: Optional[str] = None) -> SecurityManager:
    """
    Get the singleton instance of SecurityManager.
    
    Args:
        keys_dir: Directory to store keys (if None, use default)
        
    Returns:
        SecurityManager: Singleton instance of SecurityManager
    """
    global _security_manager
    
    if _security_manager is None:
        _security_manager = SecurityManager(keys_dir)
    
    return _security_manager


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Get security manager
    security_manager = get_security_manager()
    
    # Generate encryption key
    key = security_manager.generate_encryption_key("example_key")
    
    # Encrypt and decrypt data
    data = "Hello, world!"
    encrypted_data = security_manager.encrypt_data(data, "example_key")
    decrypted_data = security_manager.decrypt_data(encrypted_data, "example_key")
    
    print(f"Original data: {data}")
    print(f"Encrypted data: {encrypted_data}")
    print(f"Decrypted data: {decrypted_data.decode('utf-8')}")
    
    # Generate RSA key pair
    private_key, public_key = security_manager.generate_key_pair("example_rsa")
    
    # Encrypt and decrypt data with RSA
    rsa_data = "Secret message"
    rsa_encrypted_data = security_manager.encrypt_with_public_key(rsa_data, "example_rsa")
    rsa_decrypted_data = security_manager.decrypt_with_private_key(rsa_encrypted_data, "example_rsa")
    
    print(f"Original RSA data: {rsa_data}")
    print(f"Encrypted RSA data: {rsa_encrypted_data}")
    print(f"Decrypted RSA data: {rsa_decrypted_data.decode('utf-8')}")
    
    # Hash and verify password
    password = "password123"
    password_hash, salt = security_manager.hash_password(password)
    is_valid = security_manager.verify_password(password, password_hash, salt)
    
    print(f"Password: {password}")
    print(f"Password hash: {password_hash}")
    print(f"Salt: {salt}")
    print(f"Password valid: {is_valid}")
    
    # Generate token
    token = security_manager.generate_token()
    print(f"Token: {token}")
    
    # Create and verify HMAC
    hmac_data = "Data to authenticate"
    hmac_key = "secret_key"
    hmac_digest = security_manager.create_hmac(hmac_data, hmac_key)
    hmac_valid = security_manager.verify_hmac(hmac_data, hmac_key, hmac_digest)
    
    print(f"HMAC data: {hmac_data}")
    print(f"HMAC key: {hmac_key}")
    print(f"HMAC digest: {hmac_digest}")
    print(f"HMAC valid: {hmac_valid}")