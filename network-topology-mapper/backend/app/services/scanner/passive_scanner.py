import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Iterable, Optional, Union
import threading

logger = logging.getLogger(__name__)


class PassiveScanner:
    """Uses Scapy to passively sniff ARP, DNS, DHCP traffic.

    Runs one sniffer thread per interface so multi-homed hosts (e.g. VMs
    straddling several Docker networks) capture traffic on every leg, not
    just the default-route interface.
    """

    def __init__(self):
        self._scapy = None
        self._running = False
        self._threads: list[threading.Thread] = []
        self._callback: Optional[Callable] = None
        try:
            from scapy.all import sniff, ARP, DNS, DHCP
            self._scapy = True
        except ImportError:
            logger.warning("Scapy not installed. Passive scanning unavailable.")

    @property
    def available(self) -> bool:
        return self._scapy is not None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(
        self,
        interface: Union[str, Iterable[str], None] = None,
        callback: Callable = None,
    ):
        """
        Start passive scanning on one or more interfaces.

        Args:
            interface: Interface name, iterable of names, or None. When
                None, the configured SCAN_PASSIVE_INTERFACE (comma-separated
                list allowed) is used; if that's empty, all UP non-loopback
                interfaces are sniffed.
            callback: Function called for each discovered device.
        """
        if not self._scapy:
            logger.warning("Scapy unavailable, cannot start passive scanner")
            return

        if self._running:
            logger.warning("Passive scanner already running")
            return

        interfaces = self._resolve_interfaces(interface)
        if not interfaces:
            logger.warning("Passive scanner has no interfaces to sniff — skipping")
            return

        self._callback = callback
        self._running = True
        self._threads = []
        for iface in interfaces:
            t = threading.Thread(
                target=self._sniff_loop,
                args=(iface,),
                daemon=True,
                name=f"passive-sniffer-{iface}",
            )
            t.start()
            self._threads.append(t)
        logger.info("Passive scanner started on %d interface(s): %s",
                    len(interfaces), ", ".join(interfaces))

    def stop(self):
        self._running = False
        for t in self._threads:
            t.join(timeout=5)
        self._threads = []
        logger.info("Passive scanner stopped")

    def _resolve_interfaces(
        self, interface: Union[str, Iterable[str], None]
    ) -> list[str]:
        """Normalize the argument into a concrete list of interface names."""
        if interface is None:
            from app.config import get_settings
            return get_settings().get_passive_interfaces()
        if isinstance(interface, str):
            # Allow comma-separated strings to pass through directly.
            return [s.strip() for s in interface.split(",") if s.strip()]
        return [s for s in interface if s]

    def _sniff_loop(self, interface: str):
        from scapy.all import sniff

        def packet_handler(pkt):
            if not self._running:
                return
            device = self._process_packet(pkt)
            if device and self._callback:
                self._callback(device)

        try:
            sniff(
                iface=interface,
                prn=packet_handler,
                filter="arp or port 53 or port 67 or port 68",
                store=False,
                stop_filter=lambda _: not self._running,
            )
        except Exception as e:
            logger.error("Passive sniffing error on %s: %s", interface, e)

    def _process_packet(self, pkt) -> Optional[dict]:
        from scapy.all import ARP, DNS, DHCP, IP

        try:
            if pkt.haslayer(ARP):
                if pkt[ARP].op == 2:  # ARP reply
                    return {
                        "id": str(uuid.uuid4()),
                        "ip": pkt[ARP].psrc,
                        "mac": pkt[ARP].hwsrc,
                        "hostname": "",
                        "device_type": "unknown",
                        "discovery_method": "passive",
                        "first_seen": datetime.utcnow().isoformat(),
                        "last_seen": datetime.utcnow().isoformat(),
                        "status": "online",
                    }

            if pkt.haslayer(DNS) and pkt.haslayer(IP):
                if pkt[DNS].qr == 1:  # DNS response
                    return {
                        "id": str(uuid.uuid4()),
                        "ip": pkt[IP].src,
                        "mac": pkt.src if hasattr(pkt, 'src') else "",
                        "hostname": "",
                        "device_type": "server",
                        "discovery_method": "passive",
                        "services": ["dns"],
                        "open_ports": [53],
                        "first_seen": datetime.utcnow().isoformat(),
                        "last_seen": datetime.utcnow().isoformat(),
                        "status": "online",
                    }

            if pkt.haslayer(DHCP):
                options = {opt[0]: opt[1] for opt in pkt[DHCP].options if isinstance(opt, tuple)}
                if options.get("message-type") == 2:  # DHCP offer
                    return {
                        "id": str(uuid.uuid4()),
                        "ip": pkt[IP].src if pkt.haslayer(IP) else "",
                        "mac": pkt.src if hasattr(pkt, 'src') else "",
                        "hostname": "",
                        "device_type": "server",
                        "discovery_method": "passive",
                        "services": ["dhcp"],
                        "open_ports": [67],
                        "first_seen": datetime.utcnow().isoformat(),
                        "last_seen": datetime.utcnow().isoformat(),
                        "status": "online",
                    }
        except Exception as e:
            logger.debug("Error processing packet: %s", e)

        return None


passive_scanner = PassiveScanner()
