"""Verificación criptográfica de firmas digitales.

Referencia: docs/BACKEND_SPEC.md §app/security/signature_validation.py
            docs/ARCHITECTURE.md (RSA-PSS mínimo RSA-2048, SHA-256)
"""
from __future__ import annotations

import base64
import hashlib

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from app.utils.logger import logger

_HASHES = {
    "SHA-256": hashes.SHA256,
    "SHA256": hashes.SHA256,
    "SHA-384": hashes.SHA384,
    "SHA-512": hashes.SHA512,
}

# Algoritmos RSA con relleno PKCS#1 v1.5 (el resto se trata como PSS).
_PKCS1V15 = {"RSA-PKCS1", "RSASSA-PKCS1-V1_5", "SHA256WITHRSA", "RS256"}


def _hash_algo(name: str):
    return _HASHES.get((name or "SHA-256").upper(), hashes.SHA256)()


class SignatureValidator:
    @staticmethod
    def verify_signature(
        pdf_bytes: bytes,
        signature_base64: str,
        certificate_pem: str,
        hash_algorithm: str = "SHA-256",
        signature_algorithm: str = "RSA-PSS",
    ) -> bool:
        """Verifica que `signature` sobre `hash(pdf_bytes)` es válida para el cert."""
        try:
            signature_bytes = base64.b64decode(signature_base64)
            cert = x509.load_pem_x509_certificate(certificate_pem.encode())
            public_key = cert.public_key()

            algo = _hash_algo(hash_algorithm)
            digest = hashes.Hash(algo)
            digest.update(pdf_bytes)
            pdf_hash = digest.finalize()

            if isinstance(public_key, RSAPublicKey):
                if (signature_algorithm or "").upper() in _PKCS1V15:
                    public_key.verify(
                        signature_bytes, pdf_hash, padding.PKCS1v15(),
                        _prehashed(algo),
                    )
                else:
                    public_key.verify(
                        signature_bytes,
                        pdf_hash,
                        padding.PSS(
                            mgf=padding.MGF1(algo),
                            salt_length=padding.PSS.MAX_LENGTH,
                        ),
                        _prehashed(algo),
                    )
            elif isinstance(public_key, EllipticCurvePublicKey):
                public_key.verify(signature_bytes, pdf_hash, ec.ECDSA(_prehashed(algo)))
            else:
                logger.error("Tipo de clave pública no soportado: %s", type(public_key))
                return False

            return True
        except InvalidSignature:
            logger.warning("Firma inválida (no coincide con el certificado)")
            return False
        except Exception as exc:  # noqa: BLE001
            logger.error("Error verificando firma: %s", exc)
            return False

    @staticmethod
    def calculate_hash(signature_base64: str) -> str:
        """SHA-256 hex de los bytes de la firma (para `signatures.signature_hash`)."""
        return hashlib.sha256(base64.b64decode(signature_base64)).hexdigest()


def _prehashed(algo):
    """Permite verificar pasando el digest ya calculado (Prehashed)."""
    from cryptography.hazmat.primitives.asymmetric.utils import Prehashed

    return Prehashed(algo)
