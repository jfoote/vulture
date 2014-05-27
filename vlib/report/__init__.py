import boto

def publish_report():
    bucket = boto.connect_s3().get_bucket("vulture88")
