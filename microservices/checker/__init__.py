"""
Standalone FastStream microservice for AI coursework checking.

This package intentionally does not import anything from the main FastAPI API.
It communicates with the API through RabbitMQ and updates shared MongoDB
collections using local Beanie document models with the same collection names.
"""
