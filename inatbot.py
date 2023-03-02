import random
import requests as r
import tkinter as tk
from tkinter import filedialog
from os import remove
from PIL import Image, ImageTk
from json import loads


"""THINGS TO DO--
ALLOW IMPORTABLE JSONS.
CHANGE requests.json() to python json.loads(). json.loads() is prob safer.
COMMENT.
CLEAN UP THE READYGAMESCREEN SECTION. SPECIFCALLY CLICKABLE TEXT AND THE FUNCTIONS. CONFUSING.
"""

random.seed()
iNatUrl = "https://api.inaturalist.org/v1/observations?photos=true&taxon_name={}&identifications=most_agree&quality_grade=research&locale=en-US&page={}&per_page=10&order=desc&order_by=created_at"

def BindTree(node, event, function):
	node.bind(event, function)
	
	for child in node.children.values():
		BindTree(child, event, function)

def insert_newlines(string, every=64):
	#stole this function from stackoverflow. adds new lines every 64 characters.
	return '\n'.join(string[i:i+every] for i in range(0, len(string), every))

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
	#species list is made of tuples of 2. the first item is the name, the second is additional information.
	speciesList = []
	gameFrame = None
	
	def __init__(self, window, game):
		self.gameFrame = game
		self.mainFrame = tk.Frame(window)
		self.startGameButton = tk.Button(self.mainFrame, text = "Start", command = self.StartGame)
		self.startGameButton.pack()
		self.enterSpecies = tk.Entry(self.mainFrame)
		self.enterSpecies.bind("<KeyPress>", self.SpeciesEntered)
		self.enterSpecies.pack()
		self.importSpecies = tk.Button(self.mainFrame, text = "Import from file", command = self.ImportSpeciesFromFile)
		self.importSpecies.pack()

		self.enteredSpeciesFrame = tk.Frame(self.mainFrame, height = 200)
		self.deletedSpeciesStack = []
		self.enteredSpeciesFrame.pack()
		BindTree(self.mainFrame, "<Button-3>", self.RecoverDeletedSpecies)

	def SpeciesEntered(self, event):
		#Function for when the enter key is pressed in the enterspecies entry.
		if event.keysym == "Return":
			entered = ""
			entered = self.enterSpecies.get()
			self.AddSpecies(entered)
			self.enterSpecies.delete(0, len(entered))

	def AddSpecies(self, species, info = ""):
		newSpecies = SpeciesListItem((species, info), self.enteredSpeciesFrame, self.deletedSpeciesStack, self.speciesList)
		
		self.speciesList.append((species, info))
		newSpecies.BindRecoverDeletedSpecies(self.RecoverDeletedSpecies)

	def RecoverDeletedSpecies(self, event):
		if len(self.deletedSpeciesStack) > 0:
			species = self.deletedSpeciesStack.pop()
			species.Reappear()
			self.speciesList.append(species.info)

	def StartGame(self):
		for i in self.deletedSpeciesStack:
			i.cableText.destroy()
		del self.deletedSpeciesStack[:]
		self.UnpackSelf()
		self.gameFrame.PackSelf(self.speciesList)

	def ImportSpeciesFromFile(self):
		#Function for the import button. File dialog asking for a file. The file is read
		#and all the species are added.
		fileName = filedialog.askopenfilename(title = "select a file", filetypes = ( ('text files', '*.txt'), ('All files', '*.*') ))
		fileContent = ""
		with open(fileName, "r") as file:
			fileContent = file.read()
		fileContent = loads(fileContent)
		for i in fileContent:
			#you gotta format the json correctly! so it can be imported like this!
			info = insert_newlines(i["info"])
			self.AddSpecies(i["name"], info = info)
			

class SpeciesListItem:

	info = None
	dStack = None
	speciesList = None

	def __init__(self, info, parent, delstack, specieslist):
		#Info is a tuple of data in the species list. (NAME, INFORMATION). Setting the label text to the name.
		self.cableText = tk.Label(parent, text = info[0], cursor = "man")
		self.cableText.bind("<Button-1>", self.LeftClicked)
		self.cableText.pack()
		self.dStack = delstack
		self.info = info
		self.speciesList = specieslist
		
	def LeftClicked(self, event):
		self.dStack.append(self)
		self.cableText.pack_forget()
		self.speciesList.remove(self.info)
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
	#speciesDict keeps track of all the species and URLS to images of them.
	speciesDict = {}
	randomizedList = []
	currentImage = 0
	points = 0
		
	#make a list with the order of all the urls. just go through that loading only a few at a time

	def __init__(self, window):
		self.mainFrame = tk.Frame(window)
		self.speciesName = tk.Label(self.mainFrame, text = "Which species?")
		self.speciesInfo = tk.Label(self.mainFrame, text = "")
		self.imageCanvas = tk.Canvas(self.mainFrame, height = 400)
		self.showNameButton = tk.Button(self.mainFrame, text = "Show name", command = self.ShowName)
		self.guessSpeciesEntry = tk.Entry(self.mainFrame)
		self.guessSpeciesEntry.bind("<KeyPress>", self.GuessSpecies)
		self.speciesGuessResult = tk.Label(self.mainFrame, text = "Enter the species name")
		self.pointsLabel = tk.Label(self.mainFrame, text = "0 points")
		self.previousSpeciesButton = tk.Button(self.mainFrame, text = "Previous species", command = lambda: self.NextImage(-1))
		self.nextSpeciesButton = tk.Button(self.mainFrame, text = "Next species", command = lambda: self.NextImage(1))

	def PackSelf(self, speciesList):
		#ill fuck with the exact positioning later, once it actually works.
		self.speciesList = speciesList
		self.MakeOrder()
		self.speciesName.grid(row = 0, column = 0, sticky=tk.N+tk.E+tk.S+tk.W)
		self.pointsLabel.grid(row = 0, column = 1, sticky=tk.N+tk.E)
		self.imageCanvas.grid(row = 1, column = 0, sticky=tk.N+tk.E+tk.S+tk.W)
		self.showNameButton.grid(row = 2, column = 0, sticky=tk.N+tk.E+tk.S+tk.W)
		self.guessSpeciesEntry.grid(row = 3, column = 0, sticky=tk.N+tk.E+tk.S+tk.W)
		self.speciesGuessResult.grid(row = 3, column = 1, sticky=tk.N+tk.E+tk.S+tk.W)
		self.previousSpeciesButton.grid(row = 4, column = 0, sticky=tk.N+tk.E+tk.S+tk.W)
		self.nextSpeciesButton.grid(row = 4, column = 1, sticky=tk.N+tk.E+tk.S+tk.W)
		self.speciesInfo.grid(row = 5, column = 0, sticky=tk.N+tk.E+tk.S+tk.W)
		self.mainFrame.pack()
		#can i delete this function? I think i can but ill test it after everything else is working
		imageDownload = self.DownloadImage(self.randomizedList[1]["url"])
		self.randomizedList[1]["image"] = imageDownload
		self.NextImage(1)

	def MakeOrder(self):
		for species in self.speciesList:
			#Species[0] is the name. Species[1] is the data.
			speciesUrl = iNatUrl.format(species[0], random.randint(1, 10))
			jsonData = loads(r.get(speciesUrl).content)
			if jsonData['total_results'] == 0:
				print(species[0] + " has no results.")
			self.speciesDict[species[0]] = []
			for i in jsonData["results"]:
				#speciesDict gets the URLS to images of the species. {species1: [url1, url2...], species2: [url1, url2...]}
				self.speciesDict[species[0]].append(i["photos"][0]["url"])
				self.randomizedList.append({"species": species[0], "info": species[1], "url": i["photos"][0]["url"] })
		random.shuffle(self.randomizedList)

	def DownloadImage(self, url):
		#The url looks like this
		#https://inaturalist-open-data.s3.amazonaws.com/photos/257918386/square.jpeg
		#The following lines replace the square with medium/large. INaturalist has a few
		#Different sizes of their images - square, small, medium, large. Square is what
		#is given from the api call from before, but that's like super low res.
		index = url.find("square")
		url2 = url[:index]
		url2 = url2 + "medium"
		#url2 = url2 + "large"
		fileExtension = url[index + 6:]
		url = url2 + fileExtension
		response = r.get(url, stream = True)
		if response.status_code == 200:
			#getting the image and turning it into a PIL image to be displayed.
			img = Image.open(response.raw)
			img = ImageTk.PhotoImage(img)
			return img
		else:
			print("failed to grab image with status code " + str(response.status_code))
			return None

	def NextImage(self, increment):
		self.speciesName.config(text = "Which species?")
		self.speciesInfo.config(text = "")
		self.guessSpeciesEntry.delete(0, len(self.guessSpeciesEntry.get()))
		self.speciesGuessResult.config(text = "Enter the species name")
		self.currentImage += increment
		index = self.currentImage % len(self.randomizedList)
		self.LoadImage(self.randomizedList[index]["image"])
		
		nextImage = self.randomizedList[(self.currentImage + increment) % len(self.randomizedList)]
		imageDownload = self.DownloadImage(nextImage["url"])
		nextImage["image"] = imageDownload
		
		previousImage = self.randomizedList[(self.currentImage - (2 * increment)) % len(self.randomizedList)]
		

		#THIS STUFF NEEDS TO BE CHANGED. NO LONGER USING IMAGES STORED AS FILES!!
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

	def ShowName(self):
		self.speciesName.config(text = self.randomizedList[self.currentImage % len(self.randomizedList)]["species"])
		if "info" in self.randomizedList[self.currentImage % len(self.randomizedList)]:
			self.speciesInfo.config(text = self.randomizedList[self.currentImage % len(self.randomizedList)]["info"])

	def GuessSpecies(self, event):
		#Event fired when enter is pressed in the "guess the species" entry.
		if event.keysym == "Return":
			entered = self.guessSpeciesEntry.get()
			if entered.upper() == self.randomizedList[self.currentImage % len(self.randomizedList)]["species"].upper():
				#Check if its the name of the current species
				self.points += 1
				self.speciesGuessResult.config(text = "Correct!")
			else:
				self.points -= 1
				self.speciesGuessResult.config(text = "Inorrect :(")
			self.pointsLabel.config(text = str(self.points) + " points")
				

mainWindow = AppWindow()