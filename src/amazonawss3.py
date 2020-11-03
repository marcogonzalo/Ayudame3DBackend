import os, boto3, botocore

s3 = boto3.client(
   "s3",
   aws_access_key_id=os.environ.get('S3_ID'),
   aws_secret_access_key=os.environ.get('S3_SECRET')
)

def upload_file_to_s3(file, bucket_name, acl="public-read"):
    s3_location = 'https://{}.s3.amazonaws.com/'.format(bucket_name)

    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        print("Something Happened: ", e)
        return e

    return "{}{}".format(s3_location, file.filename)