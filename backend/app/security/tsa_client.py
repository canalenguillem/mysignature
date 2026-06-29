"""Cliente RFC 3161 para sellado de tiempo (TSA cualificada eIDAS).

Construye un TimeStampReq, lo envía a la TSA y parsea el TimeStampToken
extrayendo el `genTime`. Referencia: docs/BACKEND_SPEC.md §app/security/tsa_client.py
            RFC 3161 · docs/ARCHITECTURE.md §Integraciones (CaixaBank tst.lacaixa.es)
"""
from __future__ import annotations

import base64
import secrets

import httpx
from asn1crypto import algos, core, tsp

from app.utils.errors import TSAUnavailableError
from app.utils.logger import logger

_GRANTED = ("granted", "granted_with_mods")


class TSAClient:
    def __init__(self, tsa_url: str, timeout: int = 30):
        self.tsa_url = tsa_url
        self.timeout = timeout

    async def get_timestamp(self, data_hash: bytes) -> dict:
        """Solicita un sello de tiempo para `data_hash` (SHA-256 de los datos)."""
        request_der = self._create_timestamp_request(data_hash)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.tsa_url,
                    content=request_der,
                    headers={"Content-Type": "application/timestamp-query"},
                )
        except httpx.HTTPError as exc:
            logger.error("TSA inaccesible (%s): %s", self.tsa_url, exc)
            raise TSAUnavailableError(f"TSA unavailable: {exc}") from exc

        if response.status_code != 200:
            raise TSAUnavailableError(f"TSA returned {response.status_code}")

        return self._parse_timestamp_response(response.content)

    def _create_timestamp_request(self, data_hash: bytes) -> bytes:
        """Construye un TimeStampReq RFC 3161 (SHA-256, nonce, certReq=True)."""
        request = tsp.TimeStampReq(
            {
                "version": "v1",
                "message_imprint": tsp.MessageImprint(
                    {
                        "hash_algorithm": algos.DigestAlgorithm({"algorithm": "sha256"}),
                        "hashed_message": data_hash,
                    }
                ),
                "nonce": core.Integer(
                    int.from_bytes(secrets.token_bytes(8), "big")
                ),
                "cert_req": True,
            }
        )
        return request.dump()

    def _parse_timestamp_response(self, content: bytes) -> dict:
        """Valida el status y extrae genTime del TimeStampToken."""
        try:
            resp = tsp.TimeStampResp.load(content)
            status = resp["status"]["status"].native
            if status not in _GRANTED:
                raise TSAUnavailableError(f"TSA rejected request (status={status})")

            token = resp["time_stamp_token"]
            econtent = token["content"]["encap_content_info"]["content"]
            tst_info = tsp.TSTInfo.load(econtent.native)
            gen_time = tst_info["gen_time"].native
        except TSAUnavailableError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("No se pudo parsear la respuesta TSA: %s", exc)
            raise TSAUnavailableError("Invalid TSA response") from exc

        return {
            "timestamp": gen_time,
            "tst_base64": base64.b64encode(content).decode(),
            "tst_der": content,
            "tsa_url": self.tsa_url,
        }
