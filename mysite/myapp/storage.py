import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage

class S3MediaStorage(S3Boto3Storage):
    """
    S3 storage backend that saves the files locally as well as to S3.
    This allows for a smooth transition from local storage to S3.
    """
    location = settings.AWS_LOCATION if hasattr(settings, 'AWS_LOCATION') else 'media'
    file_overwrite = False
    default_acl = 'public-read'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_storage = FileSystemStorage(location=settings.MEDIA_ROOT)
    
    def save(self, name, content, max_length=None):
        # Save to local storage first
        local_name = self.local_storage.save(name, content)
        
        # Then save to S3
        s3_name = super().save(name, content, max_length)
        
        return s3_name
    
    def url(self, name):
        # Try to get the URL from S3
        try:
            return super().url(name)
        except Exception as e:
            # Fallback to local URL if S3 fails
            try:
                return self.local_storage.url(name)
            except:
                # If all else fails, return a relative URL
                return os.path.join(settings.MEDIA_URL, name) 