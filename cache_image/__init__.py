import imghdr
from PIL import Image
import cStringIO
import requests
from .crop_image_obj import crop_image_obj
import urllib
import logging


class CacheImageAPI(object):
    def __init__(self, cache_image_api):
        self.cache_image_api = cache_image_api

    def _cache_image(self, image_url, a_file=None):
        data = { 'url': image_url }
        if a_file:
            resp = requests.post(
                self.cache_image_api,
                data,
                files = {
                    'file': a_file
                }
            ).json()
        else:
            url = self.cache_image_api + "?" + urllib.urlencode(data)
            resp = requests.get(url).json()

        return resp['url']

    def crop(self, content, mode):
        return crop_image_obj(content, mode)

    def contrast(self, content, contrast):
        output = cStringIO.StringIO()
        out_image = Image.open(content)
        enh = ImageEnhance.Contrast(out_img)
        out_img = enh.enhance(contrast)
        out_img.save(output, format="JPEG")
        output.flush()
        output.seek(0)
        return output

    def convert(self, content, format):
        im = Image.open(content)
        out = cStringIO.StringIO()
        im.save(out, format=format)
        out.seek(0)
        return out

    def cache(self, image_url, content=None, mode=None, contrast=1.0):
        if not content:
            content = cStringIO.StringIO(requests.get(image_url).content)
            content = self.convert(content, 'png')

        if mode:
            content = self.crop(content, mode)

        if contrast != 1.0:
            content = self.contrast(content, contrast)

        return self._cache_image(image_url, content)


