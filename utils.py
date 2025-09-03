import hashlib
import os
import binascii


# Password hashing helpers (PBKDF2)
def hash_password(password: str) -> str:
	"""Return the password as-is (plaintext)."""
	return password




def verify_password(stored: str, incoming_password: str) -> bool:
	"""Verify by direct string comparison."""
	try:
		return stored == incoming_password
	except Exception:
		return False




# Theme colors
THEME = {
'bg': '#2f2f2f', # dark gray background
'panel': '#3b3b3b', # slightly lighter panels
'accent': '#8B0000', # dark red accent
'fg': '#f5f5f5', # foreground text
'muted': '#bfbfbf'
}