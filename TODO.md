# TODO

## Books - COMPLETED ✅
- ✅ Align initial `processing_status` with frontend expectations (changed from `uploaded` to `pending`).
- ✅ Add concept facet handling in Dashboard (concept filtering fully implemented).
- ✅ Implement concept add/remove UI actions for books (add/remove functionality working in BookViewer).
- ✅ Provide buttons in BookViewer to trigger processing (queue and direct processing buttons implemented).
- ✅ Ensure `/api/books/facets` respects concept filters (facets API now accepts all filter parameters).
- ✅ Confirm worker integration and status polling (background tasks, imports, and error handling verified).

## Performance & Observability
- Evaluate caching strategy for system/statistics endpoints; monitor TTL effectiveness in staging.
- Benchmark batched concept lookup for book listing under real data volume.

## Cleanup / Tests
- Extend smoke tests to cover `/api/books/{id}/download` and concept add/remove workflow.
- Remove placeholder `processingMessage`/`processingError` state when backend returns structured status updates.

