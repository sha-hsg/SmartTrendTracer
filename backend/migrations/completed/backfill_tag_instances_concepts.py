"""Backfill MongoDB tag_instances with concept identifiers.

The script locates legacy tag assignments that are missing `concept_id` or
still store a plain `tag` field, ensures the corresponding concept exists in
`tag_concepts_v2`, and updates the tag instance in-place. This keeps existing
metadata (confidence, tag_type, source) while making downstream APIs
consistent with the concept-only schema.

Run from the backend directory (ideally inside the existing virtualenv):

    python backfill_tag_instances_concepts.py
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Tuple

from bson import ObjectId

from app.services.concept_only_tag_service import ConceptOnlyTagService


logger = logging.getLogger(__name__)


def ensure_concept(
    concept_service: ConceptOnlyTagService,
    tag_text: str,
) -> Tuple[ObjectId, bool]:
    """Return a concept identifier for the provided tag text, creating one if needed."""

    slug = concept_service._normalize_to_slug(tag_text)  # pylint: disable=protected-access

    existing = concept_service.tag_concepts.find_one({"slug": slug})
    if existing:
        return existing["_id"], False

    display_name = concept_service._generate_display_name(slug)  # pylint: disable=protected-access
    concept_doc: Dict[str, object] = {
        "id": concept_service._generate_concept_id(),  # pylint: disable=protected-access
        "slug": slug,
        "name": display_name,
        "display_name": display_name,
        "description": f"Auto-generated during concept backfill for '{tag_text}'",
        "parents": [],
        "children": [],
        "entity_type": "topic",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "backfill_tag_instances",
        "auto_generated": True,
    }

    result = concept_service.tag_concepts.insert_one(concept_doc)
    logger.info("Created concept '%s' (slug=%s) for legacy tag", display_name, slug)
    return result.inserted_id, True


def update_tag_instance(concept_service: ConceptOnlyTagService, instance: Dict[str, object]) -> Tuple[bool, bool]:
    """Attach a concept_id to a legacy tag instance."""

    tag_text = (
        instance.get("original_text")
        or instance.get("tag")
        or instance.get("tag_text")
    )

    if not tag_text or not isinstance(tag_text, str):
        logger.warning("Skipping tag_instance %s with no usable text", instance.get("_id"))
        return False, False

    concept_id, concept_created = ensure_concept(concept_service, tag_text)

    normalized_tag = tag_text.lower().strip()
    set_ops: Dict[str, object] = {"concept_id": concept_id}

    if not instance.get("original_text"):
        set_ops["original_text"] = tag_text

    if not instance.get("tag_text") or instance.get("tag_text") != normalized_tag:
        set_ops["tag_text"] = normalized_tag

    if "tag_type" not in instance:
        set_ops["tag_type"] = "manual"

    if "source" not in instance:
        set_ops["source"] = "backfill_migration"

    set_ops["updated_at"] = datetime.now(timezone.utc).isoformat()

    update_doc: Dict[str, Dict[str, object]] = {"$set": set_ops}

    unset_ops: Dict[str, int] = {}
    if "tag" in instance:
        unset_ops["tag"] = 1
    if unset_ops:
        update_doc["$unset"] = unset_ops

    result = concept_service.tag_instances.update_one({"_id": instance["_id"]}, update_doc)
    if result.modified_count:
        logger.debug("Updated tag_instance %s", instance["_id"])
        return True, concept_created

    return False, concept_created


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    concept_service = ConceptOnlyTagService()

    legacy_filter = {
        "$or": [
            {"concept_id": {"$exists": False}},
            {"concept_id": None},
            {"concept_id": ""},
            {"tag": {"$exists": True}},
        ]
    }

    cursor = concept_service.tag_instances.find(legacy_filter)

    total = 0
    updated = 0
    concepts_created = 0
    for instance in cursor:
        total += 1
        changed, concept_created = update_tag_instance(concept_service, instance)
        if changed:
            updated += 1
        if concept_created:
            concepts_created += 1

    logger.info(
        "Backfill complete. Total examined=%s, updated=%s, concepts_created=%s",
        total,
        updated,
        concepts_created,
    )


if __name__ == "__main__":
    main()
