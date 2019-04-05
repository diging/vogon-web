"""
Views related to Amazon services.
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required

import base64
from hashlib import sha1
import hmac
import time
import urllib.request, urllib.parse, urllib.error
from urllib.parse import urlparse


@login_required
def sign_s3(request):
    """
    Genaration of a temporary signtaure using AWS secret key and access key.
    https://devcenter.heroku.com/articles/s3-upload-python

    This is used for user profile images.
    """

    if request.method == 'GET':
        object_name = urllib.parse.quote_plus(request.GET.get('file_name'))
        mime_type = request.GET.get('file_type')

        secondsPerDay = 24*60*60
        expires = int(time.time() + secondsPerDay)
        amz_headers = "x-amz-acl:public-read"

        string_to_sign = "PUT\n\n%s\n%d\n%s\n/%s/%s" % (mime_type, expires, amz_headers, settings.S3_BUCKET, object_name)

        encodedSecretKey = settings.AWS_SECRET_KEY.encode()
        encodedString = string_to_sign.encode()
        h = hmac.new(encodedSecretKey, encodedString, sha1)
        hDigest = h.digest()
        signature = base64.b64encode(hDigest).strip()
        signature = urllib.parse.quote_plus(signature)
        url = 'https://%s.s3.amazonaws.com/%s' % (settings.S3_BUCKET, object_name)

        # TODO: can we use the built-in Django JsonResponse for this?
        return JsonResponse({
            'signed_request': '%s?AWSAccessKeyId=%s&Expires=%s&Signature=%s' % (url, settings.AWS_ACCESS_KEY, expires, signature),
            'url': url,
        })
