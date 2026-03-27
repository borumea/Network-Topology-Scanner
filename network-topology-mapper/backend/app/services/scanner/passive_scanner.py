import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Optional
import threading

logger = logging.getLogger(__name__)


def _device_id_from_ip(ip: str, mac: str = "") -> str:
    """Generate a deterministic device ID from IP (preferred) or MAC."""
    if ip:
        return f"device-{ip}"
    if mac:
        return f"device-{mac}"
    return str(uuid.uuid4())


class PassiveScanner:
    """Uses Scapy to passively sniff ARP, DNS, DHCP traffic."""

    def __init__(self):
        self._scapy = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
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

    def _resolve_interface(self, interface: str) -> str:
        """Resolve interface name. If empty, auto-detect the default via Scapy."""
        if interface:
            return interface
        try:
            from scapy.all import conf
            default = conf.iface
            logger.info("Auto-detected network interface: %s", default)
            return str(default) if default else "eth0"
        except Exception:
            return "eth0"

    def start(self, interface: str = "", callback: Callable = None):
        if not self._scapy:
            logger.warning("Scapy unavailable, cannot start passive scanner")
            return

        if self._running:
            logger.warning("Passive scanner already running")
            return

        interface = self._resolve_interface(interface)
        self._callback = callback
        self._running = True
        self._thread = threading.Thread(
            target=self._sniff_loop,
            args=(interface,),
            daemon=True,
        )
        self._thread.start()
        logger.info("Passive scanner started on %s", interface)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Passive scanner stopped")

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
            logger.error("Passive sniffing error: %s", e)
            self._running = False

    def _process_packet(self, pkt) -> Optional[dict]:
        from scapy.all import ARP, DNS, DHCP, IP

        try:
            if pkt.haslayer(ARP):
                if pkt[ARP].op == 2:  # ARP reply
                    return {
                        "id": _device_id_from_ip(pkt[ARP].psrc, pkt[ARP].hwsrc),
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
                        "id": _device_id_from_ip(pkt[IP].src, pkt.src if hasattr(pkt, 'src') else ""),
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
                        "id": _device_id_from_ip(pkt[IP].src if pkt.haslayer(IP) else "", pkt.src if hasattr(pkt, 'src') else ""),
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
