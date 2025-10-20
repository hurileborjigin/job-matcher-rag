"""Download embedding model manually."""
import os
import ssl
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

from sentence_transformers import SentenceTransformer

print("Downloading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model downloaded successfully!")
print(f"Model saved to: {model._model_card_vars['model_name']}")