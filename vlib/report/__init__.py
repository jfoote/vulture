import boto, os, gzip

from vlib.analyzers.tools import call_for_each_bug

def publish(analysis_dir, bug_dir, html_only=False):
    bucket = boto.connect_s3().get_bucket("vulture88")

    # note that order is important below:
    #   1. create new key
    #   2. set content type
    #   3. set contents (uploads the key)
    #   4. set ACL policy

    # publish HTML
    key = bucket.new_key("index.html")
    key.set_metadata('Content-Type', 'text/html')

    thisdir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join("%s/index.html" % thisdir)
    key.set_contents_from_filename(path)
    key.set_canned_acl("public-read")

    if html_only: # TODO; replace this option with something more flexible
        return

    # publish analysis data
    # gzip/upload summary json file
    upload_json("%s/summary.json" % analysis_dir, "summary.json", bucket)

    # gzip/upload analysis for each bug
    call_for_each_bug(bug_dir, partial(upload_analysis, bucket), 5)

def upload_analysis(bucket, bugdir):
    upload_json("%s/vulture.json", "%s/vulture.json", bucket)

def upload_json(src, dst_key, bucket)
    json_path = os.path.join(src)
    gzip_path = "/tmp/%s" % src  # will be included in gzip header  :|
    try:
        gzfile = gzip.open(gzip_path, 'wb')
        gzfile.write(open(json_path, 'rt').read())
        gzfile.flush()
        gzfile.close()

        key = bucket.new_key(dst_key)
        key.set_metadata('Content-Type', 'application/json')
        # see http://stackoverflow.com/questions/477816/what-is-the-correct-json-content-type
        key.set_metadata('Content-Encoding', 'gzip')
        key.set_contents_from_filename(gzip_path)
        key.set_canned_acl("public-read")
    finally:
        if os.path.exists(gzip_path):
            os.remove(gzip_path)

