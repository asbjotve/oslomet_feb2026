from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.helpers.async_tools import run_sync
from app.helpers.arbeidsoversikt import get_google_sheets_service

logger = logging.getLogger(__name__)

CLEAR_BASIC_FILTERS = False

'''
    Støttede filtreringsmuligheter
        - "Behandlingskode": "3" → tolkes som NUMBER_EQ
        - "Sendt epost?": {"type": "NUMBER_NOT_EQ", "value": "1"}
        - "Sendt epost?": {"type": "BLANK"}
        - "Sendt epost?": {"type": "NOT_BLANK"}
        - "Sendt epost?": {"hiddenValues": ["1"]}

    Hvis det skal filtreres på flere verdier:
        "Behandlingskode": {
         "type": "ONE_OF_LIST",
         "values": ["6", "7"],
         }
 '''
FILTER_VIEWS_BY_SHEET_NAME: dict[str, list[dict[str, Any]]] = {
  "Utdragsbehandling": [
    {
      "title": "Vis - Referanser over 15% - IKKE sendt epost",
      "conditions": {
        "Behandlingskode": "3",
        "Sendt epost?": {
          "type": "BLANK"
        },
      },
    },
    {
      "title": "Vis - Referanser over 15% - sendt epost",
      "conditions": {
        "Behandlingskode": "3",
        "Sendt epost?": "1",
      },
    },
    {
      "title": "Vis - Mangelfulle referanser - IKKE sendt epost",
      "conditions": {
        "Behandlingskode": "4",
        "Sendt epost?": {
          "type": "BLANK"
        },
      },
    },
    {
      "title": "Vis - Mangelfulle referanser - sendt epost",
      "conditions": {
        "Behandlingskode": "4",
        "Sendt epost?": "1",
      },
    },
    {
      "title": "Vis - Bøker/Referanser på reservering/request",
      "conditions": {
        "Behandlingskode": "9",
      },
    },
    {
      "title": "Vis - Bøker/referanser - Bestillingsvurdering - IKKE sendt epost",
      "conditions": {
        "Behandlingskode": "11",
        "Sendt epost?": {
          "type": "BLANK"
        },
      },
    },
    {
      "title": "Vis - Bøker/referanser - Bestillingsvurdering - sendt epost",
      "conditions": {
        "Behandlingskode": "11",
        "Sendt epost?": "1",
      },
    },
    {
      "title": "Vis - Referanser med fil fra bolk - IKKE fullført i Bolk",
      "conditions": {
        "Behandlingskode": "15",
      },
    },
    {
      "title": "Vis - Referanser med fil fra Bolk - Fullført i Bolk",
      "conditions": {
        "Behandlingskode": "16",
      },
    },
    {
      "title": "Vis - Rereferanser - sjekkes for fil/bolk/requstes",
      "conditions": {
        "Behandlingskode": "17",
      },
    },
    {
      "title": "Vis - Ubehandlede referanser",
      "conditions": {
        "Behandlingskode": "2000",
      },
    },
  ]
}

COLUMN_ALIASES = {
    "Behandlingskode": ["Behandlingskode"],
    "Sendt epost?": ["Sendt epost?", "Sendt epost"],
}


@dataclass(frozen=True)
class FilterViewsResult:
    spreadsheet_id: str
    spreadsheet_title: str
    sheet_name: str
    sheet_id: int
    row_count: int
    col_count: int
    deleted_filter_view_count: int
    cleared_basic_filter_sheet_ids: list[int]
    created_filter_titles: list[str]
    message: str


def _get_filter_views_for_sheet(sheet_name: str) -> list[dict[str, Any]]:
    filter_views = FILTER_VIEWS_BY_SHEET_NAME.get(sheet_name)
    if not filter_views:
        raise ValueError(f"Ingen filtervisninger konfigurert for sheet '{sheet_name}'.")
    return filter_views


def _find_column_index(header: list[str], logical_name: str) -> int:
    candidates = COLUMN_ALIASES.get(logical_name, [logical_name])
    for candidate in candidates:
        if candidate in header:
            return header.index(candidate)
    raise ValueError(
        f"Fant ikke kolonnen '{logical_name}'. Prøvde {candidates}. Header i arket: {header}"
    )


def _normalize_condition_spec(condition: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(condition, str):
        return {
            "condition": {
                "type": "NUMBER_EQ",
                "values": [{"userEnteredValue": condition}],
            }
        }

    normalized: dict[str, Any] = {}

    hidden_values = condition.get("hiddenValues")
    if hidden_values is not None:
        if not isinstance(hidden_values, list) or not hidden_values:
            raise ValueError(
                f"'hiddenValues' må være en ikke-tom liste, f.eks. {{'hiddenValues': ['1']}}: {condition}"
            )
        normalized["hiddenValues"] = [str(item) for item in hidden_values]

    if "visibleValues" in condition:
        raise ValueError(
            "'visibleValues' er ikke støttet i dette oppsettet. Bruk 'hiddenValues' eller 'type/value'."
        )

    condition_type = condition.get("type")
    if condition_type:
        value = condition.get("value")
        values = condition.get("values")

        if value is not None and values is not None:
            raise ValueError(f"Bruk enten 'value' eller 'values', ikke begge: {condition}")

        normalized["condition"] = {"type": condition_type}

        if values is not None:
            normalized["condition"]["values"] = [
                {"userEnteredValue": str(item)} for item in values
            ]
        elif value is not None:
            normalized["condition"]["values"] = [
                {"userEnteredValue": str(value)}
            ]

    if not normalized:
        raise ValueError(
            "Betingelse må ha enten 'type' eller 'hiddenValues'. "
            f"Eksempel: {{'type': 'BLANK'}} eller {{'hiddenValues': ['1']}}. Fikk: {condition}"
        )

    return normalized


def _build_delete_all_filters_requests(
    metadata: dict,
    *,
    clear_basic_filters: bool,
) -> tuple[list[dict[str, Any]], int, list[int]]:
    requests: list[dict[str, Any]] = []
    deleted_filter_view_count = 0
    cleared_basic_filter_sheet_ids: list[int] = []

    for sheet in metadata.get("sheets", []):
        basic_filter = sheet.get("basicFilter")
        if clear_basic_filters and basic_filter:
            sheet_id = int(sheet["properties"]["sheetId"])
            requests.append({"clearBasicFilter": {"sheetId": sheet_id}})
            cleared_basic_filter_sheet_ids.append(sheet_id)

        for filter_view in sheet.get("filterViews", []):
            requests.append(
                {
                    "deleteFilterView": {
                        "filterId": filter_view["filterViewId"],
                    }
                }
            )
            deleted_filter_view_count += 1

    return requests, deleted_filter_view_count, cleared_basic_filter_sheet_ids


def _build_add_filter_view_request(
    *,
    sheet_id: int,
    row_count: int,
    col_count: int,
    title: str,
    criteria: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "addFilterView": {
            "filter": {
                "title": title,
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": row_count,
                    "startColumnIndex": 0,
                    "endColumnIndex": col_count,
                },
                "criteria": {
                    str(column_index): criterion
                    for column_index, criterion in criteria.items()
                },
            }
        }
    }


async def replace_filter_views(
    *,
    service_account_file: str,
    spreadsheet_id: str,
    sheet_name: str,
) -> FilterViewsResult:
    service = await run_sync(get_google_sheets_service, service_account_file)

    meta = await run_sync(
        lambda: service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    )
    spreadsheet_title = meta.get("properties", {}).get("title", "") or ""

    sheet_id = None
    row_count = None
    col_count = None

    for sheet in meta.get("sheets", []):
        props = sheet.get("properties", {})
        if props.get("title") == sheet_name:
            sheet_id = props.get("sheetId")
            grid = props.get("gridProperties", {})
            row_count = grid.get("rowCount")
            col_count = grid.get("columnCount")
            break

    if sheet_id is None:
        raise ValueError(f"Fant ikke sheet '{sheet_name}' i spreadsheet.")
    if not row_count or not col_count:
        raise ValueError(f"Fant ikke gridProperties for sheet '{sheet_name}'.")

    header_res = await run_sync(
        lambda: service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!1:1")
        .execute()
    )
    header = (header_res.get("values") or [[]])[0]

    requests, deleted_filter_view_count, cleared_basic_filter_sheet_ids = (
        _build_delete_all_filters_requests(
            meta,
            clear_basic_filters=CLEAR_BASIC_FILTERS,
        )
    )

    filter_views = _get_filter_views_for_sheet(sheet_name)
    created_filter_titles: list[str] = []

    for filter_view in filter_views:
        criteria = {
            _find_column_index(header, logical_name): _normalize_condition_spec(condition)
            for logical_name, condition in filter_view["conditions"].items()
        }
        requests.append(
            _build_add_filter_view_request(
                sheet_id=int(sheet_id),
                row_count=int(row_count),
                col_count=int(col_count),
                title=str(filter_view["title"]),
                criteria=criteria,
            )
        )
        created_filter_titles.append(str(filter_view["title"]))

    await run_sync(
        lambda: service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests},
        ).execute()
    )

    logger.info(
        "replace_filter_views ok spreadsheet_id=%s sheet_name=%s created=%s deleted=%s",
        spreadsheet_id,
        sheet_name,
        len(created_filter_titles),
        deleted_filter_view_count,
    )

    return FilterViewsResult(
        spreadsheet_id=spreadsheet_id,
        spreadsheet_title=spreadsheet_title,
        sheet_name=sheet_name,
        sheet_id=int(sheet_id),
        row_count=int(row_count),
        col_count=int(col_count),
        deleted_filter_view_count=deleted_filter_view_count,
        cleared_basic_filter_sheet_ids=cleared_basic_filter_sheet_ids,
        created_filter_titles=created_filter_titles,
        message=f"Opprettet {len(created_filter_titles)} filtervisninger for '{sheet_name}'.",
    )
