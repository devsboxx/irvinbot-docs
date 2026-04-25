# irvinbot-docs

Microservicio de gestión de documentos de Irvinbot. Recibe PDFs, los procesa, genera embeddings y los almacena en ChromaDB para que el servicio de chat pueda hacer búsqueda semántica. Corre en el **puerto 8003**.

---

## Qué hace

- Recibe uploads de archivos PDF vía `multipart/form-data`
- Valida tipo de archivo y tamaño (máx. configurable, default 50 MB)
- Guarda el PDF en disco (`/data/uploads`)
- Parsea el PDF y lo divide en chunks de texto (1000 chars / 200 overlap)
- Genera embeddings con OpenAI y los almacena en ChromaDB con metadata del documento
- Rastrea cada documento en PostgreSQL con su estado (`processing` → `ready` o `error`)
- Permite listar y eliminar documentos (elimina de ChromaDB, disco y BD)

---

## Pipeline de ingestión

```
POST /docs/upload (PDF)
  └── docs_service.upload_document()
        ├── 1. _validate_file()          ← solo PDF, máx 50 MB
        ├── 2. guarda archivo en disco   ← /data/uploads/{uuid}_{filename}
        ├── 3. crea registro en DB       ← status = "processing"
        ├── 4. processing/pdf_parser.py  ← PyPDFLoader + RecursiveCharacterTextSplitter
        │       └── chunks con metadata: {document_id, user_id, source, chunk_index, page}
        ├── 5. processing/vector_store.py ← OpenAI embeddings + add a ChromaDB
        └── 6. actualiza DB              ← status = "ready", chunk_count = N
```

Si el procesamiento falla en cualquier paso, el documento queda con `status = "error"` y el mensaje de error guardado.

### Configuración del chunking

En `app/processing/pdf_parser.py`:

```python
CHUNK_SIZE = 1000     # caracteres por chunk
CHUNK_OVERLAP = 200   # solapamiento entre chunks
separators = ["\n\n", "\n", ". ", " ", ""]  # orden de preferencia de corte
```

### Metadata almacenada en cada chunk de ChromaDB

```python
{
  "document_id": "uuid-del-documento",   # para filtrar/eliminar todos los chunks del doc
  "user_id": "uuid-del-usuario",         # para filtrar por usuario en el retriever
  "source": "mi_tesis.pdf",              # nombre original del archivo
  "chunk_index": 0,                      # posición del chunk en el documento
  "page": 3,                             # página del PDF (provisto por PyPDFLoader)
}
```

---

## Estructura de archivos

```
irvinbot-docs/
├── main.py
├── Dockerfile
├── requirements.txt
├── .env.example
└── app/
    ├── api/
    │   └── docs_router.py       ← 4 endpoints
    ├── services/
    │   └── docs_service.py      ← upload, list, get, delete
    ├── models/
    │   └── document.py          ← tabla "documents"
    ├── schemas/
    │   └── docs.py              ← DocumentOut, DocumentList, UploadResponse
    ├── core/
    │   ├── config.py
    │   ├── database.py
    │   └── security.py
    └── processing/
        ├── pdf_parser.py        ← parse_and_chunk(file_path, metadata) → List[Document]
        └── vector_store.py      ← add_documents(), delete_by_document_id()
```

---

## Variables de entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Conexión PostgreSQL | `...irvinbot_docs` |
| `SECRET_KEY` | Para decodificar JWT (misma que auth) | — |
| `OPENAI_API_KEY` | Para generar embeddings (siempre requerido) | — |
| `CHROMA_HOST` | Host de ChromaDB | `localhost` |
| `CHROMA_PORT` | Puerto de ChromaDB | `8004` |
| `CHROMA_COLLECTION` | Colección en ChromaDB | `thesis_docs` |
| `UPLOAD_DIR` | Directorio donde se guardan los PDFs | `/data/uploads` |
| `MAX_FILE_SIZE_MB` | Tamaño máximo de archivo | `50` |

---

## Endpoints

Todos requieren header `Authorization: Bearer <access_token>`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/docs/upload` | Sube un PDF. `Content-Type: multipart/form-data`, campo `file` |
| `GET` | `/docs/` | Lista documentos del usuario autenticado |
| `GET` | `/docs/{id}` | Info de un documento específico |
| `DELETE` | `/docs/{id}` | Elimina documento de ChromaDB, disco y BD |
| `GET` | `/health` | Health check |

### Ejemplo: subir PDF
```bash
curl -X POST http://localhost:8003/docs/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@mi_tesis.pdf"

# Respuesta:
# {
#   "document": {"id": "...", "original_name": "mi_tesis.pdf", "status": "ready", "chunk_count": 42},
#   "message": "Documento procesado correctamente"
# }
```

---

## Modelo de datos

### Tabla `documents`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | UUID | PK, también usado como `document_id` en ChromaDB |
| `user_id` | UUID | FK lógico al usuario |
| `original_name` | VARCHAR(255) | Nombre original del archivo |
| `file_path` | VARCHAR(512) | Ruta absoluta en disco |
| `status` | VARCHAR(20) | `processing`, `ready`, o `error` |
| `chunk_count` | INTEGER | Número de chunks en ChromaDB |
| `error_message` | TEXT | Mensaje de error si falló |
| `created_at` | TIMESTAMPTZ | — |

---

## Cómo correr localmente

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p /data/uploads   # o cambiar UPLOAD_DIR en .env
uvicorn main:app --reload --port 8003
```

ChromaDB debe estar corriendo. La forma más fácil:
```bash
docker run -p 8004:8000 chromadb/chroma
```

### Correr tests
```bash
pytest app/tests/ -v
# Los tests mockean pdf_parser y vector_store, no requieren ChromaDB real
```

---

## Cómo extender este servicio

**Soportar otros tipos de archivo (DOCX, TXT):**
1. En `_validate_file()`, permitir más extensiones
2. En `processing/`, añadir `docx_parser.py` con `Docx2txtLoader` de LangChain
3. En `docs_service.upload_document()`, elegir el parser según la extensión

**Procesar en background (para archivos grandes):**
1. Instalar `celery` + `redis`
2. Mover el procesamiento (parse + embed) a una tarea Celery
3. El endpoint devuelve inmediatamente con `status = "processing"`
4. El frontend hace polling a `GET /docs/{id}` hasta `status = "ready"`

**Cambiar el modelo de embeddings:**
En `processing/vector_store.py`, reemplazar `OpenAIEmbeddings` por otro:
```python
from langchain_community.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
```

**Filtrar por usuario en el chat:**
El retriever de `irvinbot-chat` puede añadir `filter={"user_id": user_id}` para que cada estudiante solo vea resultados de sus propios documentos.
