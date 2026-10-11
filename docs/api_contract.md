# API Contract --- RoomAI Backend and ML Pipeline

**API contract version:** 3.0\
**Last updated:** October 2026

-   **Local backend URL:** `http://127.0.0.1:8000`
-   **Remote ML pipeline URL:** Configured through `NGROK_URL`. The
    currently documented URL is
    `https://wackiness-spoils-manhunt.ngrok-free.dev`; it may change
    when the tunnel restarts.

This document describes the backend API and the backend-to-ML-pipeline
contract.

## 1. Supported operations

  -----------------------------------------------------------------------
  Operation               Purpose                 Click coordinates
  ----------------------- ----------------------- -----------------------
  `redesign`              Redesign the room in    Optional
                          the selected interior   
                          style while preserving  
                          the existing room       
                          structure.              

  `add_furniture`         Add requested furniture Both `click_x` and
                          at a selected location. `click_y` required
                          Mask generation and     
                          inpainting may be used  
                          internally by the ML    
                          pipeline.               
  -----------------------------------------------------------------------

`inpaint` is **not** a supported standalone operation. Inpainting is an
internal ML technique, not a separate API operation.

## 2. Endpoints

  -----------------------------------------------------------------------
  Method                  Endpoint                Purpose
  ----------------------- ----------------------- -----------------------
  `GET`                   `/`                     Basic backend status

  `GET`                   `/health`               Health check

  `GET`                   `/generate/metadata`    Supported styles,
                                                  operations, and
                                                  constraints

  `POST`                  `/generate/`            Generate a room image

  `GET`                   `/history`              Retrieve generation
                                                  history

  `GET`                   `/stats`                Retrieve generation
                                                  statistics
  -----------------------------------------------------------------------

The generation router is mounted without an extra `/generate` prefix, so
the generation endpoint is `/generate/`.

## 3. Generate an image --- `POST /generate/`

**Content type:** `multipart/form-data`

### Form fields

  -------------------------------------------------------------------------------------------
  Field                   Type                   Required Default          Description
  ----------------------- ------------- ----------------- ---------------- ------------------
  `file`                  File                        Yes ---              Input room image.
                                                                           Allowed
                                                                           extensions:
                                                                           `.jpg`, `.jpeg`,
                                                                           `.png`, `.webp`.
                                                                           Documented maximum
                                                                           size: 10 MB.

  `base_prompt`           String                      Yes ---              Room modification
                                                                           instructions.
                                                                           Backend validation
                                                                           requires 3--500
                                                                           characters.

  `style`                 String                       No `scandinavian`   One of
                                                                           `scandinavian`,
                                                                           `royal`,
                                                                           `industrial`,
                                                                           `custom`.

  `custom_style_prompt`   String              Conditional ---              Required when
                                                                           `style=custom`;
                                                                           describes the
                                                                           desired style and
                                                                           must be 3--500
                                                                           characters.

  `click_x`               Integer             Conditional ---              X coordinate for
                                                                           the selected
                                                                           furniture
                                                                           location. Required
                                                                           for
                                                                           `add_furniture`.

  `click_y`               Integer             Conditional ---              Y coordinate for
                                                                           the selected
                                                                           furniture
                                                                           location. Required
                                                                           for
                                                                           `add_furniture`.

  `user_id`               String                       No `default`        Identifier used to
                                                                           associate requests
                                                                           and history.

  `force_regenerate`      Boolean                      No `false`          Skip the cache and
                                                                           request a fresh
                                                                           generation.

  `operation`             String                       No `redesign`       `redesign` or
                                                                           `add_furniture`.
  -------------------------------------------------------------------------------------------

`base_prompt` describes the requested room changes, while `style`
selects the style preset. For a custom style, provide both `base_prompt`
and `custom_style_prompt`.

For `add_furniture`, send both coordinates. They must match the
coordinate system expected by the ML pipeline for the uploaded image.

### Query parameters

  Parameter   Allowed values    Default   Description
  ----------- ----------------- --------- ------------------------------
  `format`    `raw`, `base64`   `raw`     Selects the response format.

### Successful responses

**`200 OK` --- Raw image:** The backend returns image bytes with an
image content type, normally `image/jpeg`. The configured output is
expected to be 512 × 512 pixels.

**`200 OK` --- Base64 image:** `POST /generate/?format=base64` returns
JSON in this form:

``` json
{
  "image_base64": "<base64-encoded-image>"
}
```

The exact JSON metadata may vary according to the route implementation.

### Error responses

  -----------------------------------------------------------------------
  HTTP status                         Meaning
  ----------------------------------- -----------------------------------
  `400 Bad Request`                   Invalid file, style, operation,
                                      prompt length, missing custom style
                                      description, or missing click
                                      coordinates for `add_furniture`.

  `500 Internal Server Error`         Generation failed or the ML
                                      pipeline returned an unexpected
                                      response.

  `503 Service Unavailable`           The ML service cannot be reached or
                                      is unavailable, depending on the
                                      route's error mapping.

  `504 Gateway Timeout`               Generation exceeded the configured
                                      timeout, depending on the route's
                                      error mapping.
  -----------------------------------------------------------------------

Errors use FastAPI's JSON structure, typically
`{"detail": "Description of the error"}`.

## 4. Styles and metadata --- `GET /generate/metadata`

Supported styles: - `scandinavian` - `royal` - `industrial` - `custom`

Supported operations: - `redesign` - `add_furniture`

The metadata endpoint reports capabilities, output-image settings, input
constraints, and supported styles and operations. Use the live endpoint
as the source of truth.

``` bash
curl "http://127.0.0.1:8000/generate/metadata"
```

## 5. Generation history --- `GET /history`

Returns recent generation records, most recent first, for the requested
user.

  ----------------------------------------------------------------------------
  Parameter     Type                   Required Default         Description
  ------------- ------------- ----------------- --------------- --------------
  `user_id`     String                       No `default`       User whose
                                                                history should
                                                                be returned.

  `limit`       Integer                      No Route-defined   Maximum
                                                                records,
                                                                subject to
                                                                backend
                                                                constraints.
  ----------------------------------------------------------------------------

History records can include `request_id`, `user_id`, `base_prompt`,
`style`, `custom_style_prompt`, `operation`, `click_x`, `click_y`,
`input_url`, `output_url`, `cache_hit`, `processing_time_ms`, and
`created_at`, depending on the stored record and response
implementation.

``` bash
curl "http://127.0.0.1:8000/history?user_id=test_user"
```

## 6. Health and statistics

### `GET /health`

Checks backend and pipeline status. A healthy response may look like:

``` json
{
  "status": "healthy",
  "pipeline_status": "loaded"
}
```

Fields reflect the current runtime state.

### `GET /stats`

Returns generation statistics such as request totals, successes,
failures, and success rate, as implemented by the backend.

``` bash
curl "http://127.0.0.1:8000/stats"
```

### `GET /`

Returns a basic response indicating that the RoomAI backend is running.

## 7. Sample requests

Replace `room.jpg` with the path to your image.

### A. Redesign a room

``` bash
curl -X POST "http://127.0.0.1:8000/generate/"   -F "file=@room.jpg"   -F "base_prompt=Transform this room into a Scandinavian-style interior with light natural wood, neutral colours, warm lighting, and minimal decor. Preserve the room structure."   -F "style=scandinavian"   -F "operation=redesign"   -F "user_id=test_user"   -F "force_regenerate=true"   --output redesigned_room.jpg
```

### B. Add furniture at a selected location

The coordinates below are examples only. Use coordinates that match the
uploaded image and target location.

``` bash
curl -X POST "http://127.0.0.1:8000/generate/"   -F "file=@room.jpg"   -F "base_prompt=Add a clearly visible red three-seater sofa and a large wooden bookshelf to the selected area. Preserve the existing walls, windows, flooring, and camera angle."   -F "style=scandinavian"   -F "operation=add_furniture"   -F "click_x=370"   -F "click_y=350"   -F "user_id=test_user"   -F "force_regenerate=true"   --output room_with_furniture.jpg
```

Both coordinates are required for `add_furniture`.

### C. Request base64 output

``` bash
curl -X POST "http://127.0.0.1:8000/generate/?format=base64"   -F "file=@room.jpg"   -F "base_prompt=Create a warm minimalist living room with wood accents and a cozy reading nook."   -F "style=scandinavian"   -F "operation=redesign"   -F "user_id=test_user"
```

## 8. Backend-to-ML-pipeline contract

The backend sends a multipart request to the remote pipeline's
`/generate` endpoint. It forwards these fields as applicable:

-   `file`
-   `user_id`
-   `operation`
-   `base_prompt`
-   `custom_prompt`
-   `furniture_prompt`
-   `click_x`
-   `click_y`

Coordinates are sent as strings in the multipart form. Prompt fields
depend on the selected style.

Intended pipeline behavior:

1.  **`redesign`:** use the input room image and style/instructions to
    produce a redesigned room while preserving the room structure.
2.  **`add_furniture`:** use the input image, furniture instructions,
    and selected click location to add furniture. Mask generation and
    inpainting are internal processing steps.

The remote pipeline must accept the field names and operation values
sent by the backend. The backend expects a non-empty image response with
an `image/*` content type. The remote call timeout is 120 seconds.

A successful HTTP response does not guarantee that the requested
furniture was visually added; inspect generated output during testing.

## 9. Cache behavior

The backend caches generated results. Requests may return cached output
unless `force_regenerate=true` is supplied. The cache key includes the
pipeline version, style, custom style prompt, room instructions,
operation, and click coordinates so materially different requests do not
intentionally share a cache entry.

## 10. Operational notes

-   The remote pipeline URL is configured through `NGROK_URL`. The ngrok
    URL may change when the tunnel restarts.
-   Pipeline availability depends on the remote runtime and GPU session.
-   Generation time varies with model execution, image complexity, and
    runtime availability.
-   Check `/health` and `/generate/metadata` when debugging connectivity
    or supported options.

## 11. Mobile/client integration notes

-   Send image requests as `multipart/form-data`.
-   Include `base_prompt` and select a `style`.
-   For `style=custom`, also send `custom_style_prompt`.
-   Use `operation=redesign` for a full-room redesign.
-   Use `operation=add_furniture` and include both `click_x` and
    `click_y` to add furniture at a selected location.
-   Raw image output is the default; use `?format=base64` when the
    client needs a base64 JSON response.
-   Use the live metadata endpoint as the source of truth for supported
    styles and operations.
