"""Configuration for pytest."""
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

# Set test environment variables
os.environ['NEWS_API_KEY'] = 'test_key_for_testing'
os.environ['FORCE_CPU_IMAGE'] = 'true'
os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
