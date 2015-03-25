import imghdr
from PIL import Image
import cStringIO
import requests
from .crop_image_obj import crop_image_obj
import urllib
import logging

def _create_cache_image_content(cache_image_api, image_url, content, mode):
    # detect the file type
    ext = imghdr.what('temp', content)
    temp = cStringIO.StringIO(content)
    temp.seek(0)
    im = Image.open(temp)

    out = cStringIO.StringIO()
    im.save(out, format='png')
    out.seek(0)
 
    if mode:
        out = cStringIO.StringIO(crop_image_obj(out, mode))
    
    data = requests.post(
        cache_image_api,
        { 'url': image_url },
        files = {
            'file': out
        }
    ).json()
    return data


def create_cache_image(cache_image_api, image_url, mode = None):
    data = {'url': image_url}

    resp = None
    if not mode:
        # try cache directly
        url = cache_image_api + "?" + urllib.urlencode(data)
        resp = requests.get(url).json()

    if not resp or 'error' in resp:
        # if cache image failed, try to download image from client side
        # it can solve some error that server cannot download / transform
        # image cause by appengine itself

        logging.error(str(resp))

        content = requests.get(image_url).content

        resp = _create_cache_image_content(cache_image_api, image_url, content, mode)

    assert 'url' in resp, resp
    return resp['url']
