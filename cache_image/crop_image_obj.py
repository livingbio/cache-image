from PIL import Image, ImageFilter, ImageEnhance
import sys
import io
import urllib2
import StringIO

def find_window(pix, w, h):
    x1 = w - 1
    y1 = h - 1
    x2 = 0
    y2 = 0
    for y in range(h):
        for x in range(w):
            if pix[x, y] > 0:
                if x < x1:
                    x1 = x
                if x > x2:
                    x2 = x
                if y < y1:
                    y1 = y
                if y > y2:
                    y2 = y
    if x1 > x2:
        (x1, x2) = (x2, x1)
    if y1 > y2:
        (y1, y2) = (y2, y1)
    return (x1, y1, x2 + 1, y2 + 1)

def blank_row(pix, w, h, y, window_w):
    if sum([pix[x, y] / 255 for x in range(w)]) * 6 >= window_w:
        return False
    return True

def blank_col(pix, w, h, x, window_h):
    if sum([pix[x, y] / 255 for y in range(h)]) * 6 >= window_h:
        return False
    return True

def landscape_stretch(image):
    return image

def portrait_stretch(image):
    margin_rate = 10
    sys.stderr.write("Portrair Stretch\n")
    (w, h) = image.size
    new_w = h
    new_h = h
    sys.stderr.write("From (%d,%d) to (%d,%d)\n" % (w, h, new_w, new_h))

    margin = w / margin_rate
    new_margin = (new_w - w) / 2 + margin

    left = image.crop((0, 0, margin, h))
    right = image.crop((w - margin, 0, w, h))
    center = image.crop((margin, 0, w - margin, h))
    (cw, ch) = center.size
    sys.stderr.write("Center from (%d,%d) to (%d,%d)\n" % (cw, ch, (new_w - 2 * new_margin), h))

    left = left.resize((new_margin, h), Image.ANTIALIAS)
    right = right.resize((new_margin + 1, h), Image.ANTIALIAS)

    img_out = Image.new(image.mode, (new_w, new_h))
    img_out.paste(left, (0, 0, new_margin, h))
    img_out.paste(center, (new_margin, 0, new_margin + cw, h))
    img_out.paste(right, (new_w - new_margin - 1, 0, new_w, h))

    (w, h) = img_out.size
    sys.stderr.write("New (%d,%d)\n" % (w, h))
    return img_out

def image_stretch(image):
    (w, h) = image.size
    if w > h:
        return landscape_stretch(image)
    elif w < h:
        return portrait_stretch(image)
    return image

def find_boundary(image, mode):
    (w, h) = image.size
    pix = image.load()
    window = find_window(pix, w, h)

    (x1, y1, x2, y2) = window
    for y in range(y1, y2):
        if blank_row(pix, w, h, y, x2 - x1):
            y1 = y
        else:
            break

    if mode == "landscape" or mode == "both":
        for y in range(y1, y2):
            if blank_row(pix, w, h, y, x2 - x1):
                y1 = y
            else:
                break
        for y in reversed(range(y1, y2)):
            if blank_row(pix, w, h, y, x2 - x1):
                y2 = y
            else:
                break
    else:
        y1 = 0
        y2 = h - 1


    if mode == "portrait" or mode == "both":
        for x in range(x1, x2):
            if blank_col(pix, w, h, x, y2 - y1):
                x1 = x
            else:
                break
        for x in reversed(range(x1, x2)):
            if blank_col(pix, w, h, x, y2 - y1):
                x2 = x
            else:
                break
    else:
        x1 = 0
        x2 = w - 1
    if x1 >= x2 or y1 >= y2:
        return window
    return (x1, y1, x2 + 1, y2 + 1)

def print_image(image):
    (w, h) = image.size
    pix = image.load()
    for y in range(h):
        for x in range(w):
            sys.stdout.write("%r " % pix[x, y])
        sys.stdout.write("\n")

def fit_size(w, h, x1, y1, x2, y2):
    new_w = x2 - x1
    new_h = y2 - y1
    if new_w < new_h:
        x1 -= (new_h - new_w) / 2
        x2 = x1 + (new_h)
    elif new_w > new_h:
        y1 -= (new_w - new_h) / 2
        y2 = y1 + (new_w)
    if x1 < 0:
        x2 += -x1
        x1 = 0
    if y1 < 0:
        y2 += -y1
        y1 = 0
    if x2 >= w:
        x1 -= (x2 - w)
        x2 = w
    if y2 >= h:
        y1 -= (y2 - h)
        y2 = h
    x1 = max(x1, 0)
    y1 = max(y1, 0)
    x2 = min(x2, w)
    y2 = min(y2, h)
    return (x1, y1, x2, y2)
    #   Fit to a square.
    new_w = x2 - x1
    new_h = y2 - y1
    if new_h < new_w:
        x1 += (new_w - new_h) / 2
        x2 = x1 + new_h
    elif new_w < new_h:
        y1 += (new_h - new_w) / 2
        y2 = y1 + new_w
    return (x1, y1, x2, y2)

#   mode = both:        Remove top, bottom, left, right blanks.
#   mode = portrait:    Remove left and right blanks.
#   mode = landscape:   Remove top and bottom blanks.
def crop_image_obj(filename, mode="landscape", contrast=1.0):
    if hasattr(filename, 'read'):
        # check if it is a buffer like object
        image = Image.open(filename)
    elif filename[0:4] == 'http':
        fd = urllib2.urlopen(filename)
        image = Image.open(io.BytesIO(fd.read()))
    else:
        image = Image.open(filename)
    scale = 16
    edges = image.filter(ImageFilter.FIND_EDGES).resize((scale, scale), Image.ANTIALIAS)
    enh = ImageEnhance.Contrast(edges)
    edges = enh.enhance(1000)
    edges = edges.convert("1")
    (x1, y1, x2, y2) = find_boundary(edges, mode)
    sys.stderr.write("%d %d %d %d - " % (x1, y1, x2, y2))
    (w, h) = image.size
    (x1, y1, x2, y2) = fit_size(
        w, h,
        x1 * w / scale, y1 * h / scale,
        x2 * w / scale, y2 * h / scale)

    sys.stderr.write("%d %d %d %d\n" % (x1, y1, x2, y2))
    output = StringIO.StringIO()
    out_img = image.crop((x1, y1, x2, y2))
    out_img = image_stretch(out_img)

    enh = ImageEnhance.Contrast(out_img)
    out_img = enh.enhance(contrast)

    out_img.save(output, format="JPEG")
    output.flush()
    output.seek(0)
    return output

def preview(filename):
    for mode in ("both", "portrait", "landscape"):
        with open('temp.%s.jpg'%mode, 'wb') as ofile:
            ofile.write(crop_image_obj(filename, mode))

if __name__ == "__main__":
    import clime.now
