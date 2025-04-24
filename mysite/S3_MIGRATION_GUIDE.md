# Media Files Migration to S3 Guide

This guide explains how to migrate your media files from local storage to Amazon S3 while ensuring database links remain functional.

## Prerequisites

1. An AWS account
2. An S3 bucket created with public access enabled
3. AWS access key and secret key with S3 permissions

## Configuration Steps

### 1. Set Environment Variables

Add these environment variables to your system or .env file:

```bash
# Required
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your-bucket-name

# Optional
AWS_DEFAULT_REGION=us-east-1  # Change to your preferred region
```

### 2. Check S3 Configuration

Run the following command to check if your S3 configuration is working:

```bash
python manage.py check_s3_config
```

This will verify that:
- Your AWS credentials are properly set
- The S3 bucket exists and is accessible
- Django can write to the bucket
- Your storage configuration is correct

### 3. Migrate Existing Media Files to S3

Run the following command to upload all existing media files to S3:

```bash
python manage.py migrate_to_s3
```

This command will:
1. Find all models with file/image fields
2. Upload all referenced files to S3
3. The database won't be modified because Django-storages handles URL generation automatically

### 4. Update Any Hardcoded Media URLs in the Database (if needed)

If your application directly stores media URLs in the database (not using model file fields), run:

```bash
# First do a dry run to see what would be changed
python manage.py update_media_urls --dry-run

# Then apply the changes if everything looks correct
python manage.py update_media_urls
```

## How It Works

The migration implementation includes:

1. **Custom Storage Class**: `S3MediaStorage` that:
   - Saves files to both S3 and local storage
   - Falls back to local storage if S3 is unavailable
   - Ensures a smooth transition without breaking existing links

2. **Automatic URL Handling**: Django generates URLs automatically based on the storage backend,
   so links will work without changing your code.

3. **URL Format**: Files will be served from:
   `https://{bucket-name}.s3.amazonaws.com/media/{file-path}`

## Troubleshooting

If you encounter issues:

1. **Files not appearing on S3**:
   - Check AWS permissions
   - Verify the bucket exists and is accessible
   - Run `python manage.py check_s3_config` to diagnose

2. **Files not loading in your application**:
   - Check browser console for CORS errors
   - Make sure the S3 bucket has proper CORS configuration
   - Verify that the URLs are correctly formed

3. **Fallback to local storage**:
   - If S3 is temporarily unavailable, the system will fallback to local storage
   - Files will continue to be saved locally as a backup

## Docker Configuration

The Docker configuration has been updated to include:

1. AWS environment variables in the web service
2. A media file sync to S3 in the s3sync service
3. Local volume mounts to ensure files are accessible

To apply these changes, run:

```bash
docker-compose down
docker-compose up --build -d
``` 