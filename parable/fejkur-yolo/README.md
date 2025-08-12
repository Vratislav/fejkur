Run the FastAPI YOLO service locally:

1. Install deps once:

```
poetry install --no-interaction --no-root
```

2. Start server:

```
poetry run python -m fejkur.server
```

Environment variables:

- `FEJKUR_HOST` (default `127.0.0.1`)
- `FEJKUR_PORT` (default `8001`)
- `FEJKUR_YOLO_MODEL` (default `./models/yolo11n.pt`)

POST /detect body:

```
{
  "source_path": "/abs/path/to/image.jpg",
  "conf": 0.5,
  "save_txt": true,
  "save_conf": true
}
```

Response:

```
{
  "humansDetected": true,
  "humansCount": 1,
  "saveDir": "/.../runs/detect/predict"
}
```


