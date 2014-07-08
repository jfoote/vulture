import boto, os, gzip
from functools import partial

from vlib.analyzers.tools import call_for_each_analysis

def upload_html(filename, bucket):
    key = bucket.new_key(filename)
    key.set_metadata('Content-Type', 'text/html')
    thisdir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join("%s/%s" % (thisdir, filename))
    key.set_contents_from_filename(path)
    key.set_canned_acl("public-read")

def publish(analysis_dir, pub_list=[], buglist=[]):
    bucket = boto.connect_s3().get_bucket("vulture88")

    # note that order is important below:
    #   1. create new key
    #   2. set content type
    #   3. set contents (uploads the key)
    #   4. set ACL policy

    # publish HTML
    if (not pub_list) or ('html' in pub_list):
        upload_html("index.html", bucket)
        upload_html("bug.html", bucket)
        upload_html("jquery.dynatable.js")
        upload_html("jquery.dynatable.css")

    # publish analysis data
    # gzip/upload summary json file
    if (not pub_list) or ('summary' in pub_list):
        upload_json("%s/summary.json" % analysis_dir, "summary.json", bucket)

    # gzip/upload analysis for each bug
    if (not pub_list) or ('bugs' in pub_list):
        call_for_each_analysis(analysis_dir, partial(upload_analysis, bucket), None, buglist)

def upload_analysis(bucket, bugdir):
    bug_id_str = bugdir.split("/")[-1]

    upload_json("%s/analysis.json" % bugdir, "%s/analysis.json" % bug_id_str, bucket)
    #print "json for %s" % bugdir
    #upload_json("%s/trace.json" % bugdir, "%s/trace.json" % bug_id_str, bucket)

def upload_json(src, dst_key, bucket):
    json_path = os.path.join(src)
    gzip_path = "/tmp/%s" % dst_key.replace("/","-") # will be included in gzip header  :|
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

