"""
Data migration to seed initial categories.

Creates the predefined news categories as specified in requirements:
- Economy
- Market (Commodities)
- Health
- Technology
- Industry

Author: Obaidulllah
"""

from django.db import migrations


def create_categories(apps, schema_editor):
    """
    Create initial news categories.
    """
    Category = apps.get_model('news', 'Category')
    
    categories = [
        {
            'name': 'economy',
            'display_name': 'Economy',
            'description': 'Economic news including GDP, inflation, monetary policy, fiscal policy, and macroeconomic trends.',
            'keywords': [
                'economy', 'economic', 'gdp', 'inflation', 'recession', 'growth',
                'federal reserve', 'fed', 'central bank', 'monetary policy',
                'fiscal policy', 'budget', 'employment', 'unemployment',
                'interest rate', 'treasury'
            ]
        },
        {
            'name': 'market',
            'display_name': 'Market (Commodities)',
            'description': 'Market news covering stocks, commodities, trading, forex, and financial markets.',
            'keywords': [
                'market', 'stock', 'stocks', 'commodity', 'commodities',
                'oil', 'gold', 'trading', 'wall street', 'nasdaq',
                's&p 500', 'dow jones', 'futures', 'forex', 'currency',
                'crypto', 'bitcoin', 'etf', 'ipo', 'earnings'
            ]
        },
        {
            'name': 'health',
            'display_name': 'Health',
            'description': 'Healthcare news including medicine, pharmaceuticals, public health, and medical research.',
            'keywords': [
                'health', 'healthcare', 'medical', 'medicine', 'hospital',
                'disease', 'treatment', 'vaccine', 'pharmaceutical', 'drug',
                'fda', 'clinical trial', 'cancer', 'pandemic', 'biotech'
            ]
        },
        {
            'name': 'technology',
            'display_name': 'Technology',
            'description': 'Technology news covering software, hardware, AI, cybersecurity, and tech industry.',
            'keywords': [
                'technology', 'tech', 'software', 'hardware', 'ai',
                'artificial intelligence', 'machine learning', 'cloud',
                'cybersecurity', 'apple', 'google', 'microsoft', 'meta',
                'startup', 'semiconductor', 'chip', '5g', 'blockchain'
            ]
        },
        {
            'name': 'industry',
            'display_name': 'Industry',
            'description': 'Industry news covering manufacturing, automotive, aerospace, energy, and business sectors.',
            'keywords': [
                'industry', 'industrial', 'manufacturing', 'automotive',
                'auto', 'ev', 'electric vehicle', 'aerospace', 'aviation',
                'shipping', 'supply chain', 'energy', 'renewable', 'solar',
                'mining', 'construction', 'real estate'
            ]
        },
    ]
    
    for cat_data in categories:
        Category.objects.create(**cat_data)


def remove_categories(apps, schema_editor):
    """
    Remove categories (reverse migration).
    """
    Category = apps.get_model('news', 'Category')
    Category.objects.all().delete()


class Migration(migrations.Migration):
    """
    Data migration for initial categories.
    """
    
    dependencies = [
        ('news', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(create_categories, remove_categories),
    ]
