# Mit diesem Script können JPEG-Dateien,die in einem Verzeichnis gespeichert sind, zu einer Collage zusammengesetzt werden.
# Die Collage wir auch als JPEG-Datei gespeicht. Achtung! Sehr große Dateien, z.B. 13MB können mit Microsoft Paint nicht geöffnet werden.

#pip install pillow
#Collecting pillow
#  Downloading pillow-11.0.0-cp310-cp310-win32.whl.metadata (9.3 kB)
#Downloading pillow-11.0.0-cp310-cp310-win32.whl (2.2 MB)
#   ---------------------------------------- 2.2/2.2 MB 6.8 MB/s eta 0:00:00
#Installing collected packages: pillow
#Successfully installed pillow-11.0.0

from PIL import Image
import os
import math
import random

#Settings

# Quell-Verzeichnis:
#sFolder = 'E:\\Fotos\\2024\\00_Kalender_Wegweiser'
#sFolder = 'E:\\Fotos\\2024\\00_Kalender_Hilde_porträt'
#sFolder = 'E:\\Fotos\\2024\\00_Kalender_Hilde_quer'

# Ziel-Verzeichnis mit der fertigen Collage:
sCollageFolder = 'E:\\dev_priv\\python_svn\\collage\\c1'

# 2 Möglichkeiten für das Einpassen eines Bildes in eine Kachel der Collage:
#bFormatfuellend = True   #Bild wird aufgezogen, Teile des Bildes werden unsichtbar
#bFormatfuellend = False #Bild wird vollständig angezeigt, aber ggf. mit weißen Rahmen

# Bildgröße: 8200x11800 Pixel entsprechen bei 300 dpi etwa 70x80 cm
#pixX = 8200
#pixY = 11800

# Zwischenraum zwischen den Bildern
pixSpace = 30

#sVorlage = 'E:\\dev_priv\\python_svn\\collage\\c1\\CollagenVorlage.jpg'


### class CEnumOrientation: ###########################################
class CEnumOrientation:
   def __init__(self):
      self.Square = 1
      self.Portrait = 2
      self.Landscape = 3
     
enumOrient = CEnumOrientation()

### class CImage: ###########################################
class CImage:
   def __init__(self, sFolder, sSubFolder, filename):
      self.sFilename = filename
      
      sFile = f'{sFolder}\\{sSubFolder}\\{filename}'
      im = Image.open( sFile)
      self.cx = im.size[0]
      self.cy = im.size[1]
      im.close()

      self.dRatio = self.cx / self.cy
      print( f'{self.sFilename}: {self.dRatio}')

      if self.dRatio < 0.85:
         self.eOrientation = enumOrient.Portrait
      elif 0.9 <= self.dRatio and self.dRatio <= 1.15:
         self.eOrientation = enumOrient.Square
      else:
         self.eOrientation = enumOrient.Landscape
      



### def Collage() ##########################################################################
def Collage(sFolder, sSubFolder, pixX, pixY, bFormatfuellend):

   #Bildgrößen bestimmen und merken
   aImages = []
   anzImagesSquare = 0
   anzImagesLandscape = 0
   anzImagesPortrait = 0
   pixMaxCx = 0
   for filename in os.listdir(f'{sFolder}\\{sSubFolder}'):
       if filename.endswith(".jpg"):

          ci = CImage( sFolder, sSubFolder, filename)

          if ci.eOrientation == enumOrient.Portrait:
             anzImagesPortrait += 1
          elif ci.eOrientation == enumOrient.Landscape:
             anzImagesLandscape += 1
          else:
             anzImagesSquare += 1
   
          if ci.cx > pixMaxCx:
             pixMaxCx = ci.cx
             
          aImages.append(ci)

   #Bilder zählen
   anzImages = len(aImages)

   #Bilder zufällig anordnen
#$$   random.shuffle(aImages)

   #Kachelausrichtung bestimmen
   orientTile = enumOrient.Square
   anzOrientTile = anzImagesSquare
   if anzImagesPortrait > anzImagesLandscape and anzImagesPortrait > anzImagesSquare:
      orientTile = enumOrient.Portrait
      anzOrientTile = anzImagesPortrait
   elif anzImagesLandscape > anzImagesPortrait and anzImagesLandscape > anzImagesSquare:
      orientTile = enumOrient.Landscape
      anzOrientTile = anzImagesLandscape

   #Seitenverhältnis für die Mehrzahl der Bilder ermitteln
   dRatio = 0.0
   for ci in aImages:
      if ci.eOrientation == orientTile:
         dRatio += ci.dRatio
   dRatioAverage = dRatio / anzOrientTile


   # Verteilung der Bilder und Kachelgröße bestimmen:
   pixImageNewX = 0
   pixImageNewY = 0
   anzImagesY = 0
   anzImagesX = round((pixX + pixSpace) / (pixMaxCx + pixSpace))
      
   for anzImagesX in range( anzImagesX, anzImages+1, 1):
      pixImageNewX = (pixX - (anzImagesX - 1) * pixSpace) / anzImagesX
      
      anzImagesY = math.ceil(anzImages / anzImagesX)

      pixImageNewY = pixImageNewX / dRatioAverage
      
      if anzImagesY * pixImageNewY + (anzImagesY - 1) * pixSpace <= pixY:
         pixImageNewY = (pixY - (anzImagesY - 1) * pixSpace) / anzImagesY
         break;

   # Leere Kacheln zufällig verteilen:
   anzLeerstellen = anzImagesX*anzImagesY - anzImages
   arridxLeerstellen = []
   if 0 < anzLeerstellen:
      while True:
         r = random.randint(1, (anzImagesX*anzImagesY)-1)#anzImages)     
         if r in arridxLeerstellen:
            continue
         arridxLeerstellen.append( r)
         if len(arridxLeerstellen) >= anzLeerstellen:
            break

   #collage = Image.new("RGBA", (pixX,pixY), color=(255,255,255,255)) kann nicht als jpg gespeichert werden
   collage = Image.new("RGB", (pixX,pixY), color=(255,255,255,255))

   #würde auch funktionieren:
   #Vorlage = Image.open( f'{sVorlage}')
   #collage = Vorlage.resize((pixX, pixY))

   idxImage = 0
   for y in range(0,anzImagesY,1):
      for x in range(0,anzImagesX,1):
   
         idx = y * anzImagesX + x
         if idx in arridxLeerstellen:
            continue 
      
         ci = aImages[idxImage]
         idxImage += 1

         im = Image.open( f'{sFolder}\\{sSubFolder}\\{ci.sFilename}')

         cx = ci.cx
         cy = ci.cy

         cxNew = pixImageNewX
         cyNew = pixImageNewY
         offsetX = 0
         offsetY = 0

         if idxImage == 24 or idxImage == 29:
            print(idxImage)

         if bFormatfuellend: #Bild wird aufgezogen, Teile des Bildes werden unsichtbar
            offsX = 0
            offsY = 0
            cxNew = cx
            cyNew = cy
            
            if cx > cy:
               if cx != pixImageNewX:
                  cxNew = pixImageNewX             
                  cyNew = cy * cxNew / cx
               
               if cyNew < pixImageNewY:   
                  cxNew = cxNew * pixImageNewY / cyNew
                  cyNew = pixImageNewY             
            
            elif cy > cx:
               if cy != pixImageNewY:
                  cyNew = pixImageNewY             
                  cxNew = cx * cyNew / cy
               
               if cxNew < pixImageNewX:   
                  cyNew = cyNew * pixImageNewX / cxNew
                  cxNew = pixImageNewX             

            if cxNew > pixImageNewX:
               offsX = abs(round((cxNew - pixImageNewX) / 2))
            if cyNew > pixImageNewY:
               offsY = abs(round((cyNew - pixImageNewY) / 2))
               
            imResize = im.resize((round(cxNew), round(cyNew)))

            posX, posY, w, h = (offsX, offsY, pixImageNewX, pixImageNewY)
            box = (posX, posY, posX + w, posY + h)
            imResize = imResize.crop(box)

         else: #Bild wird vollständig angezeigt, aber mit weißen Rahmen
            if cx > cy:
               cyNew = cy * cxNew / cx
               offsetY = round((pixImageNewY - cyNew) / 2)
            elif cy > cx:
               cxNew = cx * cyNew / cy
               offsetX = round((pixImageNewX - cxNew) / 2)

            imResize = im.resize((round(cxNew), round(cyNew)))
      
         posX = offsetX + x * pixImageNewX + x  * pixSpace
         posY = offsetY + y * pixImageNewY + y  * pixSpace
      
         collage.paste(imResize, (round(posX),round(posY)))
         
         im.close()
         imResize.close()
         print(f'{posX},{posY}')

   collage.save( f'{sCollageFolder}\\{sSubFolder}_{pixX}_{pixY}_{bFormatfuellend}.jpg')
   collage.close()
   
      

### Collage zusammenstellen ##########################################################################
sFolder = 'E:\\Fotos\\2024'

Collage(sFolder, '00_Kalender_Wegweiser', 8200, 11800, True)
Collage(sFolder, '00_Kalender_Hilde_porträt', 8200, 11800, True)
Collage(sFolder, '00_Kalender_Hilde_quer', 8200, 11800, True)

Collage(sFolder, '00_Kalender_Wegweiser', 11800, 8200, True)
Collage(sFolder, '00_Kalender_Hilde_porträt', 11800, 8200, True)
Collage(sFolder, '00_Kalender_Hilde_quer', 11800, 8200, True)

# Collage(sFolder, '00_Kalender_Wegweiser', 8200, 11800, False)
# Collage(sFolder, '00_Kalender_Hilde_porträt', 8200, 11800, False)
# Collage(sFolder, '00_Kalender_Hilde_quer', 8200, 11800, False)

# Collage(sFolder, '00_Kalender_Wegweiser', 11800, 8200, False)
# Collage(sFolder, '00_Kalender_Hilde_porträt', 11800, 8200, False)
# Collage(sFolder, '00_Kalender_Hilde_quer', 11800, 8200, False)



