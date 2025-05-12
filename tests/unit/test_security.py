#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Unit Tests for Security Module
Author: ECLIPSEMOON
"""

import os
import sys
import unittest
import tempfile
import shutil
import base64
from cryptography.fernet import Fernet

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.security import SecurityManager, get_security_manager


class TestSecurityManager(unittest.TestCase):
    """Test cases for SecurityManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for keys
        self.test_keys_dir = tempfile.mkdtemp()
        
        # Create security manager
        self.security_manager = SecurityManager(self.test_keys_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test directory
        shutil.rmtree(self.test_keys_dir)
    
    def test_generate_and_load_encryption_key(self):
        """Test generating and loading an encryption key."""
        # Generate key
        key_id = "test_key"
        key = self.security_manager.generate_encryption_key(key_id)
        
        # Verify key was generated
        self.assertIsNotNone(key)
        self.assertIn(key_id, self.security_manager.encryption_keys)
        
        # Check if key file was created
        key_path = os.path.join(self.test_keys_dir, f"{key_id}.key")
        self.assertTrue(os.path.exists(key_path))
        
        # Load key
        loaded_key = self.security_manager.load_encryption_key(key_id)
        
        # Verify loaded key
        self.assertEqual(loaded_key, key)
    
    def test_encrypt_decrypt_data(self):
        """Test encrypting and decrypting data."""
        # Generate key
        key_id = "test_key"
        self.security_manager.generate_encryption_key(key_id)
        
        # Test data
        test_data = "Hello, world!"
        
        # Encrypt data
        encrypted_data = self.security_manager.encrypt_data(test_data, key_id)
        
        # Verify encrypted data
        self.assertIsNotNone(encrypted_data)
        self.assertNotEqual(encrypted_data, test_data.encode('utf-8'))
        
        # Decrypt data
        decrypted_data = self.security_manager.decrypt_data(encrypted_data, key_id)
        
        # Verify decrypted data
        self.assertEqual(decrypted_data.decode('utf-8'), test_data)
    
    def test_generate_and_load_key_pair(self):
        """Test generating and loading an RSA key pair."""
        # Generate key pair
        key_id = "test_rsa"
        private_key, public_key = self.security_manager.generate_key_pair(key_id)
        
        # Verify keys were generated
        self.assertIsNotNone(private_key)
        self.assertIsNotNone(public_key)
        
        # Check if key files were created
        private_key_path = os.path.join(self.test_keys_dir, f"{key_id}_private.pem")
        public_key_path = os.path.join(self.test_keys_dir, f"{key_id}_public.pem")
        self.assertTrue(os.path.exists(private_key_path))
        self.assertTrue(os.path.exists(public_key_path))
        
        # Load keys
        loaded_private_key = self.security_manager.load_private_key(key_id)
        loaded_public_key = self.security_manager.load_public_key(key_id)
        
        # Verify loaded keys
        self.assertIsNotNone(loaded_private_key)
        self.assertIsNotNone(loaded_public_key)
    
    def test_encrypt_decrypt_with_rsa(self):
        """Test encrypting and decrypting data with RSA."""
        # Generate key pair
        key_id = "test_rsa"
        self.security_manager.generate_key_pair(key_id)
        
        # Test data
        test_data = "Secret message"
        
        # Encrypt data
        encrypted_data = self.security_manager.encrypt_with_public_key(test_data, key_id)
        
        # Verify encrypted data
        self.assertIsNotNone(encrypted_data)
        self.assertNotEqual(encrypted_data, test_data.encode('utf-8'))
        
        # Decrypt data
        decrypted_data = self.security_manager.decrypt_with_private_key(encrypted_data, key_id)
        
        # Verify decrypted data
        self.assertEqual(decrypted_data.decode('utf-8'), test_data)
    
    def test_hash_verify_password(self):
        """Test hashing and verifying a password."""
        # Test password
        password = "password123"
        
        # Hash password
        password_hash, salt = self.security_manager.hash_password(password)
        
        # Verify hash and salt
        self.assertIsNotNone(password_hash)
        self.assertIsNotNone(salt)
        
        # Verify correct password
        is_valid = self.security_manager.verify_password(password, password_hash, salt)
        self.assertTrue(is_valid)
        
        # Verify incorrect password
        is_valid = self.security_manager.verify_password("wrong_password", password_hash, salt)
        self.assertFalse(is_valid)
    
    def test_generate_token(self):
        """Test generating a secure token."""
        # Generate token
        token = self.security_manager.generate_token()
        
        # Verify token
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 0)
        
        # Generate token with specific length
        token_length = 64
        token = self.security_manager.generate_token(token_length)
        
        # Verify token length (base64 encoding increases length)
        decoded_length = len(base64.urlsafe_b64decode(token + "=="))
        self.assertEqual(decoded_length, token_length)
    
    def test_create_verify_hmac(self):
        """Test creating and verifying an HMAC."""
        # Test data and key
        data = "Data to authenticate"
        key = "secret_key"
        
        # Create HMAC
        hmac_digest = self.security_manager.create_hmac(data, key)
        
        # Verify HMAC
        self.assertIsNotNone(hmac_digest)
        
        # Verify valid HMAC
        is_valid = self.security_manager.verify_hmac(data, key, hmac_digest)
        self.assertTrue(is_valid)
        
        # Verify invalid HMAC (different data)
        is_valid = self.security_manager.verify_hmac("Different data", key, hmac_digest)
        self.assertFalse(is_valid)
        
        # Verify invalid HMAC (different key)
        is_valid = self.security_manager.verify_hmac(data, "different_key", hmac_digest)
        self.assertFalse(is_valid)
    
    def test_get_security_manager(self):
        """Test getting the singleton security manager."""
        # Get security manager
        manager1 = get_security_manager(self.test_keys_dir)
        manager2 = get_security_manager(self.test_keys_dir)
        
        # Verify it's the same instance
        self.assertIs(manager1, manager2)


if __name__ == '__main__':
    unittest.main()