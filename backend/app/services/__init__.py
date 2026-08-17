"""
backend/app/services/__init__.py
==================================
Service layer — business logic between HTTP routes and the ML pipeline.

  model_service     — loads / reloads trained .pkl artifacts from disk
  stats_service     — process-lifetime prediction counters
  inference_service — wraps raw model calls into clean result dicts
"""
