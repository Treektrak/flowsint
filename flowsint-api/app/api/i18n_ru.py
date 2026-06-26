"""Слой русского перевода для данных, отдаваемых API (типы сущностей и обогатители).

Переводит человекочитаемые названия (label) и описания (description) категорий,
типов и обогатителей перед отдачей фронтенду, не затрагивая модели и логику.
Ключи (key/name) и значения данных остаются неизменными.
"""
from typing import Any

# --- Категории типов ---
CATEGORY_RU = {
    "global_category": "Глобальные",
    "person_category": "Личности и сущности",
    "organization_category": "Организации",
    "contact": "Связь и контакты",
    "network": "Сеть",
    "security": "Безопасность и доступ",
    "files": "Файлы и документы",
    "financial": "Финансовые данные",
    "leaks": "Утечки",
    "crypto": "Криптовалюта",
}

# --- Типы сущностей: key -> (label, description) ---
TYPE_RU = {
    "phrase": ("Фраза", "Фраза или текстовое содержимое."),
    "location": ("Локация", "Физический адрес с географическими координатами."),
    "individual": ("Личность", "Физическое лицо с подробной персональной информацией."),
    "username": ("Имя пользователя", "Имя пользователя или ник на любой платформе."),
    "organization": ("Организация", "Организация с подробными деловыми и административными данными."),
    "phone": ("Телефон", "Номер телефона с информацией о стране и операторе."),
    "email": ("Email", "Адрес электронной почты."),
    "socialaccount": ("Соцаккаунт", "Аккаунт в социальной сети (носитель имени пользователя)."),
    "message": ("Сообщение", "Сообщение с содержимым, метаданными и анализом безопасности."),
    "asn": ("ASN", "Номер автономной системы со связанной сетевой информацией."),
    "cidr": ("CIDR", "Сетевой блок CIDR (бесклассовая адресация)."),
    "domain": ("Домен", "Доменное имя и его свойства."),
    "website": ("Веб-сайт", "Веб-сайт с URL, доменом и информацией о редиректах."),
    "ip": ("IP", "IP-адрес с геолокацией и данными о провайдере."),
    "port": ("Порт", "Открытый сетевой порт, связанный с IP-адресом."),
    "dnsrecord": ("DNS-запись", "DNS-запись с типом, значением и информацией о безопасности."),
    "sslcertificate": ("SSL-сертификат", "SSL/TLS-сертификат с данными о валидации и безопасности."),
    "webtracker": ("Веб-трекер", "Технология веб-отслеживания с данными о приватности и соответствии требованиям."),
    "credential": ("Учётные данные", "Учётные данные пользователя с информацией о компрометации и использовании."),
    "session": ("Сессия", "Сессия пользователя с информацией об устройстве и активности."),
    "device": ("Устройство", "Устройство с аппаратной, программной и сетевой информацией."),
    "malware": ("ВПО", "Вредоносное ПО с семейством, возможностями и threat intelligence."),
    "weapon": ("Оружие", "Оружие с подробными характеристиками и криминалистической информацией."),
    "document": ("Документ", "Документ с метаданными, безопасностью и информацией о содержимом."),
    "file": ("Файл", "Файл с метаданными, информацией о типе и оценкой безопасности."),
    "bankaccount": ("Банковский счёт", "Банковский счёт с финансовой информацией и данными о безопасности."),
    "creditcard": ("Банковская карта", "Банковская карта с финансовыми данными и статусом безопасности."),
    "leak": ("Утечка", "Утечка или взлом данных со связанными данными."),
    "cryptowallet": ("Криптокошелёк", "Криптовалютный кошелёк."),
    "cryptowallettransaction": ("Криптотранзакция", "Криптовалютная транзакция."),
    "cryptonft": ("Крипто-NFT", "Невзаимозаменяемый токен (NFT), принадлежащий кошельку или выпущенный им."),
}

# --- Обогатители: name -> description ---
ENRICHER_RU = {
    "asn_to_cidrs": "[ASNMAP] Принимает ASN и возвращает соответствующие блоки CIDR.",
    "cidr_to_ips": "[MAPCIDR] Принимает CIDR и возвращает соответствующие IP-адреса.",
    "cryptowallet_to_nfts": "[ETHERSCAN] Находит NFT для адреса кошелька (ETH).",
    "cryptowallet_to_transactions": "[ETHERSCAN] Находит транзакции для адреса кошелька (ETH).",
    "domain_to_asn": "[ASNMAP] Принимает домен и возвращает соответствующий ASN.",
    "domain_to_dehashed": "[DeHashed] Получает данные об утечках по домену.",
    "domain_to_dummy": "Тестовый обогатитель.",
    "domain_to_history": "[WHOXY] Принимает домен и возвращает историю (история, организация, владельцы, email и т.д.).",
    "domain_to_ip": "Разрешает доменные имена в IP-адреса.",
    "domain_to_root_domain": "Поддомен → корневой домен.",
    "domain_to_subdomains": "Находит поддомены, связанные с доменом.",
    "domain_to_tls": "[httpX] Получает информацию TLS по домену.",
    "domain_to_website": "Из домена в веб-сайт.",
    "domain_to_whois": "Сканирует WHOIS-информацию домена.",
    "domain_to_whois_history": "[WHOISXML] Принимает домен и возвращает историю WHOIS (регистранты, регистраторы, организации).",
    "email_to_breaches": "[HIBPWNED] Находит утечки, в которых мог участвовать email.",
    "email_to_device_hudsonrock": "[HudsonRock] Находит устройства, связанные с email, по данным инфостилеров.",
    "email_to_domain": "Из email в домен.",
    "email_to_domains": "[WHOXY] Принимает email и возвращает зарегистрированные на него домены.",
    "email_to_gravatar": "Из MD5-хэша email в профиль Gravatar.",
    "email_to_intelligence": "[DeHashed] Получает данные об утечках по адресу email.",
    "email_to_username": "Из email в имя пользователя.",
    "individual_to_domains": "[WHOXY] Принимает личность и возвращает зарегистрированные домены.",
    "individual_to_organization": "[SIRENE] Находит организацию по человеку (данные SIRENE, только Франция).",
    "ip_to_asn": "[ASNMAP] Принимает IP-адрес и возвращает соответствующий ASN.",
    "ip_to_domain": "Разрешает IP-адреса в доменные имена через PTR, Certificate Transparency и опциональные API.",
    "ip_to_dummy_domains": "ТЕСТ: генерирует тестовые домены для проверки инкрементальных обновлений SSE.",
    "ip_to_fraudscore": "[Scamalytics] Получает оценку риска мошенничества для IP-адреса.",
    "ip_to_infos": "[ip-api.com] Получает информацию по IP-адресам.",
    "ip_to_intelligence": "[DeHashed] Получает данные об утечках по IP-адресу.",
    "ip_to_ports": "[NAABU] Сканирует порты IP-адресов для обнаружения открытых портов и сервисов.",
    "org_to_asn": "Принимает организацию и возвращает соответствующий ASN.",
    "org_to_domains": "[WHOXY] Принимает организацию и возвращает зарегистрированные домены.",
    "org_to_infos": "Обогащает организацию данными из SIRENE (только Франция).",
    "phone_to_carrier": "[veriphone] Определяет оператора номера телефона через API veriphone.",
    "phone_to_device_hudsonrock": "[HudsonRock] Находит устройства, связанные с номером телефона, по данным инфостилеров.",
    "phone_to_infos": "Получает информацию о номере телефона.",
    "username_to_dehashed": "[DeHashed] Получает данные об утечках по имени пользователя.",
    "username_to_device_hudsonrock": "[HudsonRock] Находит устройства, связанные с именем пользователя, по данным инфостилеров.",
    "username_to_socials_maigret": "[MAIGRET] Ищет соцаккаунты по именам пользователей с помощью Maigret.",
    "username_to_socials_sherlock": "[SHERLOCK] Ищет соцаккаунты по именам пользователей с помощью Sherlock.",
    "website_to_crawler": "Из веб-сайта в краулер.",
    "website_to_domain": "Из веб-сайта в домен.",
    "website_to_links": "Обходит веб-сайт и извлекает домены, внутренние и внешние ссылки.",
    "website_to_subdomains": "[c99.nl] Автоматический поиск поддоменов заданного домена.",
    "website_to_text": "Извлекает текстовое содержимое веб-страницы.",
    "website_to_webtrackers": "Из веб-сайта в веб-трекеры.",
}


def _tr_type_node(node: dict) -> None:
    key = node.get("key") or node.get("type", "").lower()
    if key in TYPE_RU:
        label, desc = TYPE_RU[key]
        node["label"] = label
        if node.get("description") is not None:
            node["description"] = desc


def translate_types_list(data: Any) -> Any:
    """Переводит категории и типы (рекурсивно по children)."""
    if not isinstance(data, list):
        return data
    for cat in data:
        if not isinstance(cat, dict):
            continue
        ckey = cat.get("key")
        if ckey in CATEGORY_RU:
            cat["label"] = CATEGORY_RU[ckey]
        for child in cat.get("children", []) or []:
            if isinstance(child, dict):
                _tr_type_node(child)
    return data


def translate_enrichers(data: Any) -> Any:
    """Переводит описания обогатителей по их name."""
    items = data if isinstance(data, list) else None
    if items is None:
        return data
    for e in items:
        if isinstance(e, dict):
            name = e.get("name")
            if name in ENRICHER_RU:
                e["description"] = ENRICHER_RU[name]
    return data
