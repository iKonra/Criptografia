def caesar(text, shift, action):
    return ''.join([chr((ord(c) + (shift if action == '1' else -shift)) % 128) for c in text])

def main():
    # Get action choice
    action = input("Encrypt (1) or Decrypt (2)? ").lower()
    while action not in ['1', '2']:
        action = input("Invalid option. Encrypt (1) or Decrypt (2)? ").lower()
    
    # Get shift value with default fallback
    shift_input = input("Shift value [default=3]: ")
    try:
        shift = int(shift_input) if shift_input else 3
    except ValueError:
        shift = 3  # Default if input isn't a number
    
    # Process message
    message = input("Message: ")
    result = caesar(message, shift, action)
    print(f"\nResult: {result}")

if __name__ == "__main__":
    main()