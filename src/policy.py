import re

_NUM = (
    r"(?:\d+|un|una|uno|um|uma|dos|tres|cuatro|quatro|cinco|seis|siete|sete|ocho|nueve|diez|doce|quince|veinte|"
    r"treinta|veinticuatro|vinte e quatro|cuarenta y ocho|quarenta e oito|one|two|three|four|five|six|seven|"
    r"eight|nine|ten|twelve|thirty|twenty-four|forty-eight)"
)
_UNIT = r"(?:horas?|hs|h|hours?|hrs?|d[ií]as?|days?|minutos?|minutes?|semanas?|weeks?|meses|mes|months?)\b"
_CALLBACK = r"(?:llamad|mensaj|correo|respuesta|contact|consult|mail|email)"

COMMITMENT = re.compile(
    r"\b(?:vamos\s+a|voy\s+a|van\s+a|vamos|vou|iremos|we\s+will|we(?:'|’)ll|we\s+are\s+going\s+to|will\s+be"
    r"|ser[aá]n?|ser[aã]o|ya\s+estamos|ya\s+\w+[ae]mos|(?:ya\s+)?estamos\s+(?:ya\s+)?\w+(?:ando|endo|indo)"
    r"|se\s+(?:acredit|devuelv|reintegr|reembols|descont|bonific|estorn|aplic)\w*"
    r"|(?:te|les|le|lhe)\s+(?:lo\s+|la\s+|los\s+|las\s+)?\w+[ae]mos|(?:lo|la|los|las)\s+\w+[ae]mos)\b",
    re.IGNORECASE,
)
TOPIC = re.compile(
    rf"\b(?:reembols|reintegr|devol|acredit|desc(?:uent|ont)|bonific|estorn|refund|credit|cobrad)\w*\b"
    rf"(?!\s+(?:(?:la|el|tu|su|los|las)\s+)?{_CALLBACK})",
    re.IGNORECASE,
)
HEDGE = re.compile(r"\bevalu\w*|\brevis\w*|\bverific\w*|\bposib\w*", re.IGNORECASE)
STATE_CLAIM = re.compile(
    r"\b(?:ya\s+)?(?:est[aá]n?|fue|fueron|ha\s+sido|han\s+sido|est[aã]o|foi|foram|is|was|are|has\s+been"
    r"|have\s+been)\s+(?:ya\s+)?(?:aprobad|acreditad|procesad|tramitad|confirmad|autorizad|aprovad|processad"
    r"|approved|processed|refunded|credited)\w*",
    re.IGNORECASE,
)
PLAZO = re.compile(
    rf"\b(?:en|em|dentro\s+de|antes\s+de|within|in)\s+(?:(?:las?|los?|the\s+next)\s+)?"
    rf"(?:pr[oó]xim[oa]s?\s+)?{_NUM}\s*{_UNIT}",
    re.IGNORECASE,
)
CLAUSE_BREAK = re.compile(
    r"[,;:.!?¿¡]|\b(?:pero|aunque|sin embargo|but|although|however|porém|mas)\b", re.IGNORECASE
)
NEGATIONS = frozenset({"no", "nunca", "jamás", "ni", "sin", "nem", "não", "nao", "not", "never"})


def find_promises(answer: str) -> list[str]:
    found: list[str] = []
    for clause in CLAUSE_BREAK.split(answer):
        if HEDGE.search(clause):
            continue
        commits = _live(clause, COMMITMENT)
        if (commits and (TOPIC.search(clause) or PLAZO.search(clause))) or _live(clause, STATE_CLAIM):
            found.append(clause.strip())
    return list(dict.fromkeys(found))


def _live(clause: str, pattern: re.Pattern[str]) -> bool:
    return any(not _negated(clause, match.start()) for match in pattern.finditer(clause))


def _negated(clause: str, start: int) -> bool:
    return any(word in NEGATIONS for word in re.findall(r"\w+", clause[:start].lower())[-3:])
