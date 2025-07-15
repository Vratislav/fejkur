"""
MQTT Client for Voice Recognition Door Opener
Handles communication with smart home system
"""

import json
import time
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any
import paho.mqtt.client as mqtt


class MQTTClient:
    """Manages MQTT communication for door unlocking"""
    
    def __init__(self, config):
        """Initialize MQTT client"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.mqtt_config = config.get_mqtt_config()
        
        self.client = None
        self.connected = False
        self.connection_thread = None
        self.running = False
        
        # Connection settings
        self.broker = self.mqtt_config.get('broker', 'localhost')
        self.port = self.mqtt_config.get('port', 1883)
        self.username = self.mqtt_config.get('username', '')
        self.password = self.mqtt_config.get('password', '')
        self.topic = self.mqtt_config.get('topic', 'home/door/unlock')
        self.client_id = self.mqtt_config.get('client_id', 'voice-recognizer')
        self.keepalive = self.mqtt_config.get('keepalive', 60)
        self.qos = self.mqtt_config.get('qos', 1)
        
        # Message tracking
        self.last_message_time = 0
        self.message_count = 0
    
    def initialize(self):
        """Initialize MQTT client"""
        try:
            self.logger.info("Initializing MQTT client...")
            
            # Create MQTT client
            self.client = mqtt.Client(
                client_id=self.client_id,
                clean_session=True,
                protocol=mqtt.MQTTv311
            )
            
            # Set up callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            self.client.on_message = self._on_message
            
            # Set authentication if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Start connection thread
            self.running = True
            self.connection_thread = threading.Thread(target=self._connection_loop, daemon=True)
            self.connection_thread.start()
            
            self.logger.info("MQTT client initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MQTT client: {e}")
            return False
    
    def _connection_loop(self):
        """Main connection loop"""
        while self.running:
            try:
                if not self.connected:
                    self.logger.info(f"Connecting to MQTT broker: {self.broker}:{self.port}")
                    
                    # Connect to broker
                    self.client.connect(self.broker, self.port, self.keepalive)
                    
                    # Start network loop
                    self.client.loop_start()
                    
                    # Wait for connection
                    timeout = 10
                    while not self.connected and timeout > 0:
                        time.sleep(0.1)
                        timeout -= 0.1
                    
                    if not self.connected:
                        self.logger.error("Failed to connect to MQTT broker")
                        self.client.loop_stop()
                        time.sleep(5)  # Wait before retry
                        continue
                
                # Keep connection alive
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in MQTT connection loop: {e}")
                self.connected = False
                time.sleep(5)  # Wait before retry
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection events"""
        if rc == 0:
            self.connected = True
            self.logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to relevant topics
            self._subscribe_to_topics()
        else:
            self.connected = False
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
            self.logger.error(f"Failed to connect to MQTT broker: {error_msg}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection events"""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection (code: {rc})")
        else:
            self.logger.info("MQTT client disconnected")
    
    def _on_publish(self, client, userdata, mid):
        """Handle MQTT publish events"""
        self.logger.debug(f"Message published successfully (mid: {mid})")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            self.logger.debug(f"Received message on topic {msg.topic}: {msg.payload.decode()}")
            
            # Parse message
            payload = json.loads(msg.payload.decode())
            
            # Handle different message types
            if msg.topic == f"{self.topic}/status":
                self._handle_status_message(payload)
            elif msg.topic == f"{self.topic}/response":
                self._handle_response_message(payload)
                
        except json.JSONDecodeError:
            self.logger.warning(f"Invalid JSON in MQTT message: {msg.payload}")
        except Exception as e:
            self.logger.error(f"Error handling MQTT message: {e}")
    
    def _subscribe_to_topics(self):
        """Subscribe to relevant MQTT topics"""
        try:
            # Subscribe to status and response topics
            topics = [
                (f"{self.topic}/status", self.qos),
                (f"{self.topic}/response", self.qos)
            ]
            
            result, mid = self.client.subscribe(topics)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info("Subscribed to MQTT topics")
            else:
                self.logger.error("Failed to subscribe to MQTT topics")
                
        except Exception as e:
            self.logger.error(f"Error subscribing to topics: {e}")
    
    def _handle_status_message(self, payload):
        """Handle status messages from smart home system"""
        try:
            status = payload.get('status', 'unknown')
            timestamp = payload.get('timestamp', '')
            
            self.logger.info(f"Door status: {status} (timestamp: {timestamp})")
            
        except Exception as e:
            self.logger.error(f"Error handling status message: {e}")
    
    def _handle_response_message(self, payload):
        """Handle response messages from smart home system"""
        try:
            success = payload.get('success', False)
            message = payload.get('message', '')
            timestamp = payload.get('timestamp', '')
            
            if success:
                self.logger.info(f"Door unlock successful: {message}")
            else:
                self.logger.warning(f"Door unlock failed: {message}")
                
        except Exception as e:
            self.logger.error(f"Error handling response message: {e}")
    
    def send_unlock_message(self) -> bool:
        """Send door unlock message to MQTT broker"""
        try:
            if not self.connected:
                self.logger.error("MQTT client not connected")
                return False
            
            # Create unlock message
            message = "success"
            
            # Convert to JSON
            payload = json.dumps(message)
            
            # Publish message
            result, mid = self.client.publish(
                topic=self.topic,
                payload=payload,
                qos=self.qos,
                retain=False
            )
            
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.last_message_time = time.time()
                self.message_count += 1
                self.logger.info(f"Unlock message sent successfully (mid: {mid})")
                return True
            else:
                self.logger.error(f"Failed to send unlock message (result: {result})")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending unlock message: {e}")
            return False
    
    def send_status_request(self) -> bool:
        """Send status request message"""
        try:
            if not self.connected:
                return False
            
            message = {
                'action': 'status_request',
                'timestamp': datetime.now().isoformat(),
                'source': 'voice-recognizer'
            }
            
            payload = json.dumps(message)
            result, mid = self.client.publish(
                topic=f"{self.topic}/request",
                payload=payload,
                qos=self.qos,
                retain=False
            )
            
            return result == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            self.logger.error(f"Error sending status request: {e}")
            return False
    
    def is_connected(self):
        """Check if MQTT client is connected"""
        return self.connected
    
    def get_connection_info(self):
        """Get MQTT connection information"""
        return {
            'broker': self.broker,
            'port': self.port,
            'connected': self.connected,
            'client_id': self.client_id,
            'topic': self.topic,
            'message_count': self.message_count,
            'last_message_time': self.last_message_time
        }
    
    def test_connection(self) -> bool:
        """Test MQTT connection"""
        try:
            if not self.connected:
                self.logger.warning("MQTT client not connected")
                return False
            
            # Send test message
            test_message = {
                'action': 'test',
                'timestamp': datetime.now().isoformat(),
                'source': 'voice-recognizer'
            }
            
            payload = json.dumps(test_message)
            result, mid = self.client.publish(
                topic=f"{self.topic}/test",
                payload=payload,
                qos=0,  # Use QoS 0 for test messages
                retain=False
            )
            
            success = result == mqtt.MQTT_ERR_SUCCESS
            if success:
                self.logger.info("MQTT connection test successful")
            else:
                self.logger.error("MQTT connection test failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error testing MQTT connection: {e}")
            return False
    
    def shutdown(self):
        """Shutdown MQTT client"""
        self.logger.info("Shutting down MQTT client...")
        self.running = False
        
        try:
            if self.client:
                if self.connected:
                    self.client.disconnect()
                self.client.loop_stop()
                
        except Exception as e:
            self.logger.error(f"Error during MQTT shutdown: {e}")
        
        self.logger.info("MQTT client shutdown complete") 