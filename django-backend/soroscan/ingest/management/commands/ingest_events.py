from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from stellar_sdk import SorobanServer
from soroscan.ingest.models import TrackedContract
from soroscan.ingest.tasks import validate_contract_payload_schema, validate_event_payload, _upsert_contract_event
from soroscan.ingest.stellar_client import SorobanClient

class Command(BaseCommand):
    help = "Ingest events for a given contract with optional dry run."

    def add_arguments(self, parser):
        parser.add_argument("--contract", required=True, help="Target tracked contract ID")
        parser.add_argument("--dry-run", action="store_true", help="Fetches and validates but does not persist")

    def handle(self, *args, **options):
        contract_id = options["contract"]
        dry_run = options["dry_run"]

        try:
            contract = TrackedContract.objects.get(contract_id=contract_id)
        except TrackedContract.DoesNotExist:
            raise CommandError(f"TrackedContract with ID {contract_id} does not exist.")

        server = SorobanServer(settings.SOROBAN_RPC_URL)
        filters = [{"type": "contract", "contractIds": [contract.contract_id]}]
        
        # fetch latest events
        kwargs = {"filters": filters, "pagination": {"limit": 100}}
        if contract.last_indexed_ledger and contract.last_indexed_ledger > 0:
            kwargs["start_ledger"] = contract.last_indexed_ledger

        self.stdout.write(f"Fetching events for {contract_id}...")
        try:
            events_response = server.get_events(**kwargs)
        except Exception as e:
            raise CommandError(f"Failed to fetch events: {e}")
        
        events = getattr(events_response, "events", [])
        
        self.stdout.write(self.style.SUCCESS(f"Fetched {len(events)} events."))

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] Summary of fetched events:"))
            self.stdout.write(f"Total events found: {len(events)}")
            if events:
                self.stdout.write("Sample events:")
                for idx, event in enumerate(events[:5]):
                    payload = getattr(event, "value", None) or getattr(event, "payload", {})
                    event_type = getattr(event, "type", "unknown")
                    ledger = getattr(event, "ledger", None)
                    
                    p1 = validate_contract_payload_schema(contract, payload, event_type, ledger=ledger)
                    p2, _ = validate_event_payload(contract, event_type, payload, ledger=ledger)
                    valid = p1 and p2
                    
                    status_str = "VALID" if valid else "INVALID"
                    self.stdout.write(f" - Event #{idx+1}: type='{event_type}', ledger={ledger}, status={status_str}")
                if len(events) > 5:
                    self.stdout.write(" ...")
            self.stdout.write(self.style.WARNING("Dry run complete. No data persisted."))
            return

        client = SorobanClient()
        batch_cache = {}
        processed = 0
        for fallback_idx, event in enumerate(events):
            _upsert_contract_event(
                contract, 
                event, 
                fallback_event_index=fallback_idx, 
                client=client, 
                batch_cache=batch_cache
            )
            processed += 1
            
        self.stdout.write(self.style.SUCCESS(f"Successfully processed {processed} events."))
