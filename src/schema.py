from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["billing", "technical", "account", "other"]
CATEGORIES: tuple[str, ...] = get_args(Category)

ACTION_CATALOG: tuple[str, ...] = (
    "verificar_cobro_duplicado",
    "gestionar_reintegro",
    "reenviar_factura",
    "actualizar_medio_de_pago",
    "explicar_cargos",
    "revisar_logs_del_error",
    "verificar_estado_de_integracion",
    "solicitar_capturas_o_pasos",
    "escalar_a_soporte_tecnico_n2",
    "restablecer_acceso",
    "gestionar_usuarios_y_permisos",
    "actualizar_datos_de_la_cuenta",
    "verificar_identidad_del_titular",
    "derivar_a_ventas",
    "solicitar_mas_informacion",
    "derivar_a_agente_humano",
)


class SupportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    category: Category
    actions: list[str] = Field(min_length=1)


FALLBACK_ANSWER = "No pudimos procesar tu consulta automáticamente. Un agente de soporte la va a revisar."


def fallback_response() -> SupportResponse:
    return SupportResponse(
        answer=FALLBACK_ANSWER,
        confidence=0.0,
        category="other",
        actions=["derivar_a_agente_humano"],
    )
