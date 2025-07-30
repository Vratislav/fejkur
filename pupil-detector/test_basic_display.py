#!/usr/bin/env python3

import os
import time

# Clear SSH forwarding
os.environ.pop('DISPLAY', None)
os.environ.pop('SSH_CLIENT', None)

def test_pygame_display():
    """Test display with pygame"""
    print("=== Testing Pygame Display ===")
    try:
        import pygame
        
        # Initialize pygame
        pygame.init()
        
        # Set display mode
        screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption("Pi Display Test")
        
        # Fill screen with colors
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
        
        print("Pygame display started. You should see colored squares on the Pi's display...")
        
        for i, color in enumerate(colors):
            screen.fill(color)
            pygame.display.flip()
            print(f"Showing {['Red', 'Green', 'Blue', 'Yellow', 'Magenta'][i]} screen...")
            time.sleep(2)
        
        pygame.quit()
        print("Pygame test completed")
        return True
        
    except ImportError:
        print("Pygame not installed. Try: sudo apt install python3-pygame")
        return False
    except Exception as e:
        print(f"Pygame test failed: {e}")
        return False

def test_framebuffer_direct():
    """Test direct framebuffer access"""
    print("\n=== Testing Direct Framebuffer ===")
    try:
        # Try to write directly to framebuffer
        with open('/dev/fb0', 'wb') as fb:
            # Create a simple pattern - red screen
            # Assuming 32-bit color (RGBA), 640x480
            width, height = 640, 480
            red_pixel = b'\x00\x00\xFF\xFF'  # BGRA format
            
            print("Writing red pattern to framebuffer...")
            for y in range(height):
                for x in range(width):
                    fb.write(red_pixel)
            fb.flush()
        
        print("Red screen written to framebuffer. Check Pi's display...")
        time.sleep(3)
        
        # Clear to black
        with open('/dev/fb0', 'wb') as fb:
            black_pixel = b'\x00\x00\x00\x00'
            print("Clearing to black...")
            for y in range(height):
                for x in range(width):
                    fb.write(black_pixel)
            fb.flush()
        
        print("Framebuffer test completed")
        return True
        
    except PermissionError:
        print("Permission denied. Try running with sudo or add user to video group")
        return False
    except Exception as e:
        print(f"Framebuffer test failed: {e}")
        return False

def test_simple_command():
    """Test simple display command"""
    print("\n=== Testing Simple Display Commands ===")
    
    # Test if we can run a simple graphical application
    commands_to_try = [
        "xeyes",  # Simple X11 app
        "xclock", # Another simple X11 app  
        "feh --bg-center /usr/share/pixmaps/debian-logo.png",  # Image viewer
    ]
    
    for cmd in commands_to_try:
        print(f"Trying: {cmd}")
        try:
            import subprocess
            result = subprocess.run(cmd.split(), timeout=5, capture_output=True)
            if result.returncode == 0:
                print(f"✓ {cmd} worked")
                return True
            else:
                print(f"✗ {cmd} failed: {result.stderr.decode()}")
        except subprocess.TimeoutExpired:
            print(f"✓ {cmd} started (timed out, which is expected)")
            return True
        except Exception as e:
            print(f"✗ {cmd} error: {e}")
    
    return False

def main():
    print("Basic Display Test")
    print("=" * 30)
    
    # Test different display methods
    working_methods = []
    
    if test_pygame_display():
        working_methods.append("pygame")
    
    if test_framebuffer_direct():
        working_methods.append("framebuffer")
    
    if test_simple_command():
        working_methods.append("x11_apps")
    
    print(f"\n=== Results ===")
    if working_methods:
        print(f"Working display methods: {working_methods}")
    else:
        print("No display methods worked!")
        print("\nTroubleshooting suggestions:")
        print("1. Check if you're physically at the Pi (not via SSH)")
        print("2. Make sure HDMI cable is connected")
        print("3. Check if display is on the correct input")
        print("4. Try: sudo systemctl restart lightdm")

if __name__ == "__main__":
    main() 