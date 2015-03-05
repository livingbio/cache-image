
convert_image_api = 'http://gothic-province-823.appspot.com/api/covert_gs_key'
cache_image_api = 'http://gothic-province-823.appspot.com/api/cache_image_v2'

def _create_cache_image_content(image_url, content):
    ext = imghdr.what('temp', content)
    temp = cStringIO.StringIO(content)
    temp.seek(0)
    im = Image.open(temp)

    out = cStringIO.StringIO()
    im.save(out, format='png')
    out.seek(0)

    data = requests.post(cache_image_api,
        {'url': image_url},
        files = {
            'file': content
        }
    ).json()
    return data


def create_cache_image(convert_image_api, cache_image_api,image_url):
    data = {'url': image_url}
    url = cache_image_api + "?" + urllib.urlencode(data)
    data = requests.get(url).json()

    if 'error' in data:
        # if cache image failed, try to download image from client side
        # it can solve some error that server cannot download / transform
        # image cause by appengine itself

        logging.error(str(data))

        content = requests.get(image_url).content

        data = _create_cache_image_content(image_url, content)

    assert 'url' in data, data
    return data['url']
