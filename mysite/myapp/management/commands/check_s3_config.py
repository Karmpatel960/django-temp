import os
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Check S3 configuration and connection'

    def handle(self, *args, **options):
        # Check if AWS credentials are set
        if not settings.AWS_ACCESS_KEY_ID:
            self.stdout.write(self.style.ERROR('AWS_ACCESS_KEY_ID is not set.'))
        else:
            self.stdout.write(self.style.SUCCESS('AWS_ACCESS_KEY_ID is set.'))
            
        if not settings.AWS_SECRET_ACCESS_KEY:
            self.stdout.write(self.style.ERROR('AWS_SECRET_ACCESS_KEY is not set.'))
        else:
            self.stdout.write(self.style.SUCCESS('AWS_SECRET_ACCESS_KEY is set.'))
            
        if not settings.AWS_STORAGE_BUCKET_NAME:
            self.stdout.write(self.style.ERROR('AWS_STORAGE_BUCKET_NAME is not set.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'AWS_STORAGE_BUCKET_NAME is set to: {settings.AWS_STORAGE_BUCKET_NAME}'))
        
        # If credentials are missing, exit early
        if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.AWS_STORAGE_BUCKET_NAME):
            self.stdout.write(self.style.ERROR('Missing AWS credentials. Please set all required environment variables.'))
            return
        
        # Test connection to S3
        try:
            self.stdout.write('Testing connection to S3...')
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
            )
            
            # Try to access the bucket
            s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            self.stdout.write(self.style.SUCCESS(f'Successfully connected to bucket: {settings.AWS_STORAGE_BUCKET_NAME}'))
            
            # List some objects in the bucket
            self.stdout.write('Listing up to 5 objects in the bucket:')
            response = s3_client.list_objects_v2(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                MaxKeys=5
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    self.stdout.write(f"  - {obj['Key']} ({obj['Size']} bytes)")
            else:
                self.stdout.write('  No objects found in the bucket.')
                
            # Check if we can write to the bucket
            self.stdout.write('Testing write access to bucket...')
            test_content = b'This is a test file from django check_s3_config command.'
            s3_client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key='test/s3_config_test.txt',
                Body=test_content,
                ACL='public-read'
            )
            self.stdout.write(self.style.SUCCESS('Successfully wrote test file to bucket.'))
            
            # Get the URL for the test file
            s3_domain = settings.AWS_S3_CUSTOM_DOMAIN
            s3_location = getattr(settings, 'AWS_LOCATION', '')
            if s3_location:
                test_url = f'https://{s3_domain}/{s3_location}/test/s3_config_test.txt'
            else:
                test_url = f'https://{s3_domain}/test/s3_config_test.txt'
                
            self.stdout.write(self.style.SUCCESS(f'Test file URL: {test_url}'))
            
            # Check Django storage configuration
            self.stdout.write('\nChecking Django storage configuration:')
            self.stdout.write(f"DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
            self.stdout.write(f"STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
            self.stdout.write(f"AWS_DEFAULT_ACL: {getattr(settings, 'AWS_DEFAULT_ACL', 'Not set')}")
            self.stdout.write(f"AWS_S3_CUSTOM_DOMAIN: {getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', 'Not set')}")
            self.stdout.write(f"AWS_LOCATION: {getattr(settings, 'AWS_LOCATION', 'Not set')}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to S3: {str(e)}'))
            self.stdout.write(self.style.WARNING('Please check your AWS credentials and network connection.')) 