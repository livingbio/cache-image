import subprocess

for i in range(1, 9):
    cmd = "python cache_image/crop_image_obj.py test/%d.jpg landscape > output/%d.jpg" % (i, i)
    print cmd
    subprocess.call(cmd, shell=True)

