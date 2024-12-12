# Mit diesem Script können JPEG-Dateien,die in einem Verzeichnis gespeichert sind, zu einer m-mal-n-Schachbrett-Collage zusammengesetzt werden.
# Z.B. alle 12 Bilder für die Übersichtsseite eines Jahreskalenders.
# Die Collage wir auch als JPEG-Datei gespeichert. Achtung! Sehr große Dateien, z.B. 13MB können mit Microsoft Paint nicht geöffnet werden.

# Der erste Ansatz war, für die Collage eine feste Größe vorzugeben und das Seitenverhältnis der Bild-Kacheln daran anzupassen.
# Das führt aber nur selten zu ausgewogenen Collagen.

# Deshalb wurde in der zweiten Version die Einstellung CTileShape eingeführt, um das Seitenverhältnis der Bildkacheln fest vorzugeben.
# LikeMajority entspricht dem ersten Ansatz mit dem berechnenten Seitenverhältnis. 
# Die anderen drei Werte definieren fest vorgegebene Seitenverhältnisse. Bei diesen drei Werten kann nur noch die für die Collage vorgegebene Breite 
# ODER die Höhe berücksichtigt werden und es wird immer mit CFillMode.Loss gerechnet.

# Die Größe der Collage in Pixel ergibt sich aus den vorgegebenen Maßen in Zentimetern und der Auflösung in dpi (ppi)
# Für den Stoffdruck sind laut eicie.com 120 dpi optimal.

# Das Script erfordert das Pillow-Paket, gefunden über https://pypi.org/project/pillow/ 
# pip install pillow
# Collecting pillow
#  Downloading pillow-11.0.0-cp310-cp310-win32.whl.metadata (9.3 kB)
# Downloading pillow-11.0.0-cp310-cp310-win32.whl (2.2 MB)
#   ---------------------------------------- 2.2/2.2 MB 6.8 MB/s eta 0:00:00
# Installing collected packages: pillow
# Successfully installed pillow-11.0.0

# pillow-Doku: https://pillow.readthedocs.io/en/stable/reference

# Das Script wurde hier veröffentlicht: https://github.com/grasmax/collage


from PIL import Image
from PIL import ExifTags
import os
import math
import random
from operator import attrgetter
import time
import datetime


### class CTileShape: ###########################################
class CTileShape:
   def __init__(self):
      self.LikeMajority = 1   # Mehrheit der Bilder entscheidet über Hoch/Quer/Quadrat, 
                              # Collage wird mit leeren Kacheln auf n x m aufgefüllt
                              # alle-CFillMode-Werte sind möglich

      # eine Collage mit einer der folgenden Einstellungen wird immer mit CFillMode.Loss erstellt
      self.Portrait34 = 2     # Kachel im Porträtformat im Seitenverhältnis 3:4
      self.Landscape169 = 3   # Kachel im Querformat im Seitenverhältnis 16:9
      self.Square = 4         # Kachel im mit Seitenverhältnis 1:1
enumTileShape = CTileShape()


### class CFillMode: ###########################################
# Diese Einstellung legt fest, wie ein Bild in einer Collage-Kachel angezeigt wird
class CFillMode:
   def __init__(self):
      self.Loss = 1        # Bild wird aufgezogen, Teile des Bildes werden unsichtbar
      self.Complete = 2    # Bild wird vollständig angezeigt, aber es treten Rändern auf
      self.Distortion = 3  # Bild wird vollständig angezeigt, aber es treten Verzerrungen auf - Nicht empfohlen
enumFill = CFillMode()


### class CEnumOrientation: ###########################################
# Jedes eingelesene Bild bekommt eine der folgenden Eigenschaften.
# Diese Eigenschaft wird nur bei CTileShape.LikeMajority ausgewertet
class CEnumOrientation:
   def __init__(self):
      self.Square = 1
      self.Portrait = 2
      self.Landscape = 3
enumOrient = CEnumOrientation()

### class CImageSort: ###########################################
# Legt die Reihenfolge fest, wie die gefundenen Bilder in die Collage aufgenommen werden
class CImageSort:
   def __init__(self):
      self.Alpha = 1          # alphabetisch nach Namen sortiert
      self.CreationDate = 2   # nach Aufnahmedatum sortiert, beginnend beim ältesten
      self.Random = 3         # zufällige Reihenfolge
enumSort = CImageSort()

### class CImage: ###########################################
# Eigenschaften eines Einzelbildes
class CImage:
   def __init__(self, sFolder, sSubFolder, filename):
      self.sFilename = filename
      
      sFile = f'{sFolder}\\{sSubFolder}\\{filename}'
      im = Image.open( sFile)
      self.cx = im.size[0]
      self.cy = im.size[1]
      
      exifData = im._getexif()
      # for key, val in exifData.items():
      #   if key in ExifTags.TAGS:
      #       print(f'Exif: {ExifTags.TAGS[key]}:{val}')
      #   else:
      #       print(f'{key}:{val}')
      # Ausgabe:
         # Exif: ImageWidth:4032
         # Exif: ImageLength:2268
         # Exif: ExifOffset:202
         # Exif: Make:samsung
         # Exif: Model:SM-G981B
         # Exif: Software:G981BXXSJHXC1
         # Exif: DateTime:2024:05:04 09:29:22
         # ...
      # DateTime: 
      try:
         #self.dateCreation = exifData.get(36867)
         self.dateCreation = exifData.get(306)
      except Exception as e:
         self.dateCreation = time.ctime(os.path.getctime(sFile))


      im.close()

      self.dRatio = self.cx / self.cy
      # print( f'{self.sFilename}: {self.dRatio}')

      if self.dRatio < 0.85:
         self.eOrientation = enumOrient.Portrait
      elif 0.9 <= self.dRatio and self.dRatio <= 1.15:
         self.eOrientation = enumOrient.Square
      else:
         self.eOrientation = enumOrient.Landscape

   def __eq__(self, other):
      return self.dateCreation == other.dateCreation

   def __lt__(self, other):
      return self.dateCreation < other.dateCreation      



### def Collage( sCollageFolder,) ##########################################################################
def Collage( sCollageFolder, sFolder, sSubFolder, eSort, dpiRes, nWidthCm, nHeightCm, eFillMode, pixSpace, eTileShape, anzTopOnly=-1):

   # Größe der Collage in Pixel berechnen
   pixX = round((nWidthCm * dpiRes) / 2.54)
   pixY = round((nHeightCm * dpiRes) / 2.54)

   # Bilddaten bestimmen und merken
   aImagesOrig = []
   anzImagesSquare = 0
   anzImagesLandscape = 0
   anzImagesPortrait = 0
   pixMaxCx = 0
   for filename in os.listdir(f'{sFolder}\\{sSubFolder}'):
      aTok = filename.split('.') 
      if len(aTok) < 2:
         continue;
      sExt = aTok[1].upper()
      
      if sExt == 'JPG':

          ci = CImage( sFolder, sSubFolder, filename)

          if ci.cx > pixMaxCx:
             pixMaxCx = ci.cx
             
          aImagesOrig.append(ci)

   # Bilder sortieren
   if eSort == enumSort.Random:
      aImages = aImagesOrig
      random.shuffle(aImages) #Bilder zufällig anordnen

   elif eSort == enumSort.CreationDate: # nach Aufnahmedatum aufsteigend
     aImages = sorted(aImagesOrig)  # __eq__ / __lt__ benutzen

   elif eSort == enumSort.Alpha:
      aImages = sorted(aImagesOrig, key=attrgetter('sFilename'))
   
   else:
      aImages = aImagesOrig  # so wie es von os.listdir gelifert wurde
   
   if anzTopOnly > 0:
      aTemp = [] 
      topN = slice(anzTopOnly)
      aTemp = aImages[topN]
      aImages = aTemp
      aTemp.clear

   #Bilder zählen
   anzImages = len(aImages)

   for ci in aImages:
      if ci.eOrientation == enumOrient.Portrait:
         anzImagesPortrait += 1
      elif ci.eOrientation == enumOrient.Landscape:
         anzImagesLandscape += 1
      else:
         anzImagesSquare += 1


   #Seitenverhältnis für die Mehrzahl der Bilder ermitteln
   dRatioAverage = 1.0 # == enumTileShape.Square

   if eTileShape == enumTileShape.LikeMajority:
      orientTile = enumOrient.Square
      anzOrientTile = anzImagesSquare
      if anzImagesPortrait > anzImagesLandscape and anzImagesPortrait > anzImagesSquare:
         orientTile = enumOrient.Portrait
         anzOrientTile = anzImagesPortrait
      elif anzImagesLandscape > anzImagesPortrait and anzImagesLandscape > anzImagesSquare:
         orientTile = enumOrient.Landscape
         anzOrientTile = anzImagesLandscape
      dRatio = 0.0
      for ci in aImages:
         if ci.eOrientation == orientTile:
            dRatio += ci.dRatio
      dRatioAverage = dRatio / anzOrientTile

   elif eTileShape == enumTileShape.Landscape169:
      dRatioAverage = 1.7777777

   elif eTileShape == enumTileShape.Portrait34:
      dRatioAverage = 0.75


   # Verteilung der Bilder und Kachelgröße bestimmen:
   #sol = []
   pixImageNewX = 0
   pixImageNewY = 0
   anzImagesY = 0
   anzImagesX = round((pixX + pixSpace) / (pixMaxCx + pixSpace))
   #for anzImagesX in range( anzImagesX, anzImages+1, 1):
   #sol = []
   for anzImagesX in range( 1, anzImages+1, 1):
      pixImageNewX = (pixX - (anzImagesX - 1) * pixSpace) / anzImagesX
      
      anzImagesY = math.ceil(anzImages / anzImagesX)

      pixImageNewY = pixImageNewX / dRatioAverage
      
      if anzImagesY * pixImageNewY + (anzImagesY - 1) * pixSpace <= pixY:

         if eTileShape == enumTileShape.LikeMajority:
            # das Seitenverhältnis ändern:
            pixImageNewY = (pixY - (anzImagesY - 1) * pixSpace) / anzImagesY

            # sol.append((anzImagesX,anzImagesY, 
            #             round(pixX - (anzImagesX * pixImageNewX + (anzImagesX - 1) * pixSpace)),
            #             round(pixY - (anzImagesY * pixImageNewY + (anzImagesY - 1) * pixSpace))  ))
            break;
         else:
            break;

   pixXCalc = round(anzImagesX * pixImageNewX + (anzImagesX - 1) * pixSpace)
   pixYCalc = round(anzImagesY * pixImageNewY + (anzImagesY - 1) * pixSpace)
   cmXCalc = round((pixXCalc * 2.54) / dpiRes)
   cmYCalc = round((pixYCalc * 2.54) / dpiRes)

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

         # if idxImage == 24 or idxImage == 29: #Debug-Stopp
         #    print(idxImage)

         if eFillMode == enumFill.Loss: #Bild wird aufgezogen, Teile des Bildes werden unsichtbar
            offsX = 0
            offsY = 0
           
            if cx > cy:
               if cx != pixImageNewX:
                  cyNew = cy * cxNew / cx
               
               if cyNew < pixImageNewY:   
                  cxNew = cxNew * pixImageNewY / cyNew
                  cyNew = pixImageNewY             
            
            elif cy > cx:
               if cy != pixImageNewY:
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

         elif eFillMode == enumFill.Complete: #Bild wird vollständig angezeigt, aber mit weißen Rahmen
            if cx > cy:
               cyNew =  pixImageNewX / ci.dRatio
               if cyNew > pixImageNewY:
                  cyNew = pixImageNewY
                  cxNew = cyNew * ci.dRatio
                 
            elif cy > cx:
               cxNew = pixImageNewY * ci.dRatio
               if cxNew > pixImageNewX:
                  cxNew = pixImageNewX
                  cyNew = cxNew / ci.dRatio

            imResize = im.resize((round(cxNew), round(cyNew)))
            
            offsetY = round((pixImageNewY - cyNew) / 2)
            offsetX = round((pixImageNewX - cxNew) / 2)

         elif eFillMode == enumFill.Distortion: #Bild wird vollständig angezeigt, aber es treten Verzerrungen auf
            imResize = im.resize((round(cxNew), round(cyNew)))
            
            offsetY = round((pixImageNewY - cyNew) / 2)
            offsetX = round((pixImageNewX - cxNew) / 2)

         else:
            print('Unzulässiger Fill-Mode.')
            quit()
            
         posX = round(offsetX + x * pixImageNewX + x  * pixSpace)
         posY = round(offsetY + y * pixImageNewY + y  * pixSpace)
      
         collage.paste(imResize, (posX, posY))
         
         im.close()
         imResize.close()
         print(f'x:{posX:04d}, y={posY:04d}, {ci.sFilename}')

   
   # Die Collage als Datei speichern
   sFillMode = ''
   if eFillMode == enumFill.Loss: #Bild wird aufgezogen, Teile des Bildes werden unsichtbar
      sFillMode = 'loss'
   elif eFillMode == enumFill.Complete: #Bild wird vollständig angezeigt, aber mit weißen Rahmen
      sFillMode = 'complete'
   elif eFillMode == enumFill.Distortion: #Bild wird vollständig angezeigt, aber es treten Verzerrungen auf
      sFillMode = 'distortion'

   sTileShape = 'square'
   if eTileShape == enumTileShape.LikeMajority:
      sTileShape = 'likemajority'
   elif eTileShape == enumTileShape.Landscape169:
      sTileShape = 'landscape169'
   elif eTileShape == enumTileShape.Portrait34:
      sTileShape = 'portrait34'

   sSort = 'def'
   if eSort == enumSort.Alpha:
      sSort = 'alpha'
   elif eSort == enumSort.CreationDate:
      sSort = 'creadate'
   elif eSort == enumSort.Random:
      sSort = 'random'


   tNow = datetime.datetime.now()
   sNow = tNow.strftime("%Y%m%d%H%M%S")
   sColl = f'{sCollageFolder}\\{sSubFolder}_{nWidthCm}cm_x_{nHeightCm}cm_{dpiRes}dpi_{cmXCalc}cm_x_{cmYCalc}cm_{sTileShape}_{sFillMode}_{sSort}_{sNow}_{pixSpace}.jpg'
   collage.save( sColl)
   collage.close()
   
      

### Collage zusammenstellen ##########################################################################

#$$ offen: leere Kacheln im m x n Schachbrett auffüllen:
  # v1 für je 3 leere Kacheln die Größe eines Bildes vervierfachen
  # v2 für jede leere Kachel ein Bild doppeln

# Verzeichnis, in dem die Bilddateien zu finden sind:
sFolder = 'E:\\Fotos\\2024'

# Verzeichnis, in dem die fertige Collage gespechert werden soll:
sCollageFolder = 'E:\\Fotos\\2024\\00_Collagen'

# Alternativ zur Erstellung einer Image-Instanz mit Image.new könnte auch eine leere Vorlage geöffnet werden.
# sVorlage definiert die Vorlage:
sVorlage = 'E:\\dev_priv\\python_svn\\collage\\c1\\CollagenVorlage.jpg'

# Zwischenraum zwischen den Bildern
pixSpace = 30

# def Collage( sCollageFolder, sFolder, sSubFolder, eSort, dpiRes, nWidthCm, nHeightCm, eFillMode, pixSpace, eTileShape):

#Collage( sCollageFolder, sFolder, '00_Kalender_Wegweiser', eSort=enumSort.Alpha, eTileShape=enumTileShape.LikeMajority,\
#         dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

# Collage( sCollageFolder, sFolder, '00_Kalender_Wegweiser', eSort=enumSort.Random, eTileShape=enumTileShape.LikeMajority,\
#          dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

# Collage( sCollageFolder, sFolder, '00_Kalender_Hilde_porträt', eSort=enumSort.CreationDate, eTileShape=enumTileShape.LikeMajority,\
#          dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

# Collage( sCollageFolder, sFolder, '00_Kalender_Hilde_quer', eSort=enumSort.CreationDate, eTileShape=enumTileShape.LikeMajority,\
#          dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

#Collage( sCollageFolder, sFolder, '00_Kalender_Hilde_quer', eSort=enumSort.CreationDate, eTileShape=enumTileShape.Landscape169,\
#          dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

#Collage( sCollageFolder, sFolder, '00_Kalender_Hilde_porträt', eSort=enumSort.CreationDate, eTileShape=enumTileShape.Portrait34,\
#          dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

# Collage( sCollageFolder, sFolder, '00_Kalender_Hilde_porträt', eSort=enumSort.CreationDate, eTileShape=enumTileShape.Square,\
#           dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

# Collage( sCollageFolder, sFolder, '00_Kalender_Hilde_quer', eSort=enumSort.CreationDate, eTileShape=enumTileShape.Square,\
#           dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

# Collage( sCollageFolder, sFolder, '00_Kalender_Wegweiser', eSort=enumSort.CreationDate, eTileShape=enumTileShape.Square,\
#           dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

#Collage( sCollageFolder, sFolder, '00_Kalender_Wegweiser', eSort=enumSort.Random, eTileShape=enumTileShape.LikeMajority,\
#          dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

#Collage( sCollageFolder, sFolder, '00_Kalender_Hilde_porträt', eSort=enumSort.CreationDate, eTileShape=enumTileShape.Portrait34,\
#           dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=pixSpace)

#Collage( sCollageFolder, sFolder, '00_Kalender_Hilde_porträt', eSort=enumSort.CreationDate, eTileShape=enumTileShape.Portrait34,\
#           dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=10)

#Collage( sCollageFolder, sFolder, '00_Wandbild_Collage_Blumen', eSort=enumSort.Random, eTileShape=enumTileShape.Portrait34,\
#           dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=10)

# for i in range (1,20,1):
#    print(f'Collage{i}')
#    Collage( sCollageFolder, sFolder, '00_Wandbild_Collage_Blumen', eSort=enumSort.Random, eTileShape=enumTileShape.LikeMajority,\
#            dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=10)

#Collage( sCollageFolder, sFolder, '00_Wandbild_Collage_SylviRichiBarca', eSort=enumSort.CreationDate, eTileShape=enumTileShape.Portrait34,\
#           dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=10)

#Collage( sCollageFolder, sFolder, '00_Wandbild_Collage_Schmetterlinge', eSort=enumSort.CreationDate, eTileShape=enumTileShape.LikeMajority,\
#           dpiRes=120, nWidthCm=70, nHeightCm=100, eFillMode=enumFill.Loss, pixSpace=10)

# for i in range (1,5,1):
#    print(f'Collage{i}')
#    Collage( sCollageFolder, sFolder, '00_Wandbild_Collage_Blumensträuße', eSort=enumSort.Random, eTileShape=enumTileShape.LikeMajority,\
#            dpiRes=300, nWidthCm=60, nHeightCm=40, eFillMode=enumFill.Loss, pixSpace=10)


# for i in range (1,20,1):
#    print(f'Collage{i}')
#    Collage( sCollageFolder, sFolder, '00_Wandbild_Collage_Blumen_2005-2012', eSort=enumSort.Random, eTileShape=enumTileShape.LikeMajority,\
#            dpiRes=300, nWidthCm=60, nHeightCm=40, eFillMode=enumFill.Loss, pixSpace=10, anzTopOnly=24)

# CeWe-A2-Kalender-Quer braucht 52x40cm und 25 Kacheln
for i in range (1,20,1):
  print(f'Collage{i}')
  Collage( sCollageFolder, sFolder, '00_Wandbild_Collage_Blumen_2005-2012', eSort=enumSort.Random, eTileShape=enumTileShape.LikeMajority,\
         dpiRes=300, nWidthCm=52, nHeightCm=40, eFillMode=enumFill.Loss, pixSpace=10, anzTopOnly=25)
