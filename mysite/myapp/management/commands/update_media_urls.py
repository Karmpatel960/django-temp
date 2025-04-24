import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

class Command(BaseCommand):
    help = 'Update hardcoded media URLs in the database to S3 URLs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--old-prefix',
            default='/media/',
            help='The old URL prefix to replace (default: /media/)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without making changes'
        )

    def handle(self, *args, **options):
        # Check if AWS credentials are set
        if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.AWS_STORAGE_BUCKET_NAME):
            self.stdout.write(self.style.ERROR('AWS credentials not set. Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_STORAGE_BUCKET_NAME.'))
            return
        
        old_prefix = options['old_prefix']
        dry_run = options['dry_run']
        
        # Construct the new S3 URL prefix
        s3_domain = settings.AWS_S3_CUSTOM_DOMAIN
        s3_location = getattr(settings, 'AWS_LOCATION', 'media')
        new_prefix = f'https://{s3_domain}/{s3_location}/'
        
        self.stdout.write(self.style.SUCCESS(f'Replacing {old_prefix} with {new_prefix}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE: No changes will be made.'))
        
        # Get all tables in the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            # Skip Django internal tables and migrations
            if table.startswith('django_') or table.startswith('auth_') or table.startswith('sqlite_'):
                continue
                
            self.stdout.write(f'Checking table: {table}')
            
            # Get columns for this table
            with connection.cursor() as cursor:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [row[1] for row in cursor.fetchall()]
            
            # Look for text and varchar columns that might contain URLs
            text_columns = []
            for column in columns:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT typeof({column}) FROM {table} LIMIT 1;")
                    result = cursor.fetchone()
                    if result and result[0].lower() in ('text', 'varchar', 'char', 'string'):
                        text_columns.append(column)
            
            if not text_columns:
                continue
                
            self.stdout.write(f'  Found text columns: {", ".join(text_columns)}')
            
            # Check each text column for the old prefix
            for column in text_columns:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} LIKE ?;", [f'%{old_prefix}%'])
                    count = cursor.fetchone()[0]
                
                if count == 0:
                    continue
                    
                self.stdout.write(f'  Found {count} rows with potential media URLs in {column}')
                
                # Update the URLs
                if not dry_run:
                    with connection.cursor() as cursor:
                        cursor.execute(f"""
                            UPDATE {table} 
                            SET {column} = replace({column}, ?, ?)
                            WHERE {column} LIKE ?;
                        """, [old_prefix, new_prefix, f'%{old_prefix}%'])
                        
                    self.stdout.write(self.style.SUCCESS(f'  Updated {count} rows in {table}.{column}'))
        
        self.stdout.write(self.style.SUCCESS('URL migration complete!'))
        if dry_run:
            self.stdout.write(self.style.WARNING('This was a dry run. No changes were made. Run again without --dry-run to apply changes.')) 