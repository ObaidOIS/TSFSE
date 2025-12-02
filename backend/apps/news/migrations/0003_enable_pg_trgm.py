"""
Migration to enable PostgreSQL pg_trgm extension.

This extension provides:
- SIMILARITY function for fuzzy text matching
- GIN/GiST index support for trigram matching
- Better full-text search capabilities

Author: Obaidulllah
"""

from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):
    """Enable pg_trgm extension for fuzzy search."""

    dependencies = [
        ('news', '0002_seed_categories'),
    ]

    operations = [
        TrigramExtension(),
    ]
