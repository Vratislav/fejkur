"""
Bluetooth Manager for Voice Recognition Door Opener
Handles automatic connection to Bluetooth handsfree devices
Uses bluetoothctl commands instead of pybluez2 library
"""

import os
import time
import logging
import subprocess
import threading
from typing import Optional, List


class BluetoothManager:
    """Manages Bluetooth connections for handsfree devices"""
    
    def __init__(self, config):
        """Initialize Bluetooth manager"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.bluetooth_config = config.get_bluetooth_config()
        
        self.connected_device = None
        self.is_connected = False
        self.connection_thread = None
        self.running = False
    
    def initialize(self):
        """Initialize Bluetooth system"""
        try:
            self.logger.info("Initializing Bluetooth manager...")
            
            # Check if Bluetooth is available
            if not self._check_bluetooth_available():
                self.logger.error("Bluetooth not available")
                return False
            
            # Enable Bluetooth
            if not self._enable_bluetooth():
                self.logger.error("Failed to enable Bluetooth")
                return False
            
            # Start connection monitoring thread
            self.running = True
            self.connection_thread = threading.Thread(target=self._monitor_connection, daemon=True)
            self.connection_thread.start()
            
            self.logger.info("Bluetooth manager initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Bluetooth: {e}")
            return False
    
    def _check_bluetooth_available(self):
        """Check if Bluetooth is available on the system"""
        try:
            result = subprocess.run(['bluetoothctl', 'show'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.logger.error("bluetoothctl not available")
            return False
    
    def _enable_bluetooth(self):
        """Enable Bluetooth adapter"""
        try:
            # Power on Bluetooth adapter
            subprocess.run(['bluetoothctl', 'power', 'on'], 
                         capture_output=True, timeout=5)
            
            # Make device discoverable
            subprocess.run(['bluetoothctl', 'discoverable', 'on'], 
                         capture_output=True, timeout=5)
            
            # Make device pairable
            subprocess.run(['bluetoothctl', 'pairable', 'on'], 
                         capture_output=True, timeout=5)
            
            self.logger.info("Bluetooth adapter enabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable Bluetooth: {e}")
            return False
    
    def ensure_audio_profile(self):
        """Ensure Bluetooth device is set to headset profile and is default source"""
        if not self.connected_device:
            self.logger.warning("No connected device to set audio profile for.")
            return False
        
        mac = self.connected_device['mac'].replace(':', '_')
        card = f"bluez_card.{mac}"
        source = f"bluez_input.{mac}.0"
        
        # Wait for Bluetooth audio card to appear (can take a few seconds)
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                # Check if card exists
                result = subprocess.run(['pactl', 'list', 'cards', 'short'], 
                                      capture_output=True, text=True, timeout=5)
                if card in result.stdout:
                    self.logger.info(f"Found Bluetooth card: {card}")
                    break
                else:
                    self.logger.info(f"Waiting for Bluetooth card to appear... (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(1)
            except Exception as e:
                self.logger.warning(f"Error checking for Bluetooth card: {e}")
                time.sleep(1)
        else:
            self.logger.warning("Bluetooth audio card not found after waiting")
            return False
        
        try:
            # Set profile to headset-head-unit
            subprocess.run(['pactl', 'set-card-profile', card, 'headset-head-unit'], 
                         check=True, timeout=10)
            self.logger.info(f"Set card profile to headset-head-unit for {card}")
            time.sleep(1)
            
            # Wait for source to appear
            for attempt in range(5):
                result = subprocess.run(['pactl', 'list', 'sources', 'short'], 
                                      capture_output=True, text=True, timeout=5)
                if source in result.stdout:
                    self.logger.info(f"Found Bluetooth source: {source}")
                    break
                else:
                    self.logger.info(f"Waiting for Bluetooth source to appear... (attempt {attempt + 1}/5)")
                    time.sleep(1)
            else:
                self.logger.warning("Bluetooth source not found")
                return False
            
            # Set as default source
            subprocess.run(['pactl', 'set-default-source', source], check=True, timeout=5)
            self.logger.info(f"Set default source to {source}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to set audio profile: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error setting audio profile: {e}")
            return False

    def connect(self):
        """Connect to Bluetooth handsfree device"""
        try:
            self.logger.info("Attempting to connect to Bluetooth device...")
            # Get paired devices
            paired_devices = self._get_paired_devices()
            if not paired_devices:
                self.logger.warning("No paired devices found")
                return False
            # Find handsfree device
            target_device = self._find_handsfree_device(paired_devices)
            if not target_device:
                self.logger.warning("No suitable handsfree device found")
                return False
            # Connect to device
            if self._connect_to_device(target_device):
                self.connected_device = target_device
                self.is_connected = True
                self.logger.info(f"Connected to {target_device['name']}")
                # Ensure audio profile and default source
                self.ensure_audio_profile()
                return True
            else:
                self.logger.error(f"Failed to connect to {target_device['name']}")
                return False
        except Exception as e:
            self.logger.error(f"Error during Bluetooth connection: {e}")
            return False
    
    def _get_paired_devices(self):
        """Get list of paired devices"""
        try:
            # Try using bluetoothctl with proper input
            process = subprocess.Popen(
                ['bluetoothctl'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send commands to bluetoothctl - use 'devices' instead of 'paired-devices'
            commands = "devices\nquit\n"
            stdout, stderr = process.communicate(input=commands, timeout=10)
            
            if process.returncode != 0:
                self.logger.error(f"bluetoothctl failed: {stderr}")
                return []
            
            devices = []
            for line in stdout.split('\n'):
                if line.strip() and 'Device' in line and not line.startswith('['):
                    # Parse device info (format: Device XX:XX:XX:XX:XX:XX DeviceName)
                    parts = line.split()
                    if len(parts) >= 2:
                        mac = parts[1]
                        name = ' '.join(parts[2:]) if len(parts) > 2 else 'Unknown'
                        devices.append({'mac': mac, 'name': name})
            
            self.logger.info(f"Found {len(devices)} devices")
            return devices
            
        except subprocess.TimeoutExpired:
            self.logger.error("bluetoothctl command timed out")
            return []
        except Exception as e:
            self.logger.error(f"Error getting paired devices: {e}")
            return []
    
    def _find_handsfree_device(self, devices):
        """Find suitable handsfree device from paired devices"""
        target_name = self.bluetooth_config.get('device_name', '').lower()
        
        for device in devices:
            device_name = device['name'].lower()
            
            # If specific device name is configured, look for exact match
            if target_name and target_name in device_name:
                self.logger.info(f"Found configured device: {device['name']}")
                return device
            
            # Look for common handsfree device names
            handsfree_keywords = [
                'headset', 'headphone', 'earphone', 'earphones',
                'bluetooth', 'wireless', 'hands-free', 'handsfree',
                'speaker', 'speakerphone', 'audio', 'sound'
            ]
            
            for keyword in handsfree_keywords:
                if keyword in device_name:
                    self.logger.info(f"Found handsfree device: {device['name']}")
                    return device
        
        # If no specific device found, return first available
        if devices:
            self.logger.info(f"Using first available device: {devices[0]['name']}")
            return devices[0]
        
        return None
    
    def _connect_to_device(self, device):
        """Connect to specific Bluetooth device"""
        try:
            mac = device['mac']
            
            # Use bluetoothctl with proper input
            process = subprocess.Popen(
                ['bluetoothctl'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send connect command
            commands = f"connect {mac}\nquit\n"
            stdout, stderr = process.communicate(input=commands, timeout=15)
            
            if process.returncode == 0:
                self.logger.info(f"Successfully connected to {device['name']}")
                return True
            else:
                self.logger.error(f"Failed to connect: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Connection attempt timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error connecting to device: {e}")
            return False
    
    def _monitor_connection(self):
        """Monitor Bluetooth connection status"""
        while self.running:
            try:
                if self.connected_device:
                    # Check if device is still connected
                    if not self._is_device_connected(self.connected_device['mac']):
                        self.logger.warning("Device disconnected")
                        self.is_connected = False
                        self.connected_device = None
                        
                        # Try to reconnect if auto-connect is enabled
                        if self.bluetooth_config.get('auto_connect', True):
                            self.logger.info("Attempting to reconnect...")
                            time.sleep(2)  # Wait before reconnection attempt
                            self.connect()
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in connection monitor: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _is_device_connected(self, mac):
        """Check if device is currently connected"""
        try:
            process = subprocess.Popen(
                ['bluetoothctl'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send info command
            commands = f"info {mac}\nquit\n"
            stdout, stderr = process.communicate(input=commands, timeout=5)
            
            if process.returncode == 0:
                return 'Connected: yes' in stdout
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking device connection: {e}")
            return False
    
    def is_connected(self):
        """Check if currently connected to a device"""
        return self.is_connected
    
    def get_connected_device(self):
        """Get information about currently connected device"""
        return self.connected_device
    
    def disconnect(self):
        """Disconnect from current device"""
        if self.connected_device:
            try:
                mac = self.connected_device['mac']
                subprocess.run(['bluetoothctl', 'disconnect', mac], 
                             capture_output=True, timeout=5)
                self.logger.info(f"Disconnected from {self.connected_device['name']}")
            except Exception as e:
                self.logger.error(f"Error disconnecting: {e}")
            finally:
                self.connected_device = None
                self.is_connected = False
    
    def shutdown(self):
        """Shutdown Bluetooth manager"""
        self.logger.info("Shutting down Bluetooth manager...")
        self.running = False
        
        if self.connection_thread and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=5)
        
        self.disconnect()
        self.logger.info("Bluetooth manager shutdown complete") 