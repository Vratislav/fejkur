"""
Password Manager for Voice Recognition Door Opener
Handles password loading and validation
"""

import os
import logging
import re
from typing import List, Optional


class PasswordManager:
    """Manages password loading and validation for voice recognition"""
    
    def __init__(self, config):
        """Initialize password manager"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.security_config = config.get_security_config()
        
        self.passwords = []
        self.password_file = config.get_password_file_path()
        self.loaded = False
        
        # Validation settings
        self.case_sensitive = False
        self.strip_whitespace = True
        self.normalize_text = True
    
    def load_passwords(self):
        """Load passwords from file"""
        try:
            self.logger.info(f"Loading passwords from: {self.password_file}")
            
            if not os.path.exists(self.password_file):
                self.logger.warning(f"Password file not found: {self.password_file}")
                self.logger.info("Creating default password file...")
                self._create_default_password_file()
            
            # Read password file
            with open(self.password_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Parse passwords
            self.passwords = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Add password to list
                password = self._normalize_password(line)
                if password:
                    self.passwords.append(password)
                    self.logger.debug(f"Loaded password: '{password}'")
            
            self.loaded = True
            self.logger.info(f"Loaded {len(self.passwords)} passwords")
            
            # Validate that we have at least one password
            if not self.passwords:
                self.logger.warning("No passwords loaded - system will not function properly")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading passwords: {e}")
            return False
    
    def _create_default_password_file(self):
        """Create default password file with sample passwords"""
        try:
            # Create directory if it doesn't exist
            password_dir = os.path.dirname(self.password_file)
            if password_dir and not os.path.exists(password_dir):
                os.makedirs(password_dir, exist_ok=True)
            
            # Create default password file
            with open(self.password_file, 'w', encoding='utf-8') as file:
                file.write("# Voice Recognition Passwords\n")
                file.write("# One password per line\n")
                file.write("# These will be matched against VOSK speech recognition output\n\n")
                file.write("otevři\n")
                file.write("otevři dveře\n")
                file.write("otevři prosím\n")
                file.write("otevři dveře prosím\n")
                file.write("otevři bránu\n")
                file.write("otevři bránu prosím\n")
                file.write("otevři vrata\n")
                file.write("otevři vrata prosím\n")
                file.write("otevři garáž\n")
                file.write("otevři garáž prosím\n")
            
            self.logger.info(f"Created default password file: {self.password_file}")
            
        except Exception as e:
            self.logger.error(f"Error creating default password file: {e}")
    
    def _normalize_password(self, password: str) -> Optional[str]:
        """Normalize password for comparison"""
        if not password:
            return None
        
        # Strip whitespace
        if self.strip_whitespace:
            password = password.strip()
        
        # Convert to lowercase if not case sensitive
        if not self.case_sensitive:
            password = password.lower()
        
        # Normalize text (remove extra spaces, etc.)
        if self.normalize_text:
            # Remove [unk] tokens from VOSK
            password = re.sub(r'\[unk\]', '', password)
            # Remove extra whitespace
            password = re.sub(r'\s+', ' ', password)
            # Remove leading/trailing whitespace
            password = password.strip()
        
        return password if password else None
    
    def check_password(self, recognized_text: str) -> bool:
        """Check if recognized text matches any password"""
        try:
            if not self.loaded:
                self.logger.error("Passwords not loaded")
                return False
            
            if not recognized_text:
                self.logger.warning("No recognized text to check")
                return False
            
            # Normalize recognized text
            normalized_text = self._normalize_password(recognized_text)
            if not normalized_text:
                return False
            
            self.logger.debug(f"Checking recognized text: '{normalized_text}'")
            
            # Check against all passwords
            for password in self.passwords:
                if self._compare_texts(normalized_text, password):
                    self.logger.info(f"Password match found: '{password}'")
                    return True
            
            self.logger.debug("No password match found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking password: {e}")
            return False
    
    def _compare_texts(self, text1: str, text2: str) -> bool:
        """Compare two texts for password matching"""
        try:
            # Exact match
            if text1 == text2:
                return True
            
            # Partial match - check if password is contained in recognized text
            if text2 in text1:
                self.logger.debug(f"Partial match: '{text2}' found in '{text1}'")
                return True
            
            # Reverse partial match - check if recognized text is contained in password
            if text1 in text2:
                self.logger.debug(f"Reverse partial match: '{text1}' found in '{text2}'")
                return True
            
            # Word-based partial matching - require at least 2 words to match
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            # Check if at least 2 password words are in recognized text
            intersection = words2.intersection(words1)
            if len(intersection) >= 2:
                self.logger.debug(f"Word-based match: {intersection} found in '{text1}'")
                return True
            
            # For single words, require exact match or high similarity
            if len(words2) == 1 and len(intersection) == 1:
                # Only match if the single word is the complete recognized text
                if text1.strip() == text2.strip():
                    self.logger.debug(f"Single word exact match: '{text1}' == '{text2}'")
                    return True
            
            # Fuzzy matching (optional)
            # This could be enhanced with more sophisticated matching algorithms
            similarity = self._calculate_similarity(text1, text2)
            if similarity >= 0.8:  # Higher threshold for stricter matching
                self.logger.debug(f"Fuzzy match: '{text1}' ~ '{text2}' (similarity: {similarity:.3f})")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error comparing texts: {e}")
            return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        try:
            # Simple Levenshtein distance-based similarity
            if not text1 or not text2:
                return 0.0
            
            # Convert to sets of words for better matching
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            if not words1 or not words2:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def add_password(self, password: str) -> bool:
        """Add a new password to the list"""
        try:
            normalized_password = self._normalize_password(password)
            if not normalized_password:
                self.logger.warning("Invalid password format")
                return False
            
            if normalized_password in self.passwords:
                self.logger.warning("Password already exists")
                return False
            
            self.passwords.append(normalized_password)
            self.logger.info(f"Added password: '{normalized_password}'")
            
            # Save to file
            return self._save_passwords()
            
        except Exception as e:
            self.logger.error(f"Error adding password: {e}")
            return False
    
    def remove_password(self, password: str) -> bool:
        """Remove a password from the list"""
        try:
            normalized_password = self._normalize_password(password)
            if not normalized_password:
                return False
            
            if normalized_password in self.passwords:
                self.passwords.remove(normalized_password)
                self.logger.info(f"Removed password: '{normalized_password}'")
                return self._save_passwords()
            else:
                self.logger.warning("Password not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing password: {e}")
            return False
    
    def _save_passwords(self) -> bool:
        """Save passwords to file"""
        try:
            with open(self.password_file, 'w', encoding='utf-8') as file:
                file.write("# Voice Recognition Passwords\n")
                file.write("# One password per line\n")
                file.write("# These will be matched against VOSK speech recognition output\n\n")
                
                for password in sorted(self.passwords):
                    file.write(f"{password}\n")
            
            self.logger.info(f"Saved {len(self.passwords)} passwords to file")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving passwords: {e}")
            return False
    
    def get_passwords(self) -> List[str]:
        """Get list of all passwords"""
        return self.passwords.copy()
    
    def get_password_count(self) -> int:
        """Get number of loaded passwords"""
        return len(self.passwords)
    
    def is_loaded(self) -> bool:
        """Check if passwords are loaded"""
        return self.loaded
    
    def reload_passwords(self) -> bool:
        """Reload passwords from file"""
        self.loaded = False
        self.passwords = []
        return self.load_passwords()
    
    def test_password_matching(self, test_text: str) -> List[str]:
        """Test password matching and return all matches"""
        matches = []
        
        try:
            normalized_text = self._normalize_password(test_text)
            if not normalized_text:
                return matches
            
            for password in self.passwords:
                if self._compare_texts(normalized_text, password):
                    matches.append(password)
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error testing password matching: {e}")
            return matches
    
    def get_password_info(self):
        """Get password manager information"""
        return {
            'password_file': self.password_file,
            'loaded': self.loaded,
            'password_count': len(self.passwords),
            'case_sensitive': self.case_sensitive,
            'strip_whitespace': self.strip_whitespace,
            'normalize_text': self.normalize_text
        } 