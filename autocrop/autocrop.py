from __future__ import print_function

from contextlib import contextmanager
import cv2
import glob
import numpy as np
import argparse
import os
import shutil
import sys

# Internal variables
errors = 0
fixexp = True                 # Flag to fix underexposition
marker = False                # Flag for gamma correct
INPUT_FILETYPES = ['*.jpg', '*.jpeg']
INCREMENT = 0.06
GAMMA_THRES = 0.001 
GAMMA = 0.90
FACE_RATIO = 6
cascPath = 'haarcascade_frontalface_default.xml'

# Define directory change within context
@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)

# Define simple gamma correction fn
def gamma(img, correction):
    img = cv2.pow(img/255.0, correction)
    return np.uint8(img*255)

def main():
    # Create the haar cascade
    faceCascade = cv2.CascadeClassifier(cascPath)

    with cd('../photos/'):
        files_grabbed = []
        for files in INPUT_FILETYPES:
            files_grabbed.extend(glob.glob(files))

        for file in files_grabbed:
            image = cv2.imread(file)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
 
            # Scale the image
            height, width = (image.shape[:2])
            minface = int(np.sqrt(height*height + width*width) / 8)

            # ====== Detect faces in the image ======
            faces = [[]]
            faces = faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(minface, minface),
                flags = cv2.cv.CV_HAAR_FIND_BIGGEST_OBJECT | cv2.cv.CV_HAAR_DO_ROUGH_SEARCH
            )

            # Handle no faces
            if len(faces) == 0: 
                print(' No faces can be detected in file {0}.'.format(str(file)))
                errors += 1
                break

            # Copy to /bkp
            shutil.copy(file, 'bkp')

            # Make padding from probable biggest face
            x, y, w, h = faces[-1]
            pad = h / FACE_RATIO

            # Make sure padding is contained within picture
            while True:  # decreases pad by 6% increments to fit crop into image. Can lead to very small faces.
                if y-2*pad < 0 or y+h+pad > height or int(x-1.5*pad) < 0 or x+w+int(1.5*pad) > width:
                    pad = (1 - INCREMENT) * pad
                else:
                    break

            # Crop the image from the original
            image = image[y-2*pad:y+h+pad, x-1.5*pad:x+w+1.5*pad]

            # Resize the damn thing
            image = cv2.resize(image, (fheight, fwidth), interpolation = cv2.INTER_AREA)

            # ====== Dealing with underexposition ======
            if fixexp == True:
                # Check if under-exposed
                uexp = cv2.calcHist([gray], [0], None, [256], [0,256])

                if sum(uexp[-26:]) < GAMMA_THRES * sum(uexp) :
                    marker = True
                    image = gamma(image, GAMMA)

            # Write cropfile
            cropfilename = '{0}'.format(str(file))
            cv2.imwrite(cropfilename, image)

            # Move files to /crop
            shutil.move(cropfilename, 'crop')

    # Stop and print timer
    print(' {0} files have been cropped'.format(len(files_grabbed) - errors))

def cli():
    # Taken from https://www.saltycrane.com/blog/2009/09/python-optparse-example/
    parser = argparse.ArgumentParser(description='Automatically crops faces from batches of pictures')
    parser.add_argument('-w', '--width', default=500, help='Width of the cropped files in pixels')
    parser.add_argument('-h', '--height', default=500, help='Height of the cropped files in pixels')
    args = parser.parse_args()
    fwidth = args.width
    fheight = args.height

    # if len(args) != 1:
    #     parser.error('wrong number of arguments')

    main()

