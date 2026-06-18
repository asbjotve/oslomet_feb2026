from typing import List, Literal, Optional

Variant = Literal["ALLE", "SKAL_BOLKES", "DECLINED", "SKAL_LAASES"]


def map_fakultet(fakultet: str) -> Optional[List[str]]:
    """
    Returnerer liste over fakultet-koder som skal brukes i IN (...),
    eller None hvis det betyr "ingen filter" (ALLE).
    """
    f = (fakultet or "ALLE").strip().upper().replace(" ", "")

    if f in ("ALLE", "ALL", ""):
        return None
    if f == "SAM":
        return ["SAM"]
    if f == "TKD,LUI,HV":
        return ["TKD", "LUI", "HV"]

    raise ValueError(f"Ugyldig fakultet: {fakultet}")


def map_variant(variant: str) -> Variant:
    """
    Normaliserer variant fra query-parameter.
    """
    v = (variant or "ALLE").strip().upper().replace("-", "_").replace(" ", "_")

    if v in ("ALLE", "ALL", ""):
        return "ALLE"
    if v in ("SKAL_BOLKES", "SKALBOLKES"):
        return "SKAL_BOLKES"
    if v == "DECLINED":
        return "DECLINED"
    if v in ("SKAL_LAASES", "SKAL_LÅSES", "SKALLAASES", "SKALLÅSES"):
        return "SKAL_LAASES"

    raise ValueError(f"Ugyldig variant: {variant}")


def variant_clause(variant: Variant) -> str:
    """
    Returnerer ekstra WHERE-betingelse basert på variant.
    Tom streng betyr "ingen ekstra filter".
    """
    if variant == "ALLE":
        return ""
    if variant == "SKAL_BOLKES":
        return "AND antall_skal_bolkes > 0"
    if variant == "DECLINED":
        return "AND antall_declined > 0"
    if variant == "SKAL_LAASES":
        return "AND total_referanser_rapporteringspliktig = antall_bolket"
    raise ValueError(f"Ugyldig variant: {variant}")
