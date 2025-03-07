import base64
import logging

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

logger = logging.getLogger(__name__)


def verify_signature(request, public_key_pem):
    """Verify HTTP Signatures according to ActivityPub spec."""
    signature_header = request.headers.get("Signature")
    if not signature_header:
        return False

    # Parse signature header
    sig_parts = dict(part.split("=", 1) for part in signature_header.split(","))
    headers_to_sign = sig_parts.get("headers", "").split()
    signature = base64.b64decode(sig_parts.get("signature", "").strip('"'))

    # Build string to verify
    lines = []
    for header in headers_to_sign:
        if header == "(request-target)":
            lines.append(f"(request-target): post {request.path}")
        else:
            lines.append(f"{header}: {request.headers[header]}")
    signing_string = "\n".join(lines)

    # Verify signature
    try:
        public_key = load_pem_public_key(public_key_pem.encode())
        public_key.verify(
            signature, signing_string.encode(), padding.PKCS1v15(), hashes.SHA256()
        )
        return True
    except Exception:
        return False


def fetch_actor_profile(actor_url):
    """Fetch an ActivityPub actor's profile from their URL."""
    try:
        response = requests.get(
            actor_url, headers={"Accept": "application/activity+json"}
        )
        return response.json() if response.ok else None
    except requests.RequestException:
        return None
