#!/usr/bin/env python3
"""
Password List Management
Updates passwords.txt with learning results and manages the password list
"""

import os
import json
from pathlib import Path


def load_passwords():
    """Load current passwords from passwords.txt"""
    passwords_file = "passwords.txt"
    if not os.path.exists(passwords_file):
        return []
    
    with open(passwords_file, 'r', encoding='utf-8') as f:
        passwords = [line.strip() for line in f if line.strip()]
    
    return passwords


def save_passwords(passwords):
    """Save passwords to passwords.txt"""
    with open("passwords.txt", 'w', encoding='utf-8') as f:
        for password in passwords:
            f.write(password + '\n')


def add_from_learning_results(results_file):
    """Add passwords from learning results file"""
    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        return False
    
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        current_passwords = load_passwords()
        new_passwords = results.get('suggested_additions', [])
        
        print(f"📝 Current passwords: {len(current_passwords)}")
        print(f"🆕 New suggestions: {len(new_passwords)}")
        
        # Add new passwords
        added_count = 0
        for password in new_passwords:
            if password not in current_passwords:
                current_passwords.append(password)
                added_count += 1
                print(f"   + {password}")
        
        if added_count > 0:
            save_passwords(current_passwords)
            print(f"\n✅ Added {added_count} new passwords to passwords.txt")
        else:
            print("\nℹ️  No new passwords to add")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing results file: {e}")
        return False


def show_current_passwords():
    """Show current password list"""
    passwords = load_passwords()
    print(f"📋 Current passwords ({len(passwords)}):")
    for i, password in enumerate(passwords, 1):
        print(f"   {i}. {password}")


def remove_password(password):
    """Remove a password from the list"""
    passwords = load_passwords()
    if password in passwords:
        passwords.remove(password)
        save_passwords(passwords)
        print(f"✅ Removed: {password}")
    else:
        print(f"❌ Password not found: {password}")


def main():
    """Main password management function"""
    print("🔐 PASSWORD LIST MANAGEMENT")
    print("=" * 40)
    
    while True:
        print("\nSelect action:")
        print("1. Show current passwords")
        print("2. Add from learning results")
        print("3. Remove password")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            show_current_passwords()
        
        elif choice == '2':
            results_file = input("Enter learning results file name: ").strip()
            if results_file:
                add_from_learning_results(results_file)
        
        elif choice == '3':
            password = input("Enter password to remove: ").strip()
            if password:
                remove_password(password)
        
        elif choice == '4':
            print("👋 Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1-4.")


if __name__ == "__main__":
    main() 