import ipaddress
import requests

_cache: dict[str, dict] = {}

_BATCH_URL = "http://ip-api.com/batch"
_BATCH_SIZE = 100


def _is_public(ip: str) -> bool:
    try:
        obj = ipaddress.ip_address(ip)
        return not (obj.is_private or obj.is_loopback or obj.is_unspecified or obj.is_reserved or obj.is_multicast)
    except ValueError:
        return False


def geolocate_ips(ips: list[str]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    to_fetch: list[str] = []

    for ip in ips:
        if not _is_public(ip):
            continue
        if ip in _cache:
            result[ip] = _cache[ip]
        else:
            to_fetch.append(ip)

    for i in range(0, len(to_fetch), _BATCH_SIZE):
        batch = to_fetch[i : i + _BATCH_SIZE]
        payload = [{"query": ip} for ip in batch]
        try:
            resp = requests.post(_BATCH_URL, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for entry in data:
                ip = entry.get("query", "")
                if entry.get("status") == "success":
                    geo = {
                        "lat": entry.get("lat"),
                        "lon": entry.get("lon"),
                        "country": entry.get("countryCode", ""),
                        "city": entry.get("city", ""),
                    }
                    _cache[ip] = geo
                    result[ip] = geo
        except Exception:
            pass

    return result
