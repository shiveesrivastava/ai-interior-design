# API Contract — Backend

**Version:** 2.0  
**Last Updated:** April 2026  
**Base URL (local):** http://127.0.0.1:8000  
**Base URL (production):** ngrok URL (updated in Week 3)

---

## Endpoints

### GET /generate/

Information about the generate endpoint.

**Response 200**
```json
{
  "endpoint": "/generate/",
  "method": "POST",
  "input": "image file (JPEG, PNG, WEBP)",
  "output": "redesigned room image (JPEG or base64)"
}
````

---

### POST /generate/

Upload a room image and receive a redesigned version.

---

## Request

* Method: POST
* Content-Type: multipart/form-data

### Form Fields

| Field       | Type   | Required | Description                            |
| ----------- | ------ | -------- | -------------------------------------- |
| file        | File   | Yes      | Room image (JPEG, PNG, WEBP, max 10MB) |
| base_prompt | String | No       | Custom prompt (default provided)       |
| click_x     | Int    | No       | X coordinate for object edit           |
| click_y     | Int    | No       | Y coordinate for object edit           |
| user_id     | String | No       | User identifier                        |

---

### Query Parameters

| Param  | Values       | Description                    |
| ------ | ------------ | ------------------------------ |
| format | raw / base64 | Response format (default: raw) |

---

## Response

### 200 — Raw Image (default)

* Content-Type: `image/jpeg`
* Headers:

```
Content-Disposition: inline; filename="redesigned_room.jpg"
```

* Body: JPEG image (512x512)

---

### 200 — Base64 Response

```json
{
  "image_base64": "..."
}
```

---

## Error Responses

### 400 — Invalid Input

```json
{
  "detail": "Invalid image content or dimensions."
}
```

### 503 — ML Service Unavailable

```json
{
  "detail": "Cannot reach image generation service."
}
```

### 504 — Timeout

```json
{
  "detail": "Image generation timed out."
}
```

### 500 — General Failure

```json
{
  "detail": "Image Generation Failed."
}
```

---

## GET /generate/metadata

Returns API capabilities and constraints.

### Response 200

```json
{
  "output_image": {
    "format": "JPEG",
    "dimensions": "512x512",
    "quality": 95
    },
  "input_constraints": {
    "max_file_size": "10MB",
    "allowed_formats": ["jpg", "jpeg", "png", "webp"]
    },
  "features": {
    "base64_supported": true,
    "click_coordinates_supported": true
    }
}
```

---

## GET /health

Server health check.

### Response 200

```json
{
  "status": "healthy"
}
```

---

## Sample curl Commands

### Raw Image

```bash
curl -X POST "http://127.0.0.1:8000/generate/" \
  -F "file=@room.jpg" \
  --output result.jpg
```

---

### Base64 Response

```bash
curl -X POST "http://127.0.0.1:8000/generate/?format=base64" \
  -F "file=@room.jpg"
```

---

## Notes for Mobile Developer

* Send image as `multipart/form-data`
* Default response is raw image (`image/jpeg`)
* Use `?format=base64` if base64 is required
* Max upload size: 10MB
* Output image is always 512x512 JPEG
* ngrok URL changes each session — use latest shared URL

---

````

---