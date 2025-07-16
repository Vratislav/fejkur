"""
Configuration Manager for Voice Recognition Door Opener
Handles loading and accessing configuration settings
"""

import os
import yaml
import logging
from pathlib import Path


class ConfigManager:
    """Manages configuration settings for the voice recognition system"""
    
    def __init__(self, config_file="config.yaml"):
        """Initialize configuration manager"""
        self.config_file = config_file
        self.config = {}
        self.logger = logging.getLogger(__name__)
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            # Get the project root directory (2 levels up from src/core/)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, '..', '..')
            config_path = os.path.join(project_root, 'config', self.config_file)
            
            if not os.path.exists(config_path):
                self.logger.error(f"Configuration file not found: {config_path}")
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
            
            self.logger.info(f"Configuration loaded from {config_path}")
            
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing configuration file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise
    
    def get(self, key, default=None):
        """Get configuration value by key"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_audio_config(self):
        """Get audio configuration"""
        return self.get('audio', {})
    
    def get_bluetooth_config(self):
        """Get Bluetooth configuration"""
        return self.get('bluetooth', {})
    
    def get_gpio_config(self):
        """Get GPIO configuration"""
        return self.get('gpio', {})
    
    def get_mqtt_config(self):
        """Get MQTT configuration"""
        return self.get('mqtt', {})
    
    def get_voice_config(self):
        """Get voice recognition configuration"""
        voice_config = self.get('voice', {})
        
        # Handle language-based model path selection
        language = voice_config.get('language', 'en')
        model_path = voice_config.get('model_path', '')
        
        # If model_path is not set or doesn't exist, try language-specific path
        if not model_path or not os.path.exists(model_path):
            project_root = self.get_project_root()
            if language == 'cs':
                language_model_path = os.path.join(project_root, 'models', 'vosk-model-cs')
            elif language == 'en':
                language_model_path = os.path.join(project_root, 'models', 'vosk-model-en')
            else:
                language_model_path = os.path.join(project_root, 'models', f'vosk-model-{language}')
            
            if os.path.exists(language_model_path):
                voice_config['model_path'] = language_model_path
                self.logger.info(f"Using {language} model at: {language_model_path}")
            else:
                self.logger.warning(f"Model not found for language '{language}' at: {language_model_path}")
        
        return voice_config
    
    def get_security_config(self):
        """Get security configuration"""
        return self.get('security', {})
    
    def get_logging_config(self):
        """Get logging configuration"""
        return self.get('logging', {})
    
    def get_audio_files_config(self):
        """Get audio files configuration"""
        return self.get('audio_files', {})
    
    def validate_config(self):
        """Validate configuration settings"""
        errors = []
        
        # Check required sections
        required_sections = ['audio', 'bluetooth', 'gpio', 'mqtt', 'voice', 'security', 'logging']
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required configuration section: {section}")
        
        # Check audio settings
        audio_config = self.get_audio_config()
        if not audio_config.get('sample_rate'):
            errors.append("Missing audio sample_rate setting")
        if not audio_config.get('channels'):
            errors.append("Missing audio channels setting")
        
        # Check voice settings
        voice_config = self.get_voice_config()
        if not voice_config.get('model_path'):
            errors.append("Missing voice model_path setting")
        
        # Check MQTT settings
        mqtt_config = self.get_mqtt_config()
        if not mqtt_config.get('broker'):
            errors.append("Missing MQTT broker setting")
        if not mqtt_config.get('topic'):
            errors.append("Missing MQTT topic setting")
        
        # Check GPIO settings
        gpio_config = self.get_gpio_config()
        if gpio_config.get('button_pin') is None:
            errors.append("Missing GPIO button_pin setting")
        
        if errors:
            for error in errors:
                self.logger.error(error)
            return False
        
        self.logger.info("Configuration validation passed")
        return True
    
    def get_script_directory(self):
        """Get the directory where the script is located"""
        return os.path.dirname(os.path.abspath(__file__))
    
    def get_project_root(self):
        """Get the project root directory"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, '..', '..')
    
    def get_audio_file_path(self, audio_type):
        """Get full path to audio file"""
        audio_files = self.get_audio_files_config()
        audio_file = audio_files.get(audio_type)
        
        if not audio_file:
            self.logger.warning(f"No audio file configured for type: {audio_type}")
            return None
        
        # If it's already an absolute path, return as is
        if os.path.isabs(audio_file):
            return audio_file
        
        # Otherwise, make it relative to the project root
        project_root = self.get_project_root()
        return os.path.join(project_root, audio_file)
    
    def get_password_file_path(self):
        """Get full path to password file"""
        password_file = self.get('security.password_file', 'passwords.txt')
        
        # If it's already an absolute path, return as is
        if os.path.isabs(password_file):
            return password_file
        
        # Otherwise, make it relative to the project root
        project_root = self.get_project_root()
        return os.path.join(project_root, 'config', password_file) 