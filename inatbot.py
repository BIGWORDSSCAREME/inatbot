import random
import requests as r
import tkinter as tk
from tkinter import filedialog
from os import remove
from PIL import Image, ImageTk
from json import loads
from tkinter.ttk import *
import ttkthemes
import traceback

"""THINGS TO DO--
1. Make the program check for updates
3. Make the description of plants into a scrolling textbox
4. Add a way to create your own JSON plant lists


Some things could be cleaned up. But that's not the biggest deal. Commenting more is important.
Rename methods to using underscores. I think that convention looks ugly, but seems like classes use
uppercase and methods use underscores.

Might want to change the ShowName() function to show the name gotten from inaturalist. This could make it
so genuses n stuff can be used.
"""

version = "b0.9"

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

		self.window = ttkthemes.ThemedTk(theme = "adapta")	
				
		self.window.geometry("800x500")
		self.window.title("iNat study helper")

		self.gameScreen = Game(self.window)
		self.readyGameScreen = ReadyGame(self.window, self.gameScreen)
		self.mainMenuScreen = MainMenu(self.window, self.readyGameScreen)
		
		self.mainMenuScreen.PackSelf()
		
		self.window.report_callback_exception = self.handle_exception
				
		self.window.mainloop()
		
	def handle_exception(self, exception, value, tb):
		#Called upon exception. Just writes to log.txt.
		log = open("log.txt", "w")
		log.write("EXCEPTION: " + str(exception) + "\n")
		log.write(str(value) + "\n")
		for i in traceback.format_tb(tb):
			log.write(i)
		log.close()
		
class MainMenu(Screen):

	readyGameScreen = None

	def __init__(self, window, readygamescreen):
		self.mainFrame = Frame(window)
		self.readyGameScreen = readygamescreen
		self.topLabel = Label(self.mainFrame, text = "iNat study helper version: " + version)
		self.topLabel.pack()
		#lol
		self.venmoLabel = Label(self.mainFrame, text = "My venmo is @Sebastian-Ehlke lol")		
		self.venmoLabel.pack()
		self.gameButton = Button(self.mainFrame, text = "Start", command = self.ReadyGameButton)
		self.gameButton.pack()
	
	def ReadyGameButton(self):
		self.UnpackSelf()
		self.readyGameScreen.PackSelf()

	def PackSelf(self):
		#This checks for an update and creates a dialogue of one is available.
		req = r.get("https://bigwordsscareme.github.io/data/update.json")
		req = loads(req.content)
		updateVersion = req["version"]
		message = req["message"]
		if updateVersion != version:
			updateDialogue = tk.messagebox.showinfo("Update available", "Update version " + updateVersion + " available at https://github.com/BIGWORDSSCAREME/inatbot" + "\n" + message)
		self.mainFrame.pack(fill = "both", expand = True)



class ReadyGame(Screen):
	#deletedSpeciesStack keeps track of species left-clicked (deleted). For undeleteing them.
	deletedSpeciesStack = []
	#speciesList is a dict - {"name": species, "info": info}
	speciesList = []
	gameFrame = None
	
	def __init__(self, window, game):
		#GameFrame is the next screen - the screen of the game. for packing + unpacking this screen.
		self.gameFrame = game
		self.mainFrame = Frame(window)
		self.startGameButton = Button(self.mainFrame, text = "Start", command = self.StartGame)
		self.startGameButton.grid(column = 1, row = 0, columnspan = 2)
		self.enterSpecies = tk.Entry(self.mainFrame)
		self.enterSpecies.bind("<KeyPress>", self.SpeciesEntered)
		self.enterSpecies.grid(column = 1, row = 1, columnspan = 2)
		self.importSpecies = Button(self.mainFrame, text = "Import from file", command = self.ImportSpeciesFromFile)
		self.importSpecies.grid(column = 1, row = 2, columnspan = 2)
		

		#Using tk.Frame instead of the Frame (which would be ttk.Frame) because I want a border
		#Using a tk.Frame is probably the reason its a different color than the rest of the background.
		#the ttk Frames have a styled/colored background. I like how it looks though.
		self.canvasBorderFrame = tk.Frame(self.mainFrame, highlightbackground = "grey", highlightthickness = 2)
		self.canvasBorderFrame.grid(column = 1, row = 3)
		#tk.Canvas uses the tkinter canvas. Specifying nothing before a widget uses the stylable ttk widget.
		self.enteredSpeciesCanvas = tk.Canvas(self.canvasBorderFrame)
		self.enteredSpeciesCanvas.pack(anchor = "center")
		self.enteredSpeciesScrollbar = Scrollbar(self.mainFrame, orient = "vertical")
		self.enteredSpeciesScrollbar.grid(column = 2, row = 3, sticky = tk.N + tk.S)
		self.enteredSpeciesCanvas.configure(yscrollcommand = self.enteredSpeciesScrollbar.set)
		self.enteredSpeciesCanvas.bind("<Configure>", lambda e: self.enteredSpeciesCanvas.configure(scrollregion = self.enteredSpeciesCanvas.bbox("all")))
		self.enteredSpeciesFrame = Frame(self.enteredSpeciesCanvas)
		self.enteredSpeciesFrame.bind("<Configure>", self.ResetScrollregion)
		
		self.enteredSpeciesScrollbar.config(command = self.enteredSpeciesCanvas.yview)
		self.deletedSpeciesStack = []
		BindTree(self.mainFrame, "<Button-3>", self.RecoverDeletedSpecies)
		self.mainFrame.grid_columnconfigure((0, 3), weight = 1)

	def ResetScrollregion(self, event):
		self.enteredSpeciesCanvas.configure(scrollregion = self.enteredSpeciesCanvas.bbox("all"))

	def SpeciesEntered(self, event):
		#Function for when the enter key is pressed in the enterspecies entry.
		if event.keysym == "Return":
			entered = ""
			entered = self.enterSpecies.get()
			self.AddSpecies(entered)
			self.enterSpecies.delete(0, len(entered))

	def AddSpecies(self, species, info = ""):
		#Adds a species entered to the species list
		newSpecies = SpeciesListItem({"name": species, "info": info}, self.enteredSpeciesFrame, self.deletedSpeciesStack, self.speciesList)
		
		self.speciesList.append({"name": species, "info": info})
		newSpecies.BindRecoverDeletedSpecies(self.RecoverDeletedSpecies)

	def RecoverDeletedSpecies(self, event):
		#When right clicked, the last species deleted from the list reappears
		if len(self.deletedSpeciesStack) > 0:
			species = self.deletedSpeciesStack.pop()
			species.Reappear()
			self.speciesList.append(species)

	def StartGame(self):
		for i in self.deletedSpeciesStack:
			i.cableText.destroy()
		del self.deletedSpeciesStack[:]
		self.UnpackSelf()
		self.gameFrame.PackSelf(self.speciesList, self)

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
			
	def PackSelf(self):
		self.mainFrame.pack(fill = "both", expand = True)
		#This stuff needs to be done after the grid is set up so it can get the actual width of the grid.
		x0 = self.mainFrame.grid_bbox(1, 3)[2] / 2

		self.enteredSpeciesCanvas.create_window((x0, 0), window = self.enteredSpeciesFrame, anchor = "n")
		

class SpeciesListItem:

	#I'll probably want to change the name of this variable info.
	#Its the name and info of a species. Kinda confusing.
	info = None
	dStack = None
	speciesList = None

	def __init__(self, info, parent, delstack, specieslist):
		#Info is a tuple of data in the species list. (NAME, INFORMATION). Setting the label text to the name.
		self.cableText = Label(parent, text = info["name"], cursor = "man")
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
	mainFrame = None
	readyGameScreen = None

	def __init__(self, window):
		self.mainFrame = Frame(window)
		self.speciesName = Label(self.mainFrame, text = "Which species?")
		self.speciesInfo = Label(self.mainFrame, text = "")
		self.imageCanvas = tk.Canvas(self.mainFrame, height = 400, background = "black")
		self.showNameButton = Button(self.mainFrame, text = "Show name", command = self.ShowName)
		self.guessSpeciesEntry = Entry(self.mainFrame)
		self.guessSpeciesEntry.bind("<KeyPress>", self.GuessSpecies)
		self.speciesGuessResult = Label(self.mainFrame, text = "Enter the species name", justify = "left", anchor = "w")
		self.pointsLabel = Label(self.mainFrame, text = "0 points")
		self.previousSpeciesButton = Button(self.mainFrame, text = "Previous species", command = lambda: self.NextImage(-1))
		self.nextSpeciesButton = Button(self.mainFrame, text = "Next species", command = lambda: self.NextImage(1))
		self.exitButton = Button(self.mainFrame, text = "Back to enter species", command = self.BackButton)

		
		self.speciesName.grid(row = 0, column = 1, columnspan = 2)
		self.pointsLabel.grid(row = 0, column = 2, sticky = tk.N + tk.E, columnspan = 2, padx = (0, 100))
		self.imageCanvas.grid(row = 1, column = 1, columnspan = 2)
		self.showNameButton.grid(row = 2, column = 1, sticky = tk.N + tk.S + tk.E + tk.W, columnspan = 2)
		self.guessSpeciesEntry.grid(row = 3, column = 1, sticky = tk.E)
		self.speciesGuessResult.grid(row = 3, column = 2, sticky = tk.W)
		self.previousSpeciesButton.grid(row = 4, column = 1, sticky = tk.E)
		self.nextSpeciesButton.grid(row = 4, column = 2, sticky = tk.W)
		self.speciesInfo.grid(row = 5, column = 1, columnspan = 2)
		self.exitButton.grid(row = 6, column = 0, sticky = tk.W, columnspan = 2)
		self.mainFrame.grid_columnconfigure((0, 3), weight = 1)

	def PackSelf(self, speciesList, readygamescreen):
		self.readyGameScreen = readygamescreen
		self.speciesList = speciesList
		self.MakeOrder()
		self.mainFrame.pack(fill = "both", expand = True)
		
		#These next few lines are just loading the first and next few images to be shown basically.
		#The NextImage function does basically the same thing.
		while self.GetImageUrls(self.randomizedList[1]["name"]) == 0:
			self.RemoveSpeciesFromList(self.randomizedList[1]["name"])
		imageDownload = self.DownloadImage(self.speciesDict[self.randomizedList[1]["name"]][self.randomizedList[1]["index"]]["url"])
		self.speciesDict[self.randomizedList[1]["name"]][self.randomizedList[1]["index"]]["image"] = imageDownload
		self.NextImage(1)

	def BackButton(self):
		self.UnpackSelf()
		self.readyGameScreen.PackSelf()
	
	def MakeOrder(self):
		#Makes the order in which images are shown.
		newList = []
		for species in self.speciesList:
			for j in range(10):
				self.randomizedList.append({"name": species["name"], "index": j, "info": species["info"]})
		random.shuffle(self.randomizedList)
	
	def RemoveSpeciesFromList(self, species):
		#Function called when for whatever reason data can't be gotten for a species.
		#This probably doesn't have to be its own function, but its a relatively beefy ass line.
		self.randomizedList = list(filter(lambda i: i["name"] != species, self.randomizedList))
		#Filter returns an interable, list() turns it into a list
		#Filter filters based on that lambda stuff.

	def GetImageUrls(self, species):
		#Every time you get to a new species where the images haven't been loaded, this fetches the images URLs.
		#The iNatUrl is
		#https://api.inaturalist.org/v1/observations?photos=true&taxon_name={}&identifications=most_agree&quality_grade=research&locale=en-US&page={}&per_page=10&order=desc&order_by=created_at
		#The species name is the taxon name in the url. The random int is the page number so
		#It doesn't repeat pictures too often.
		speciesUrl = iNatUrl.format(species, random.randint(1, 3))
		#The previous line changes which page to get results from. We take 10 from each page.
		#If something doesn't have atleast 30 results, this will fucking things up in the NextImage function.
		request = None
		try:
			request = r.get(speciesUrl)
			jsonData = loads(request.content)
		except:
			return 0
		if jsonData['total_results'] == 0:
			print(species + " has no results.")
			return 0
		self.speciesDict[species] = []
		for i in jsonData["results"]:
			self.speciesDict[species].append({"url": i["photos"][0]["url"], "image": None})
		random.shuffle(self.speciesDict[species])

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
		#all this modulo math just makes it iterate through the list
		index = self.currentImage % len(self.randomizedList)
		#This line is so fucking beefy lmao. I'm sorry to whoever has to read this bullshit.
		#But--explanation.
		#speciesDict is a dict (wow) of species (no way). Go to the species name, then for each species
		#There is a list of dicts. These dicts have URLS for images, and the PIL images themselves.
		#randomizedList has the name of the species and index of the image to be grabbed.
		currentImage = self.randomizedList[index]
		self.LoadImage(self.speciesDict[currentImage["name"]][currentImage["index"]]["image"])
		
		nextImage = self.randomizedList[(self.currentImage + increment) % len(self.randomizedList)]
		#Next image name and index. Easier to save them as a variable just so i don't have to keep typing out the whole thing.
		NIName = nextImage["name"]
		NIIndex = nextImage["index"]
		if not (nextImage["name"] in self.speciesDict):
			while self.GetImageUrls(nextImage["name"]) == 0:
				#This means that it failed getting images for this species. Should also make sure
				#To get the new next image ready!
				print("wuh-oh " + nextImage["name"] + " not found on iNaturalist")
				self.RemoveSpeciesFromList(nextImage["name"])
				nextImage = self.randomizedList[(self.currentImage + increment) % len(self.randomizedList)]
				#Set nextImage again after removing the previous one (that wasn't found) from the list.
				NIName = nextImage["name"]
				NIIndex = nextImage["index"]
		#If the below line is causing an error, it might be something to do with what is described
		#in the comments of the GetImageUrls function.
		if self.speciesDict[NIName][NIIndex]["image"] == None:
			imageDownload = self.DownloadImage(self.speciesDict[NIName][NIIndex]["url"])
			self.speciesDict[NIName][NIIndex]["image"] = imageDownload
		
		#previousImage = self.randomizedList[(self.currentImage - (2 * increment)) % len(self.randomizedList)]
		#Might need to find out if theres a pil.close() thing for the images.

	def LoadImage(self, image):
		self.imageCanvas.delete("all")
		self.imageCanvas.create_image(0, 0, anchor = tk.NW, image = image)
		self.imageCanvas.image = image

	def ShowName(self):
		species = self.randomizedList[self.currentImage % len(self.randomizedList)]
		self.speciesName.config(text = species["name"])
		
		if len(species["info"]) > 0:
			#If there is information about the species entered, it will show up on screen.
			self.speciesInfo.config(text = species["info"])

	def GuessSpecies(self, event):
		#Event fired when enter is pressed in the "guess the species" entry.
		if event.keysym == "Return":
			entered = self.guessSpeciesEntry.get()
			if entered.upper() == self.randomizedList[self.currentImage % len(self.randomizedList)]["name"].upper():
				#Check if its the name of the current species
				self.points += 1
				self.speciesGuessResult.config(text = "Correct!")
			else:
				self.points -= 1
				self.speciesGuessResult.config(text = "Inorrect :(")
			self.pointsLabel.config(text = str(self.points) + " points")

	def UnpackSelf(self):
		self.speciesList = []
		self.randomizedList = []
		self.speciesDict = {}
		self.imageCanvas.delete("all")
		self.currentImage = 0
		self.mainFrame.pack_forget()

				
mainWindow = AppWindow()