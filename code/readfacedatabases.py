"""The aim of this script is to read the multi pie dataset """

import scipy.io
import numpy as np
import matplotlib.pyplot as plt
import glob
import cPickle as pickle
import os
import cv2
import facedetection
import fnmatch

import matplotlib.image as io
# from skimage import io
# from skimage import color
from skimage.transform import resize

from common import *

SMALL_SIZE = ((40, 30))

# TODO: make some general things with the path in order to make it work easily between
# lab machine and local
def equalizeImg(x):
  # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
  # return clahe.apply(img)
  return cv2.equalizeHist(x)

def equalizeFromFloat(x):
  x = x * 255
  x = np.asarray(x, dtype='uint8')
  y = x.reshape(SMALL_SIZE)
  y =  equalizeImg(y).reshape(-1)
  return y / 255.0

def equalizePIE():
  imgs, labels = readMultiPIE()

  imgs = np.array(map(lambda x: equalizeFromFloat(x), imgs))

  return imgs, labels

def equalizeKanade(big=False):
  data, labels = readKanade(big=big, equalize=False)

  if big:
      fileName = 'equalized_kanade_big.pickle'
  else:
      fileName = 'equalized_kanade_small.pickle'


  data = np.array(map(lambda x: equalizeFromFloat(x), data))

  with open(fileName, "wb") as f:
    pickle.dump(data, f)
    pickle.dump(labels, f)

# TODO: add equalize argument
def readMultiPIE(show=False):
  PATH = '/data/mcr10/Multi-PIE_Aligned/A_MultiPIE.mat'
  # PATH = '/home/aela/uni/project/Multi-PIE_Aligned/A_MultiPIE.mat'

  mat = scipy.io.loadmat(PATH)
  data = mat['a_multipie']
  # For all the subjects
  imgs = []
  labels = []
  for subject in xrange(147):
    for pose in xrange(5):
      for expression in xrange(6): # ['Neutral','Surprise','Squint','Smile','Disgust','Scream']
        for illumination in xrange(5):
            image = np.squeeze(data[subject,pose,expression,illumination,:])
            image = image.reshape(30,40).T
            if show:
              plt.imshow(image, cmap=plt.cm.gray)
              plt.show()
            imgs += [image.reshape(-1)]
            labels += [expression]

  return np.array(imgs), labelsToVectors(labels, 6)


def readMultiPieDifferentIlluminations(illuminationTrain, show=False):
  PATH = '/data/mcr10/Multi-PIE_Aligned/A_MultiPIE.mat'
  # PATH = '/home/aela/uni/project/Multi-PIE_Aligned/A_MultiPIE.mat'
  mat = scipy.io.loadmat(PATH)
  data = mat['a_multipie']
  # For all the subjects
  imgsTrain = []
  labelsTrain = []

  imgsTest = []
  labelsTest = []

  for subject in xrange(147):
    for pose in xrange(5):
      for expression in xrange(6): # ['Neutral','Surprise','Squint','Smile','Disgust','Scream']
        for illumination in xrange(5):
            image = np.squeeze(data[subject,pose,expression,illumination,:])
            image = image.reshape(30,40).T
            if show:
              plt.imshow(image, cmap=plt.cm.gray)
              plt.show()
            if illumination in illuminationTrain:
              imgsTrain += [image.reshape(-1)]
              labelsTrain += [expression]
            else:
              imgsTest += [image.reshape(-1)]
              labelsTest += [expression]

  # Let us shuffle some things
  imgsTrain = np.array(imgsTrain)
  labelsTrain = np.array(labelsTrain)

  imgsTest = np.array(imgsTest)
  labelsTest = np.array(labelsTest)

  imgsTrain, labelsTrain = shuffle(imgsTrain, labelsTrain)
  imgsTest, labelsTest = shuffle(imgsTest, labelsTest)

  return (imgsTrain, labelsToVectors(labelsTrain, 6),
          imgsTest,  labelsToVectors(labelsTest, 6))


def readMultiPIESubjects():
  PATH = '/data/mcr10/Multi-PIE_Aligned/A_MultiPIE.mat'
  # PATH = '/home/aela/uni/project/Multi-PIE_Aligned/A_MultiPIE.mat'

  mat = scipy.io.loadmat(PATH)
  data = mat['a_multipie']
  subjectsToImgs = {}
  # For all the subjects

  for subject in xrange(147):
    subjectsToImgs[subject] = []
    for pose in xrange(5):
      for expression in xrange(6): # ['Neutral','Surprise','Squint','Smile','Disgust','Scream']
        for illumination in xrange(5):
            image = np.squeeze(data[subject,pose,expression,illumination,:])
            image = image.reshape(30,40).T
            image = image.reshape(-1)

            subjectsToImgs[subject] += [image]

  return subjectsToImgs


def readMultiPIEEmotions():
  PATH = '/data/mcr10/Multi-PIE_Aligned/A_MultiPIE.mat'
  # PATH = '/home/aela/uni/project/Multi-PIE_Aligned/A_MultiPIE.mat'

  mat = scipy.io.loadmat(PATH)
  data = mat['a_multipie']
  emotionToImages = {}
  # For all the subjects

  for expression in xrange(6):
    emotionToImages[expression] = []

  for subject in xrange(147):
    for pose in xrange(5):
      for expression in xrange(6): # ['Neutral','Surprise','Squint','Smile','Disgust','Scream']
        for illumination in xrange(5):
            image = np.squeeze(data[subject,pose,expression,illumination,:])
            image = image.reshape(30,40).T
            image = image.reshape(-1)

            emotionToImages[expression] += [image]

  print emotionToImages
  return emotionToImages

def readKanade(big=False, folds=None, equalize=False):
  if not equalize:
    if big:
      files = glob.glob('kanade_150*.pickle')
    else:
      files = glob.glob('kanade_f*.pickle')

    if not folds:
      folds = range(1, 6)

    # Read the data from them. Sort out the files that do not have
    # the folds that we want
    # TODO: do this better (with regex in the file name)
    # DO not reply on the order returned
    files = [ files[x -1] for x in folds]

    data = np.array([])
    labels = np.array([])

    # TODO: do proper CV in which you use 4 folds for training and one for testing
    # at that time
    dataFolds = []
    labelFolds = []
    for filename in files:
      with open(filename, "rb") as  f:
        # Sort out the labels from the data
        # TODO: run the readKanade again tomorrow and change these idnices here
        dataAndLabels = pickle.load(f)
        foldData = dataAndLabels[:, 0:-1]
        print "foldData.shape"
        print foldData.shape
        foldLabels = dataAndLabels[:,-1]
        dataFolds.append(foldData)
        foldLabels = np.array(map(int, foldLabels))

        vectorLabels = labelsToVectors(foldLabels -1, 7)
        labelFolds.append(vectorLabels)

        print "foldLabels.shape"
        print vectorLabels.shape


    data = np.vstack(tuple(dataFolds))
    labels = np.vstack(tuple(labelFolds))
  else:
    if big:
      fileName = 'equalized_kanade_big.pickle'
    else:
      fileName = 'equalized_kanade_small.pickle'

    # If there are no files with the equalized data, make one now
    if not os.path.exists(fileName):
      equalizeKanade(big)

    with open(fileName, "rb") as  f:
      data = pickle.load(f)
      labels = pickle.load(f)

  # For now: check that the data is binary
  assert np.all(np.min(data, axis=1) >= 0.0) and np.all(np.max(data, axis=1) < 1.0 + 1e-8)

  return data, labels


# TODO: get big, small as argument in order to be able to fit the resizing
def readCroppedYale(equalize):
  PATH = "/data/mcr10/yaleb/CroppedYale"
  # PATH = "/home/aela/uni/project/CroppedYale"

  imageFiles = [os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(PATH)
    for f in fnmatch.filter(files, '*.pgm')]

  # Filter out the ones that containt "amyes bient"
  imageFiles = [ x for x in imageFiles if not "Ambient" in x]

  images = []
  for f in imageFiles:
    img = cv2.imread(f, 0)

    if equalize:
      img = equalizeImg(img)

    img = resize(img, SMALL_SIZE)

    images += [img.reshape(-1)]

  return np.array(images)

def readCroppedYaleSubjects(equalize=False, show=False):
  PATH = "/data/mcr10/yaleb/CroppedYale"
  # PATH = "/home/aela/uni/project/CroppedYale"

  subject = 0
  subjectsToImgs = {}
  for subjectImagePath in os.listdir(PATH):
    print "subjectImagePath"
    print subjectImagePath


    fullSubjectPath = os.path.join(PATH, subjectImagePath)
    imageFiles = os.listdir(fullSubjectPath)
    imageFiles = [os.path.join(fullSubjectPath, f) for f in imageFiles]

    # Filter out the files which are not image files
    imageFiles = fnmatch.filter(imageFiles, '*.pgm')

    # Remove the ambient files
    imageFiles = [ x for x in imageFiles if not "Ambient" in x]

    print imageFiles

    images = []
    for f in imageFiles:
      img = cv2.imread(f, 0)
      print f
      print img.shape


      if equalize:
        img = equalizeImg(img)

      img = resize(img, SMALL_SIZE)

      if show:
        plt.imshow(img, cmap=plt.cm.gray)
        plt.show()

      images += [img.reshape(-1)]

    subjectsToImgs[subject] = images
    subject += 1

  return subjectsToImgs



def readAttData(equalize=False):
  PATH = "/data/mcr10/att"
  # PATH = "/home/aela/uni/project/code/pics/cambrdige_pics"

  imageFiles = [os.path.join(dirpath, f)
    for dirpath, dirnames, files in os.walk(PATH)
    for f in fnmatch.filter(files, '*.pgm')]

  images = []
  for f in imageFiles:
    img = cv2.imread(f, 0)
    if equalize:
      img = equalizeImg(img)
    img = resize(img, SMALL_SIZE)
    images += [img.reshape(-1)]


  return np.array(images)

def readCropEqualize(path, extension, doRecognition, equalize=False,
                     isColoured=False):
  dirforres = "detection-cropped"
  pathForCropped = os.path.join(path, dirforres)

  if doRecognition:
    if not os.path.exists(pathForCropped):
      os.makedirs(pathForCropped)

    imageFiles = [(os.path.join(dirpath, f), f)
      for dirpath, dirnames, files in os.walk(path)
      for f in fnmatch.filter(files, '*.' + extension)]

    images = []

    for fullPath, shortPath in imageFiles:
      # Do not do this for already cropped images
      if pathForCropped in fullPath:
        continue

      print fullPath
      img = cv2.imread(fullPath, 0)

      if equalize:
        img = equalizeImg(img)

      face = facedetection.cropFace(img)
      if not face == None:
        # Only do the resizing once you are done with the cropping of the faces
        face = resize(face, SMALL_SIZE)
        # Check that you are always saving them in the right format
        print "face.min"
        print face.min()

        print "face.max"
        print face.max()

        assert face.min() >=0 and face.max() <=1
        images += [face.reshape(-1)]

        # Save faces as files
        croppedFileName = os.path.join(pathForCropped, shortPath)
        io.imsave(croppedFileName, face)

  else:
    images = []
    imageFiles = [os.path.join(dirpath, f)
      for dirpath, dirnames, files in os.walk(pathForCropped)
      for f in fnmatch.filter(files, '*.' + extension)]

    for f in imageFiles:
      img = cv2.imread(f, 0)
      if type(img[0,0]) == np.uint8:
        print "rescaling unit"
        img = img / 255.0
      images += [img.reshape(-1)]

  print len(images)
  return np.array(images)


# This needs some thought: remove the cropped folder from path?
def readJaffe(detectFaces, equalize):
  PATH = "/data/mcr10/jaffe"
  # PATH = "/home/aela/uni/project/jaffe"
  return readCropEqualize(PATH , "tiff", detectFaces, equalize=equalize,
                          isColoured=False)

def readNottingham(detectFaces, equalize):
  PATH = "/home/aela/uni/project/nottingham"
  # PATH = "/data/mcr10/nottingham"
  return readCropEqualize(PATH, "gif", detectFaces, equalize=equalize,
                          isColoured=False)

def readAberdeen(detectFaces, equalize):
  PATH = "/data/mcr10/Aberdeen"
  # PATH = "/home/aela/uni/project/Aberdeen"
  return readCropEqualize(PATH, "jpg", detectFaces, equalize=equalize,
                           isColoured=True)

if __name__ == '__main__':
  # path = '/home/aela/uni/project/Multi-PIE_Aligned/A_MultiPIE.mat'
  # readMultiPIE(show=True)
  readCroppedYaleSubjects(show=True)

