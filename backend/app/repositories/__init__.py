"""
Data-access layer for SmartTrendTracer.

API routers stay thin (HTTP concerns: params, status codes); the MongoDB
queries and the rules attached to them live here:

* tweets._id is the Twitter ID string (see tweets.save_tweets)
* tag_instances.concept_id is stored in mixed form — query via
  app.database.mongodb.concept_id_query_variants
* repositories raise app.repositories.errors.*, never FastAPI exceptions;
  app.main maps them to HTTP responses.

Modules are imported explicitly (from app.repositories import tweets);
this package deliberately re-exports nothing.
"""
