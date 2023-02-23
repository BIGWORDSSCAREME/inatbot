import shutil
import random
import requests as r
import tkinter as tk
from os import remove
from PIL import Image, ImageTk

random.seed()
iNatUrl = "https://api.inaturalist.org/v1/observations?photos=true&taxon_name={}&identifications=most_agree&quality_grade=research&locale=en-US&page=1&per_page=10&order=desc&order_by=created_at"

def BindTree(node, event, function):
	node.bind(event, function)
	
	for child in node.children.values():
		BindTree(child, event, function)

class Screen:
	
	mainFrame = None

	def PackSelf(self):
		self.mainFrame.pack(fill = "both", expand = True)

	def UnpackSelf(self):
		self.mainFrame.pack_forget()

class AppWindow:

	readyGameScreen = None
	gameScreen = None

	def __init__(self):
		#building of the GUI
		self.window = tk.Tk()
				
		self.window.geometry("800x500")
		self.window.title("iNat study helper")

		self.gameScreen = Game(self.window)
		self.readyGameScreen = ReadyGame(self.window, self.gameScreen)
		self.mainMenuScreen = MainMenu(self.window, self.readyGameScreen)
		
		self.mainMenuScreen.PackSelf()
		
		
		
		self.window.mainloop()
		
		
		
class MainMenu(Screen):

	readyGameScreen = None

	def __init__(self, window, readygamescreen):
		self.mainFrame = tk.Frame(window)
		self.readyGameScreen = readygamescreen
		self.topLabel = tk.Label(self.mainFrame, text = "hi")
		self.topLabel.pack()
		self.gameButton = tk.Button(self.mainFrame, text = "Start", command = self.ReadyGameButton)
		self.gameButton.pack()
	
	def ReadyGameButton(self):
		self.UnpackSelf()
		self.readyGameScreen.PackSelf()



class ReadyGame(Screen):

	deletedSpeciesStack = []
	speciesList = []
	gameFrame = None
	
	def __init__(self, window, game):
		self.gameFrame = game
		self.mainFrame = tk.Frame(window)
		self.startGameButton = tk.Button(self.mainFrame, text = "Start", command = self.StartGame)
		self.startGameButton.pack()
		self.enterSpecies = tk.Entry(self.mainFrame)
		self.enterSpecies.bind("<KeyPress>", self.AddSpecies)
		self.enterSpecies.pack()

		self.enteredSpeciesFrame = tk.Frame(self.mainFrame, height = 200)
		self.deletedSpeciesStack = []
		self.enteredSpeciesFrame.pack()
		BindTree(self.mainFrame, "<Button-3>", self.RecoverDeletedSpecies)

	def AddSpecies(self, event):
		if event.keysym == "Return":
			entered = ""
			entered = self.enterSpecies.get()
			newSpecies = SpeciesListItem(entered, self.enteredSpeciesFrame, self.deletedSpeciesStack, self.speciesList)
			self.speciesList.append(entered)
			newSpecies.BindRecoverDeletedSpecies(self.RecoverDeletedSpecies)
			self.enterSpecies.delete(0, len(entered))

	def RecoverDeletedSpecies(self, event):
		if len(self.deletedSpeciesStack) > 0:
			species = self.deletedSpeciesStack.pop()
			species.Reappear()
			self.speciesList.append(species.name)

	def StartGame(self):
		for i in self.deletedSpeciesStack:
			i.cableText.destroy()
		del self.deletedSpeciesStack[:]
		self.UnpackSelf()
		self.gameFrame.PackSelf(self.speciesList)
		

class SpeciesListItem:

	name = ""
	dStack = None
	sList = None

	def __init__(self, text, parent, delstack, specieslist):
		self.cableText = tk.Label(parent, text = text, cursor = "man")
		self.cableText.bind("<Button-1>", self.LeftClicked)
		self.cableText.pack()
		self.dStack = delstack
		self.name = text
		self.sList = specieslist
		
	def LeftClicked(self, event):
		self.dStack.append(self)
		self.cableText.pack_forget()
		self.sList.remove(self.name)
		if len(self.dStack) > 15:
			self.dStack[0].cableText.destroy()
			del self.dStack[0]
			
	def Reappear(self):
		self.cableText.pack()

	def BindRecoverDeletedSpecies(self, function):
		self.cableText.bind("<Button-3>", function)

class Game(Screen):

	imageList = []
	speciesList = []
	speciesDict = {}
	randomizedList = []
	currentImage = 0
		
	#make a list with the order of all the urls. just go through that loading only a few at a time

	def __init__(self, window):
		self.mainFrame = tk.Frame(window)
		self.speciesName = tk.Label(self.mainFrame, text = "Which species?")
		self.imageCanvas = tk.Canvas(self.mainFrame)
		self.showNameButton = tk.Button(self.mainFrame, text = "Show name", command = self.ShowName)
		self.previousSpeciesButton = tk.Button(self.mainFrame, text = "Previous species", command = lambda: self.NextImage(-1))
		self.nextSpeciesButton = tk.Button(self.mainFrame, text = "Next species", command = lambda: self.NextImage(1))

	def PackSelf(self, species):
		#ill fuck with the exact positioning later, once it actually works.
		self.speciesList = species
		self.MakeOrder()
		self.speciesName.grid(row = 0, column = 0, sticky=tk.N+tk.E+tk.S+tk.W)
		self.imageCanvas.grid(row = 1, column = 0, sticky=tk.N+tk.E+tk.S+tk.W)
		self.showNameButton.grid(row = 2, column = 0, sticky=tk.N+tk.E+tk.S+tk.W)
		self.previousSpeciesButton.grid(row = 3, column = 0, sticky=tk.N+tk.E+tk.S+tk.W)
		self.nextSpeciesButton.grid(row = 3, column = 1, sticky=tk.N+tk.E+tk.S+tk.W)
		self.mainFrame.pack()
		self.PickImage()
		imageDownload = self.DownloadImage(self.randomizedList[1]["url"])
		self.randomizedList[1]["image"] = imageDownload[0]
		self.randomizedList[1]["filename"] = imageDownload[1]
		self.NextImage(1)

	def MakeOrder(self):
		for species in self.speciesList:
			speciesUrl = iNatUrl.format(species)
			jsonData = r.get(speciesUrl).json()
			if jsonData['total_results'] == 0:
				print(species + " has no results.")
			self.speciesDict[species] = []
			for i in jsonData["results"]:
				self.speciesDict[species].append(i["photos"][0]["url"])
				self.randomizedList.append({"species": species, "url": i["photos"][0]["url"] })
		random.shuffle(self.randomizedList)

	def DownloadImage(self, url):
		index = url.find("square")
		idIndex = url.find("/photos/")
		id = url[idIndex + 8: idIndex + 17]
		url2 = url[:index]
		url2 = url2 + "medium"
		fileExtension = url[index + 6:]
		url = url2 + fileExtension
		response = r.get(url, stream = True)
		#in the url replace the "square" with medium to get a larger file.
		if response.status_code == 200:
			with open(id + fileExtension, 'wb') as f: # this might be failing because it does not have a file extension
				shutil.copyfileobj(response.raw, f)
			img = Image.open(id + fileExtension)
			img = ImageTk.PhotoImage(img)
			#return the image and the name of the file
			return (img, id + fileExtension)
		else:
			print("failed to grab image with status code " + str(response.status_code))
			print(iNatPicUrl.format(id))
			return None

	def NextImage(self, increment):
		self.speciesName.config(text = "Which species?")
		self.currentImage += increment
		index = self.currentImage % len(self.randomizedList)
		self.LoadImage(self.randomizedList[index]["image"])
		
		nextImage = self.randomizedList[(self.currentImage + increment) % len(self.randomizedList)]
		self.DownloadImage(nextImage["url"])
		imageDownload = self.DownloadImage(nextImage["url"])
		nextImage["image"] = imageDownload[0]
		nextImage["filename"] = imageDownload[1]
		
		previousImage = self.randomizedList[(self.currentImage - (2 * increment)) % len(self.randomizedList)]
		if "filename" in previousImage:
		#The above line checks to see if there is a filename field in the KEYS of the
		#dictionary, previousImage. Weird.
			#previousImage["image"].close() not sure how to close lololoolol. looks
			#like this doesn't work anymore. not a method.
			remove(path = previousImage["filename"])	

	def LoadImage(self, image):
		self.imageCanvas.delete("all")
		self.imageCanvas.create_image(0, 0, anchor = tk.NW, image = image)
		self.imageCanvas.image = image

	def PickImage(self):
		#Pick randomly from the list of species and stuff.
		#If there are no species, rangeint will fail. 0 to -1 and the number on the right has to be higher.
		species = self.speciesList[random.randint(0, len(self.speciesList) - 1)]
		url = self.speciesDict[species][random.randint(0, len(self.speciesDict[species]) - 1)]
		self.speciesDict[species].remove(url)
		if len(self.speciesDict[species]) == 0:
			speciesList.remove(species)
		#Adds to the end of the list
		self.imageList.append(self.DownloadImage(url))

	def ShowName(self):
		self.speciesName.config(text = self.randomizedList[self.currentImage % len(self.randomizedList)]["species"])

	def __del__(self):
		for i in self.randomizedList:
			if "filename" in i:
				#might want to change it from removing it based on the path string
				#to something else. not a big deal but if the id string somehow contained
				#a file path it could delete your files good heavens.
				#Also this fails to delete one of the images. Not sure why. something to fix.
				try:
					remove(path = i["filename"])
				except: pass

mainWindow = AppWindow()