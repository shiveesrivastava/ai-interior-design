# API Contract — Backend

**Version:** 1.0  
**Last Updated:** April 2026  
**Base URL (local):** http://127.0.0.1:8000  
**Base URL (production):** ngrok URL (updated in Week 3)

---

## Endpoints

---

### GET /generate/

Health check for the generate endpoint.

**Request**
- Method: GET
- No body required

**Response 200**
```json
{
  "endpoint": "/generate",
  "method": "POST",
  "input": "image file (JPEG, PNG, WEBP) + optional style",
  "styles": ["scandinavian", "royal", "industrial", "bohemian"],
  "output": "redesigned room image"
}
```

---

### POST /generate/

Upload a room image and receive a redesigned version.

**Request**
- Method: POST
- Content-Type: multipart/form-data

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file  | File | Yes | Room image (JPEG, PNG, WEBP, max 10MB) |
| style | Text | No | Design style (default: scandinavian) |

**Available styles**
| Value | Description |
|-------|-------------|
| scandinavian | Modern minimal, warm lighting, hardwood floors |
| royal | Luxurious, gold accents, velvet furniture |
| industrial | Exposed brick, metal fixtures, loft style |
| bohemian | Earth tones, plants, cozy textures |

**Response 200**
- Content-Type: image/jpeg
- Body: redesigned room image (512x512 JPEG)

**Response 400**
```json
{
  "detail": "Invalid file type: application/pdf. Allowed: JPEG, PNG, WEBP"
}
```

**Response 500**
```json
{
  "detail": "Internal server error"
}
```

---

### GET /health

Server health check.

**Response 200**
```json
{
  "status": "healthy"
}
```

---

## Sample curl Command
```bash
curl -X POST http://127.0.0.1:8000/generate/ \
  -F "file=@/path/to/room.jpg" \
  -F "style=scandinavian" \
  --output result.jpg
```

---

## Notes for Person 3 (Mobile)

- Send image as `multipart/form-data`
- Style field is optional — defaults to scandinavian
- Response is raw image bytes (image/jpeg)
- Save the response directly as a .jpg file
- ngrok URL will change each Kaggle session —
  check WhatsApp for the latest URL