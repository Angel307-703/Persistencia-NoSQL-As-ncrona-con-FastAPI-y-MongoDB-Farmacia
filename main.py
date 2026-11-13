from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from bson import ObjectId
from datetime import datetime

from models import Medicamento, MedicamentoCreate, MedicamentoUpdate
from database import coleccion_medicamentos, verificar_conexion

app = FastAPI(
    title="API Droguería - SENA ADSO",
    description="API RESTful asíncrona con FastAPI y MongoDB (FARM Stack).",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await verificar_conexion()


@app.get("/", tags=["Raíz"])
async def root():
    return {
        "mensaje": "Bienvenido a la API Asíncrona de Droguería (SENA ADSO)",
        "documentacion": "/docs"
    }

@app.post(
    "/medicamentos",
    response_model=Medicamento,
    status_code=status.HTTP_201_CREATED,
    tags=["Medicamentos"],
    summary="Crear un nuevo medicamento en MongoDB"
)
async def create_medicamento(medicamento_in: MedicamentoCreate):
    medicamento_existente = await coleccion_medicamentos.find_one({"nombre_producto": medicamento_in.nombre_producto})
    if medicamento_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un medicamento registrado con el nombre '{medicamento_in.nombre_producto}'."
        )

    nuevo_medicamento = medicamento_in.model_dump()
    nuevo_medicamento["fecha_creacion"] = datetime.now()

    resultado = await coleccion_medicamentos.insert_one(nuevo_medicamento)
    medicamento_creado = await coleccion_medicamentos.find_one({"_id": resultado.inserted_id})
    return medicamento_creado


@app.get(
    "/medicamentos",
    response_model=List[Medicamento],
    status_code=status.HTTP_200_OK,
    tags=["Medicamentos"],
    summary="Listar todos los medicamentos"
)
async def get_medicamentos():
    medicamentos = []
    cursor = coleccion_medicamentos.find()
    async for documento in cursor:
        medicamentos.append(documento)
    return medicamentos


@app.get(
    "/medicamentos/{id}",
    response_model=Medicamento,
    status_code=status.HTTP_200_OK,
    tags=["Medicamentos"],
    summary="Buscar medicamento por ObjectId"
)
async def get_medicamento_por_id(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido de MongoDB."
        )

    medicamento = await coleccion_medicamentos.find_one({"_id": ObjectId(id)})
    if medicamento:
        return medicamento

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"El medicamento con ID '{id}' no fue encontrado."
    )


@app.put(
    "/medicamentos/{id}",
    response_model=Medicamento,
    status_code=status.HTTP_200_OK,
    tags=["Medicamentos"],
    summary="Actualizar campos de un medicamento"
)
async def update_medicamento(id: str, medicamento_update: MedicamentoUpdate):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido."
        )

    datos_a_actualizar = medicamento_update.model_dump(exclude_unset=True)

    if len(datos_a_actualizar) >= 1:
        resultado_actualizacion = await coleccion_medicamentos.update_one(
            {"_id": ObjectId(id)},
            {"$set": datos_a_actualizar}
        )

        if resultado_actualizacion.modified_count == 1 or resultado_actualizacion.matched_count == 1:
            medicamento_modificado = await coleccion_medicamentos.find_one({"_id": ObjectId(id)})
            return medicamento_modificado

    medicamento_existente = await coleccion_medicamentos.find_one({"_id": ObjectId(id)})
    if medicamento_existente:
        return medicamento_existente

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No es posible actualizar. El medicamento con ID '{id}' no existe."
    )


@app.delete(
    "/medicamentos/{id}",
    status_code=status.HTTP_200_OK,
    tags=["Medicamentos"],
    summary="Eliminar medicamento de MongoDB"
)
async def delete_medicamento(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido."
        )

    resultado_eliminacion = await coleccion_medicamentos.delete_one({"_id": ObjectId(id)})

    if resultado_eliminacion.deleted_count == 1:
        return {"mensaje": f"Medicamento con ID '{id}' eliminado exitosamente de MongoDB."}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No es posible eliminar. El medicamento con ID '{id}' no existe en la base de datos."
    )