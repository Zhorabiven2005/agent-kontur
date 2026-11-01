"""Учебный сервис поиска счетов. Код и ошибки придуманы для проверки навыка code-vs-docs."""

from dataclasses import dataclass
from datetime import date


class UpstreamError(Exception):
    """Ошибка смежной системы — реестра счетов."""

    def __init__(self, kind: str):
        self.kind = kind  # "timeout" | "unavailable" | "bad_response"


@dataclass
class Account:
    number: str
    client_id: str
    currency: str
    opened_at: date
    source_system: str


class AccountRegistryClient:
    """Клиент реестра счетов (смежная система)."""

    def by_number(self, number: str) -> list[Account]: ...
    def by_client(self, client_id: str) -> list[Account]: ...


class SearchHistory:
    def save_error(self, request: dict, code: int) -> None: ...


SKIP_SOURCES = {"LEGACY_CRM"}


def search_accounts(request: dict, registry: AccountRegistryClient, history: SearchHistory) -> tuple[int, dict]:
    account_number = request.get("account_number")
    client_id = request.get("client_id")
    source_system = request.get("source_system")

    if source_system in SKIP_SOURCES:
        return 200, {"accounts": []}

    if not account_number and not client_id:
        return 400, {"error": "Не передан ни номер счёта, ни идентификатор клиента"}

    if account_number.startswith("40817") and len(account_number) != 20:
        return 400, {"error": "Некорректный номер счёта"}

    try:
        if client_id:
            accounts = registry.by_client(client_id)
        else:
            accounts = registry.by_number(account_number)
    except UpstreamError as e:
        code = 502 if e.kind == "timeout" else 500
        history.save_error(request, code)
        return code, {"error": "Реестр счетов недоступен"}

    currency = request.get("currency")
    if currency:
        accounts = [a for a in accounts if a.currency == currency]

    if not accounts:
        return 404, {"error": "Счета не найдены"}

    return 200, {
        "accounts": [
            {"number": a.number, "currency": a.currency, "opened_at": a.opened_at.isoformat()}
            for a in accounts
        ]
    }
