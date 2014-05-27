import boto, os, gzip

def publish(analysis_dir):
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

    #return # TODO delete this!

    # publish analysis data
    # gzip big json file
    json_path = os.path.join("%s/summary.json" % analysis_dir)
    gzip_path = "summary.json.gz" # will be included in gzip header  :|
    try:
        gzfile = gzip.open(gzip_path, 'wb')
        gzfile.write(open(json_path, 'rt').read())
        gzfile.flush()
        gzfile.close()

        key = bucket.new_key("summary.json")
        key.set_metadata('Content-Type', 'application/json')
        # see http://stackoverflow.com/questions/477816/what-is-the-correct-json-content-type
        key.set_metadata('Content-Encoding', 'gzip')
        key.set_contents_from_filename(gzip_path)
        key.set_canned_acl("public-read")
    finally:
        if os.path.exists(gzip_path):
            os.remove(gzip_path)

