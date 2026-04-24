"""
Tests for decoded event payload caching (Task 1).

Covers:
- Cache miss falls back to decode and stores result
- Cache hit returns cached value without re-decoding
- TTL is set to 24 hours
- Cache is invalidated on event update
"""
import pytest
from unittest.mock import patch
from django.core.cache import cache
from django.test import TestCase

from soroscan.ingest.cache_utils import (
    DECODED_PAYLOAD_TTL,
    decoded_payload_cache_key,
    get_cached_decoded_payload,
    set_cached_decoded_payload,
    invalidate_decoded_payload_cache,
    _SENTINEL,
)
from .factories import TrackedContractFactory, UserFactory, ContractABIFactory


class DecodedPayloadCacheKeyTest(TestCase):
    def test_key_format(self):
        key = decoded_payload_cache_key(42)
        self.assertEqual(key, "soroscan:decoded:42")

    def test_ttl_is_24_hours(self):
        self.assertEqual(DECODED_PAYLOAD_TTL, 86_400)


class DecodedPayloadCacheTest(TestCase):
    def setUp(self):
        cache.clear()

    def test_get_returns_sentinel_on_miss(self):
        result = get_cached_decoded_payload(9999)
        self.assertIs(result, _SENTINEL)

    def test_set_and_get_roundtrip(self):
        payload = {"amount": 100, "from": "GABC"}
        set_cached_decoded_payload(1, payload)
        result = get_cached_decoded_payload(1)
        self.assertEqual(result, payload)

    def test_set_stores_with_correct_ttl(self):
        with patch("soroscan.ingest.cache_utils.cache") as mock_cache:
            mock_cache.get.return_value = _SENTINEL
            set_cached_decoded_payload(5, {"x": 1})
            mock_cache.set.assert_called_once_with(
                "soroscan:decoded:5", {"x": 1}, timeout=86_400
            )

    def test_invalidate_removes_cached_value(self):
        set_cached_decoded_payload(2, {"val": 42})
        invalidate_decoded_payload_cache(2)
        result = get_cached_decoded_payload(2)
        self.assertIs(result, _SENTINEL)

    def test_none_payload_is_not_cached_as_sentinel(self):
        """Storing None is distinct from a cache miss."""
        set_cached_decoded_payload(3, None)
        result = get_cached_decoded_payload(3)
        # None stored explicitly should come back as None, not _SENTINEL
        self.assertIsNone(result)


@pytest.mark.django_db
class TryDecodeEventCacheIntegrationTest(TestCase):
    """_try_decode_event should use and populate the decoded payload cache."""

    def setUp(self):
        cache.clear()

    def test_cache_populated_after_successful_decode(self):
        from stellar_sdk import xdr as stellar_xdr
        from soroscan.ingest.tasks import _upsert_contract_event

        user = UserFactory()
        contract = TrackedContractFactory(owner=user)
        ContractABIFactory(
            contract=contract,
            abi_json=[{"name": "transfer", "fields": [{"name": "amount", "type": "I32"}]}],
        )

        sc_val = stellar_xdr.SCVal(
            type=stellar_xdr.SCValType.SCV_I32,
            i32=stellar_xdr.Int32(77),
        )
        obj, created = _upsert_contract_event(
            contract,
            {
                "ledger": 5000,
                "event_index": 0,
                "tx_hash": "cache_test_hash",
                "type": "transfer",
                "value": {},
                "timestamp": None,
                "xdr": sc_val.to_xdr(),
            },
        )
        self.assertTrue(created)
        obj.refresh_from_db()
        self.assertEqual(obj.decoding_status, "success")

        # Cache should now hold the decoded payload
        cached = get_cached_decoded_payload(obj.pk)
        self.assertIsNot(cached, _SENTINEL)
        self.assertEqual(cached["amount"], 77)

    def test_cache_hit_skips_decode(self):
        """When cache already has a decoded payload, decode_event_payload is not called."""
        from soroscan.ingest.tasks import _try_decode_event
        from soroscan.ingest.models import ContractEvent
        from soroscan.ingest.cache_utils import set_cached_decoded_payload

        user = UserFactory()
        contract = TrackedContractFactory(owner=user)
        ContractABIFactory(contract=contract)

        # Pre-populate cache
        fake_payload = {"amount": 999}
        from django.utils import timezone
        event = ContractEvent.objects.create(
            contract=contract,
            event_type="transfer",
            payload={},
            payload_hash="a" * 64,
            ledger=6000,
            event_index=0,
            timestamp=timezone.now(),
            tx_hash="b" * 64,
        )
        set_cached_decoded_payload(event.pk, fake_payload)

        # decode_event_payload lives in soroscan.ingest.decoder and is imported
        # locally inside _try_decode_event, so patch it at the source module.
        with patch("soroscan.ingest.decoder.decode_event_payload") as mock_decode:
            _try_decode_event(event, contract, "transfer", "some_xdr")
            mock_decode.assert_not_called()

        event.refresh_from_db()
        self.assertEqual(event.decoded_payload, fake_payload)
        self.assertEqual(event.decoding_status, "success")

    def test_cache_invalidated_on_event_update(self):
        """Re-ingesting an existing event (update) should invalidate the cache."""
        from stellar_sdk import xdr as stellar_xdr
        from soroscan.ingest.tasks import _upsert_contract_event
        from soroscan.ingest.cache_utils import set_cached_decoded_payload

        user = UserFactory()
        contract = TrackedContractFactory(owner=user)

        sc_val = stellar_xdr.SCVal(
            type=stellar_xdr.SCValType.SCV_I32,
            i32=stellar_xdr.Int32(1),
        )
        event_data = {
            "ledger": 7000,
            "event_index": 0,
            "tx_hash": "update_test_hash",
            "type": "transfer",
            "value": {},
            "timestamp": None,
            "xdr": sc_val.to_xdr(),
        }

        # First ingest — creates the event
        obj, created = _upsert_contract_event(contract, event_data)
        self.assertTrue(created)

        # Manually populate cache to simulate a prior cache hit
        set_cached_decoded_payload(obj.pk, {"amount": 1})
        cached_before = get_cached_decoded_payload(obj.pk)
        self.assertIsNot(cached_before, _SENTINEL)

        # Second ingest of same ledger+index — triggers update path
        _upsert_contract_event(contract, event_data)

        # Cache should be invalidated
        cached_after = get_cached_decoded_payload(obj.pk)
        self.assertIs(cached_after, _SENTINEL)
