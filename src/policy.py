import re

_NUM = (
    r"(?:\d+|un|una|uno|um|uma|dos|tres|cuatro|quatro|cinco|seis|siete|sete|ocho|nueve|diez|doce|quince|veinte|"
    r"treinta|veinticuatro|vinte e quatro|cuarenta y ocho|quarenta e oito|one|two|three|four|five|six|seven|"
    r"eight|nine|ten|twelve|thirty|twenty-four|forty-eight)"
)
_UNIT = r"(?:horas?|hs|h|hours?|hrs?|d[ií]as?|days?|minutos?|minutes?|semanas?|weeks?|meses|mes|months?)\b"
_REFUND_VERB = r"(?:devolv|devuelv|reembols|reintegr|bonific|descont|estorn|credit|refund|reimburs)\w*"
_REFUND_OBJ = r"(?:reembols|reintegr|devolu|desc(?:uent|ont)|bonific|rebaj|estorn|refund|reimburs|discount|rebate)\w*"
_MONEY = rf"(?:{_REFUND_OBJ}|dinero|plata|cargo|cobro|valor|importe|monto)\w*"
_GIVE = r"(?:aplic|otorg|conced|bonific)\w*"
_PERCENT = r"(?:\d+\s*(?:%|por ciento|percent)\s*(?:de\s+|off\s+)?)?"
_GAP = r"(?:\s+[^\s.;:!?,]+){0,3}?\s+"
_PRONOUN = r"(?:te|le|les|lhe|lhes)"
_NOT_CALLBACK = r"(?!\s+(?:(?:la|el|los|las|tu|su)\s+)?(?:llamad|mensaj|correo|respuesta|contact|consult|mail|email))"
_FUTURE = r"(?:vamos a|voy a|van a|vamos|vou|iremos)"
_WE_FUTURE = r"(?:we will|we(?:'|’)ll|we are going to|we(?:'|’)re going to)"
_WE_STATE = r"(?:we will|we(?:'|’)ll|we are|we(?:'|’)re|we have|we(?:'|’)ve)"

_PATTERNS: tuple[str, ...] = (
    rf"\b{_PRONOUN}\s+(?:{_FUTURE}\s+)?{_REFUND_VERB}\b{_NOT_CALLBACK}",
    rf"\b{_FUTURE}\s+(?:devolver|reintegrar|reembolsar|bonificar|descontar|estornar|creditar){_PRONOUN}\b"
    rf"{_NOT_CALLBACK}",
    rf"\b{_PRONOUN}\s+(?:{_FUTURE}\s+)?(?:aplic|otorg|conced|bonific|d(?:ar|a|amos|oy))\w*"
    rf"{_GAP}{_PERCENT}{_REFUND_OBJ}",
    rf"\b(?:vamos a|voy a|van a|se)\s+(?:{_GIVE}|{_REFUND_VERB}){_GAP}{_PERCENT}{_MONEY}",
    rf"\b(?:vamos a|voy a|van a|se)\s+dar\w*\s+(?:un|una|el|la)\s+{_PERCENT}{_REFUND_OBJ}",
    rf"\b(?:se|ser[aá]n?|ser[aã]o|s[aã]o|é|will be|has been|have been|is being|are being)\s+"
    rf"(?:va a\s+|va\s+a\s+)?{_REFUND_VERB}",
    rf"\b(?:estamos|estoy|estaremos|est[aá]n|estou|est[aã]o)\s+(?:ya\s+|j[aá]\s+)?"
    rf"(?:proces|process|tramit|gestion|gener|realiz|emit|aprob|aplic|trat|prepar)\w*{_GAP}{_PERCENT}{_REFUND_OBJ}",
    rf"\b{_WE_FUTURE}\s+(?:already\s+|now\s+|just\s+)?(?:refund|reimburs|credit)\w*",
    rf"\b{_WE_STATE}\s+(?:already\s+|now\s+|just\s+|be\s+)?(?:apply|give|issue|process|grant|offer|waive)\w*"
    rf"{_GAP}{_PERCENT}{_REFUND_OBJ}",
    rf"\b(?:receber[aá]|vai receber|you (?:will|(?:'|’)ll) (?:receive|get))\b{_GAP}{_PERCENT}{_REFUND_OBJ}",
    rf"\b(?:ten[eé]s|tiene|tendr[aá]s?|cuentas con|tem|you have|you(?:'|’)ve got)\s+(?:un|una|um|uma|a|an)\s+"
    rf"{_PERCENT}{_REFUND_OBJ}",
    rf"\b{_PRONOUN}\s+(?:corresponde|corresponden|cabe)\s+(?:un|una|el|la|los|las|um|uma|o|a)?\s*{_PERCENT}"
    rf"{_REFUND_OBJ}",
    rf"\b{_REFUND_OBJ}\s+(?:ya\s+)?(?:est[aá]|fue|ha sido|est[aã]o|foi|foram|is|was|has been|is being|are)\s+"
    rf"(?:ya\s+)?(?:aprobad|acreditad|procesad|tramitad|aprovad|processad|approved|processed|refunded|credited|"
    rf"confirmad|autorizad)\w*",
    rf"\b(?:en|em|dentro de|antes de|within|in)\s+(?:(?:las?|los?|the next)\s+)?(?:pr[oó]xim[oa]s?\s+)?"
    rf"{_NUM}\s*{_UNIT}",
)

_COMPILED = tuple(re.compile(pattern, re.IGNORECASE) for pattern in _PATTERNS)
_CLAUSE_BREAK = re.compile(
    r"[,;:.!?¿¡]|\b(?:pero|aunque|sin embargo|but|although|however|porém|mas)\b", re.IGNORECASE
)
_NEGATION = re.compile(r"\b(?:no|nunca|jamás|ni|sin|not|never|n[ãa]o|nem)\b", re.IGNORECASE)


def find_promises(answer: str) -> list[str]:
    found = [
        match.group(0)
        for pattern in _COMPILED
        for match in pattern.finditer(answer)
        if not _negated(answer, match.start())
    ]
    return list(dict.fromkeys(found))


def _negated(text: str, start: int) -> bool:
    clause_start = 0
    for break_match in _CLAUSE_BREAK.finditer(text, 0, start):
        clause_start = break_match.end()
    return _NEGATION.search(text, clause_start, start) is not None
