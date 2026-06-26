"""Встроенный движок SpiderFoot внутри Traceon.

SpiderFoot (233 модуля сбора OSINT) вендорится в образ Traceon и запускается
in-process через его CLI (sf.py -o json) как subprocess. События скана
маппятся в типы сущностей Traceon и добавляются в граф расследования.
Внешний HTTP-сервис SpiderFoot не требуется — весь функционал внутри Traceon.
"""
import json
import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

# Путь к вендоренному SpiderFoot внутри образа
SPIDERFOOT_HOME = os.environ.get("SPIDERFOOT_HOME", "/app/flowsint-api/spiderfoot")

# Пресеты модулей под сценарии.
# fast — быстрый набор без брутфорса/медленных внешних фидов (для синхронного API).
# passive — расширенный пассивный сбор (дольше, для фоновых сканов).
PRESETS = {
    "fast": [
        "sfp_dnsresolve", "sfp_whois", "sfp_sslcert", "sfp_ssltools",
        "sfp_iptoasn", "sfp_dnsraw", "sfp_dnstext",
    ],
    "passive": [
        "sfp_dnsresolve", "sfp_whois", "sfp_sslcert", "sfp_ssltools",
        "sfp_iptoasn", "sfp_dnsraw", "sfp_dnstext", "sfp_crt",
        "sfp_ripe", "sfp_arin", "sfp_email", "sfp_names", "sfp_company",
        "sfp_socialprofiles", "sfp_ipinfo", "sfp_phone", "sfp_subdomain_takeover",
    ],
}

# Маппинг человекочитаемых типов событий SpiderFoot -> типы сущностей Traceon
# (sf.py -o json выводит "type" как имя, напр. "Internet Name", "IP Address")
SF_TYPE_MAP = {
    "Internet Name": "domain", "Domain Name": "domain",
    "Affiliate - Domain Name": "domain", "Co-Hosted Site": "domain",
    "Similar Domain": "domain", "Internet Name - Unresolved": "domain",
    "IP Address": "ip", "IPv6 Address": "ip", "Affiliate - IP Address": "ip",
    "Email Address": "email", "Email Address - Generic": "email",
    "Affiliate - Email Address": "email",
    "Phone Number": "phone",
    "Username": "username", "Account on External Site": "socialaccount",
    "Human Name": "individual",
    "Company Name": "organization", "Affiliate - Company Name": "organization",
    "Netblock Ownership": "cidr", "Netblock Membership": "cidr",
    "BGP AS Ownership": "asn", "BGP AS Membership": "asn",
    "Linked URL - Internal": "website", "Linked URL - External": "website",
    "URL (Static)": "website", "Hosting Provider": "website",
    "Open TCP Port": "port",
    "DNS TXT Record": "dnsrecord", "DNS SPF Record": "dnsrecord",
    "SSL Certificate - Issued to": "sslcertificate",
    "SSL Certificate - Raw Data": "sslcertificate",
    "Web Technology": "webtracker", "Web Analytics": "webtracker",
    "Bitcoin Address": "cryptowallet", "Ethereum Address": "cryptowallet",
    "Physical Address": "location", "Physical Coordinates": "location",
    "Physical Location": "location",
    "Password Compromised": "credential",
    "Leak Site Content": "leak", "Leak Site URL": "leak",
    "Dark Web Mention (URL)": "leak",
    "Malicious IP Address": "phrase", "Malicious Internet Name": "phrase",
    "Vulnerability - Third Party Disclosed": "phrase",
    "Vulnerability - CVE Critical": "phrase",
}

_LABEL_KEY = {
    "domain": "domain", "ip": "address", "email": "email", "phone": "number",
    "username": "value", "socialaccount": "username", "individual": "full_name",
    "organization": "name", "cidr": "network", "asn": "asn_str", "website": "url",
    "port": "number", "dnsrecord": "value", "sslcertificate": "subject",
    "webtracker": "name", "cryptowallet": "address", "location": "address",
    "credential": "username", "leak": "name", "phrase": "text",
}


def list_modules() -> List[str]:
    """Список доступных модулей SpiderFoot (sfp_*.py) во встроенном движке."""
    mod_dir = os.path.join(SPIDERFOOT_HOME, "modules")
    if not os.path.isdir(mod_dir):
        return []
    return sorted(
        f[:-3] for f in os.listdir(mod_dir)
        if f.startswith("sfp_") and f.endswith(".py")
    )


def run_scan(
    target: str,
    modules: Optional[List[str]] = None,
    preset: str = "fast",
    timeout: int = 600,
) -> List[Dict[str, Any]]:
    """Запускает скан встроенного SpiderFoot через CLI (sf.py -o json) и
    возвращает список событий. Синхронно (блокирует до завершения скана)."""
    sf_py = os.path.join(SPIDERFOOT_HOME, "sf.py")
    if not os.path.isfile(sf_py):
        raise RuntimeError(
            "Встроенный SpiderFoot не найден в образе (SPIDERFOOT_HOME)."
        )
    mods = modules or PRESETS.get(preset, PRESETS["passive"])
    cmd = [
        "python", sf_py, "-s", target,
        "-m", ",".join(mods),
        "-o", "json", "-q",
    ]
    proc = subprocess.run(
        cmd, cwd=SPIDERFOOT_HOME, capture_output=True, text=True, timeout=timeout
    )
    out = proc.stdout.strip()
    # sf.py с -o json выводит JSON-массив событий в stdout
    try:
        data = json.loads(out)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    # запасной парсинг построчного JSON
    events = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


def events_to_graph(events: List[Dict[str, Any]], target: str) -> Tuple[List[dict], List[dict]]:
    """Преобразует события SpiderFoot в узлы и связи для графа.
    Узлы — по значению данных; связи строятся по полю source (родитель→данные)."""
    nodes: Dict[str, dict] = {}
    edges: List[dict] = []

    # корневой узел цели (значение -> ключ)
    troot = _guess_target_type(target)
    root_key = f"{troot}:{target.lower()}"
    nodes[root_key] = {"key": root_key, "type": troot, "label": target,
                       "properties": {"nodeLabel": target, "source": "SpiderFoot"}}
    value_to_key: Dict[str, str] = {target.lower(): root_key}

    for ev in events:
        etype = ev.get("type") or ev.get("Type") or ""
        data = (ev.get("data") or ev.get("Data") or "").strip()
        src = (ev.get("source") or ev.get("Source") or "").strip()
        if not data:
            continue
        ttype = SF_TYPE_MAP.get(etype)
        if ttype is None:
            continue
        val = data[:120]
        key = f"{ttype}:{val.lower()}"
        if key not in nodes:
            props = {"nodeLabel": val, "source": "SpiderFoot"}
            lk = _LABEL_KEY.get(ttype)
            if lk:
                props[lk] = val
            nodes[key] = {"key": key, "type": ttype, "label": val, "properties": props}
        value_to_key.setdefault(val.lower(), key)
        # связь от источника (если он уже известен как узел) к данным
        src_key = value_to_key.get(src.lower(), root_key)
        if src_key != key:
            edges.append({"source": src_key, "target": key, "label": etype})

    node_list = list(nodes.values())[:250]
    allowed = {n["key"] for n in node_list}
    edge_list = []
    seen = set()
    for e in edges:
        if e["source"] in allowed and e["target"] in allowed:
            sig = (e["source"], e["target"])
            if sig not in seen:
                seen.add(sig)
                edge_list.append(e)
    return node_list, edge_list[:400]


def _guess_target_type(target: str) -> str:
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", target):
        return "ip"
    if "@" in target:
        return "email"
    if re.match(r"^\+?\d[\d\s\-()]{5,}$", target):
        return "phone"
    return "domain"
