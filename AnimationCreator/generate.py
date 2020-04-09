# This application will generate json animations based on 18x7 resolution images,
# outputting to either 2018 version or 2019 DCfurs badge json
# By Farkes

#Run files in bulk using unix shell pattern rules E.G.: ? * []
#Run individual files by setting `bulkRun` to '' and listing them in the `filenames` list

from PIL import Image
import json
import glob


##SET OPTIONS HERE >:3
interval = 500  					#Time in miliseconds between frames
bulkRun = 'face*.png' 					#glob driven bulk run (Leave blank if you don't want `filenames` stuffed full of 'face*.png')
filenames = ['face1.png','face2.png','face3.png'] 	#Name of images to create frames from 
outFilename = 'face.json' 				#Name of file to be created
runGrey = True 						#Generates in grayscale for 2018 badges. change this to false for color 2019 badges
####



##WORK HAPPENS HERE
if(bulkRun):
    filenames = sorted(glob.glob(bulkRun), key=str.lower)


def convertPixelGrey(pixel): #This takes a pixel tuple in the form of (<R>,<G>,<B>,[A]) and outputs a hex character indicating LED brightness
    intensity = int(max(pixel[0],pixel[1],pixel[2])/16)     #max intensity taken from RGB and shifted to a scale of 16

    #create result number
    result = "{0:0{1}x}".format(int(intensity),1) #converted to single hex char string
    return result

def generateStringGrey(filename): #This iterates over each pixel in a image supported by PIL returning a string of hex chars for intensity
    #built based on https://www.hackerearth.com/practice/notes/extracting-pixel-values-of-an-image-in-python/
    im = Image.open(filename,'r')
    pix_val = list(im.getdata())
    count = 0
    string = ''

    for pixel in pix_val: #iterate over each pixel
        count+=1        
        out = convertPixelGrey(pixel)
        string = string + out

        if(count%18==0 and count != 126): #add a colon to separate lines with exception of the last line
            string = string+':'
    return string

def generateJSONGrey(filenames, interval): #handle putting strings in json and return a list with each frame
    #built based on https://stackabuse.com/reading-and-writing-json-to-a-file-in-python/
    data = []
    for filename in filenames:
        frame = generateStringGrey(filename)
        data.append({'interval':str(interval),'frame':frame})
    return data

def convertPixel(pixel): #This takes a pixel tuple in the form of (<R>,<G>,<B>,[A]) and outputs a hex pair in 8-bit color R[7:5]G[4:2]B[1:0]
    outRed = int(round(pixel[0]/32))     #256 downscaled to 8 (3 bit)
    outGreen = int(round(pixel[1]/32))   #256 downscaled to 8 (3 bit)
    outBlue = int(round(pixel[2]/64))    #256 downscaled to 4 (2 bit)
    
    #shifting: [this bit shifts to match the proper location in the 8-bit color format]
    binRed = outRed << 5
    binGreen = outGreen << 2
    binBlue = outBlue

    #create result number
    value = binRed+binGreen+outBlue #add together 8 bit color chunks
    result = "{0:0{1}x}".format(value,2) #converted to hex pair string
    return result

def generateString(filename): #This iterates over each pixel in a image supported by PIL returning a string of hexpairs for colors
    #built based on https://www.hackerearth.com/practice/notes/extracting-pixel-values-of-an-image-in-python/
    im = Image.open(filename,'r')
    pix_val = list(im.getdata())
    count = 0
    string = ''

    for pixel in pix_val: #iterate over each pixel
        count+=1        
        out = convertPixel(pixel)
        string = string + out

        if(count%18==0 and count != 126): #add a colon to separate lines with exception of the last line
            string = string+':'
    return string

def generateJSON(filenames, interval): #handle putting strings in json and return a list with each frame
    #built based on https://stackabuse.com/reading-and-writing-json-to-a-file-in-python/
    data = []
    for filename in filenames:
        rgb = generateString(filename)
        data.append({'interval':str(interval),'rgb':rgb})
    return data

def outputJSON(data, outFilename):
    #built based on https://stackabuse.com/reading-and-writing-json-to-a-file-in-python/    
    with open(outFilename, 'w') as outfile:
        json.dump(data, outfile)

if(runGrey):
    data = generateJSONGrey(filenames, interval)
else:
    data = generateJSON(filenames, interval)
outputJSON(data, outFilename)
