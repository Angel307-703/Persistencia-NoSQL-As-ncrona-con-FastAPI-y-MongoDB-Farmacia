from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema

class _ObjectIdPydanticAnnotation:
    """Adaptador para validar y serializar ObjectId de MongoDB en Pydantic v2"""
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        def validate(v):
            if isinstance(v, ObjectId):
                return str(v)
            if isinstance(v, str) and ObjectId.is_valid(v):
                return v
            raise ValueError("ID invalido de MongoDB (ObjectId)")

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )

PyObjectId = Annotated[str, _ObjectIdPydanticAnnotation]

class MedicamentoBase(BaseModel):
    nombre_producto: str = Field(..., min_length=2, max_length=150, description="Nombre del medicamento")
    laboratorio: str = Field(..., min_length=2, max_length=150, description="Laboratorio fabricante")
    precio: float = Field(..., gt=0, description="Precio del producto al público")
    requiere_receta: bool = Field(default=False, description="Indica si el medicamento requiere receta médica")

class MedicamentoCreate(MedicamentoBase):
    """Modelo utilizado para recibir solicitudes POST de creación"""
    pass

class MedicamentoUpdate(BaseModel):
    """Modelo para solicitudes PUT (Campos opcionales para edición)"""
    nombre_producto: Optional[str] = Field(None, min_length=2, max_length=150)
    laboratorio: Optional[str] = Field(None, min_length=2, max_length=150)
    precio: Optional[float] = Field(None, gt=0)
    requiere_receta: Optional[bool] = None

class Medicamento(MedicamentoBase):
    """Modelo completo de respuesta que incluye el ID de MongoDB y la fecha"""
    id: PyObjectId = Field(alias="_id", description="Identificador único ObjectId de MongoDB")
    fecha_creacion: datetime = Field(default_factory=datetime.now, description="Fecha de registro")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "_id": "654321789abcdef012345678",
                "nombre_producto": "Acetaminofén 500mg",
                "laboratorio": "Genfar",
                "precio": 2500.0,
                "requiere_receta": False,
                "fecha_creacion": "2026-11-05T18:30:00"
            }
        }
    )