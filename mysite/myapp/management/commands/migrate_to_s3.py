import os
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps
from django.db.models import FileField, ImageField

class Command(BaseCommand):
    help = 'Migrate existing media files to S3 and update database records'

    def handle(self, *args, **options):
        # Check if AWS credentials are set
        if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.AWS_STORAGE_BUCKET_NAME):
            self.stdout.write(self.style.ERROR('AWS credentials not set. Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_STORAGE_BUCKET_NAME.'))
            return
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
        )
        
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        
        # Verify bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            self.stdout.write(self.style.SUCCESS(f'Connected to bucket: {bucket_name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to bucket {bucket_name}: {str(e)}'))
            return
        
        # Find all models with file fields
        models_with_file_fields = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                file_fields = []
                for field in model._meta.fields:
                    if isinstance(field, (FileField, ImageField)):
                        file_fields.append(field.name)
                
                if file_fields:
                    models_with_file_fields.append((model, file_fields))
        
        # For each model with file fields, upload files to S3
        for model, fields in models_with_file_fields:
            self.stdout.write(f'Migrating {model.__name__} files...')
            
            # Get all objects with non-empty file fields
            filter_condition = {}
            for field in fields:
                filter_condition[f'{field}__isnull'] = False
            
            queryset = model.objects.filter(**filter_condition)
            
            for obj in queryset:
                for field_name in fields:
                    file_field = getattr(obj, field_name)
                    
                    if not file_field or not file_field.name:
                        continue
                    
                    file_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
                    
                    # Check if the file exists locally
                    if not os.path.exists(file_path):
                        self.stdout.write(self.style.WARNING(f'File not found: {file_path}'))
                        continue
                    
                    # Construct S3 key (path in the bucket)
                    s3_key = f'{settings.AWS_LOCATION}/{file_field.name}' if hasattr(settings, 'AWS_LOCATION') else file_field.name
                    
                    try:
                        # Upload file to S3
                        self.stdout.write(f'  Uploading {file_field.name} to S3...')
                        with open(file_path, 'rb') as file_data:
                            s3_client.upload_fileobj(
                                file_data,
                                bucket_name,
                                s3_key,
                                ExtraArgs={
                                    'ACL': 'public-read',
                                    'ContentType': file_field.file.content_type if hasattr(file_field.file, 'content_type') else 'application/octet-stream'
                                }
                            )
                            
                        # No need to update database records since Django-storages will handle URL generation
                        self.stdout.write(self.style.SUCCESS(f'  Uploaded {file_field.name} to S3'))
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Error uploading {file_field.name} to S3: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('Media migration complete!'))
        self.stdout.write(self.style.WARNING('Note: The URLs in your database will now be automatically handled by Django-storages.')) 