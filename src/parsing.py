import json

from pydantic import ValidationError

from src.schema import SupportResponse

_DECODER = json.JSONDecoder()


class InvalidResponseError(ValueError):
    pass


def parse_support_response(text: str) -> SupportResponse:
    start = text.find("{")
    if start == -1:
        raise InvalidResponseError("no hay un objeto JSON en la respuesta")
    try:
        data, _ = _DECODER.raw_decode(text, start)
    except json.JSONDecodeError as error:
        raise InvalidResponseError("el JSON está mal formado") from error
    try:
        return SupportResponse.model_validate(data)
    except ValidationError as error:
        raise InvalidResponseError(_describe(error)) from error


def _describe(error: ValidationError) -> str:
    fields = sorted({".".join(str(part) for part in item["loc"]) for item in error.errors() if item["loc"]})
    return "campos inválidos: " + (", ".join(fields) or "estructura")
