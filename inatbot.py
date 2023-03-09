import random
import requests as r
import tkinter as tk
from tkinter import filedialog
from os import remove
from PIL import Image, ImageTk
from json import loads, dump
from tkinter.ttk import *
from sys import exc_info
import ttkthemes
import traceback

"""THINGS TO DO--

Some things could be cleaned up. But that's not the biggest deal. Commenting more is important.
Rename methods to using underscores. I think that convention looks ugly, but seems like classes use
uppercase and methods use underscores.

Might want to change the ShowName() function to show the name gotten from inaturalist. This could make it
so genuses n stuff can be used.
"""
version = "b0.9"
catImages = [None, None]
catEnabled = False
#For some fucking reason it doesn't let me set catenabled to true from a class function.
#Maybe because it thinks its a local variable but why i have no idea.
def CatEnabledFunc():
	catEnabled = True

random.seed()
iNatUrl = "https://api.inaturalist.org/v1/observations?photos=true&taxon_name={}&identifications=most_agree&quality_grade=research&locale=en-US&page={}&per_page=10&order=desc&order_by=created_at"

def handle_exception(exception, value, tb):
	#Called upon exception. Just writes to log.txt.
	log = open("log.txt", "w")
	log.write("EXCEPTION: " + str(exception) + "\n")
	log.write(str(value) + "\n")
	for i in traceback.format_tb(tb):
		log.write(i)
	log.close()

def BindTree(node, event, function):
	node.bind(event, function)
	
	for child in node.children.values():
		BindTree(child, event, function)

def insert_newlines(string, every=64):
	#stole this function from stackoverflow. adds new lines every 64 characters.
	return '\n'.join(string[i:i+every] for i in range(0, len(string), every))

def GetCatImages():
	cat = r.get("https://bigwordsscareme.github.io/inatbot/images/cats/generalsalmon.jpg", stream = True)
	if cat.status_code == 200:
		img = Image.open(cat.raw)
		catImages[0] = img
	cat = r.get("https://bigwordsscareme.github.io/inatbot/images/cats/smokey.jpg", stream = True)
	if cat.status_code == 200:
		img = Image.open(cat.raw)
		catImages[1] = img


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
				
		self.window.state("zoomed")
		self.window.title("iNat study helper")

		self.mainMenuScreen = MainMenu(self.window)
		
		self.mainMenuScreen.PackSelf()
		
		self.window.report_callback_exception = handle_exception
				
		self.window.mainloop()
		
class MainMenu(Screen):

	readyGameScreen = None
	studySetMakerScreen = None

	def __init__(self, window):
		GetCatImages()
		self.mainFrame = Frame(window)
		self.studySetMakerScreen = StudySetMaker(window)
		self.readyGameScreen = ReadyGame(window)
		self.topLabel = Label(self.mainFrame, text = "iNat study helper version: " + version)
		self.topLabel.pack()
		#lol
		self.venmoLabel = Label(self.mainFrame, text = "My venmo is @Sebastian-Ehlke lol")		
		self.venmoLabel.pack()
		self.goToReadyGameButton = Button(self.mainFrame, text = "Start studying!", command = self.GoToReadyGame)
		self.goToReadyGameButton.pack()
		self.GoToStudySetButtonMaker = Button(self.mainFrame, text = "Create study set", command = self.GoToStudySetMaker)
		self.GoToStudySetButtonMaker.pack()
		self.catImageCanvas = None
		self.catLabel = None

	
	def GoToReadyGame(self):
		#Self explanitory. Called by the gotoreadygamebutton
		self.UnpackSelf()
		self.readyGameScreen.PackSelf(self)

	def GoToStudySetMaker(self):
		#Self explanitory. Called by the gotostudysetmakerbutton
		self.UnpackSelf()
		self.studySetMakerScreen.PackSelf(self)

	def PackSelf(self):
		#This checks for an update and creates a dialogue of one is available.
		req = r.get("https://bigwordsscareme.github.io/inatbot/data/update.json")
		try:
			req = loads(req.content)
			updateVersion = req["version"]
			message = req["message"]
			if version != updateVersion:
				updateDialogue = tk.messagebox.showinfo("Update available", "Update version " + updateVersion + " available at https://github.com/BIGWORDSSCAREME/inatbot" + "\n" + message)
		except:
			updateDialogue = tk.messagebox.showinfo("Update available", "Error fetching update information. Update may be available at https://github.com/BIGWORDSSCAREME/inatbot")
		self.mainFrame.pack(fill = "both", expand = True)
		if catImages[0] != None and self.catLabel == None:
		#Check if the cat image was retrieved and also if this chunk of code has already been run.
		#If it has already been run, it'll run it again but that doesn't really do anything other
		#Than extending the height of the canvas and making it look ugly
			self.catImageCanvas = tk.Canvas(self.mainFrame, height = 350)
			self.catImageCanvas.pack()
			catImages[0] = catImages[0].resize((438, 350), Image.LANCZOS)
			catImages[0] = ImageTk.PhotoImage(catImages[0])
			self.catImageCanvas.create_image(0, 0, anchor = tk.NW, image = catImages[0])
			self.catLabel = Label(self.mainFrame, text = "This is my mom's (MY) cat General Salmon.\nShe likes meowing very loudly, licking plastic, and eating plants.\nA true botanist.", justify = "center")
			self.catLabel.pack()


class ReadyGame(Screen):
	#---I SHOULD PROBABLY KEEP THE OTHERS SCREENS DEFINED IN EITHER PACKSELF OR INIT. BOTH IS CONFUSING---#
	#deletedSpeciesStack keeps track of species left-clicked (deleted). For undeleteing them.
	deletedSpeciesStack = []
	#speciesList is a dict - {"name": species, "info": info}
	speciesList = []
	gameScreen = None
	mainMenu = None
	
	def __init__(self, window):
		self.gameScreen = Game(window)
		self.mainFrame = Frame(window)
		self.instructionLabel = Label(self.mainFrame, text = "Type a species name (e.g Viola sororia) then press enter to add to the list.\nCheck your spelling!", justify = "center")
		self.instructionLabel.grid(column = 1, row = 0)
		self.startGameButton = Button(self.mainFrame, text = "Start", command = self.StartGame)
		self.startGameButton.grid(column = 1, row = 1, columnspan = 2)
		self.enterSpecies = tk.Entry(self.mainFrame)
		self.enterSpecies.bind("<KeyPress>", self.SpeciesEntered)
		self.enterSpecies.grid(column = 1, row = 2, columnspan = 2)
		self.importSpecies = Button(self.mainFrame, text = "Import from file", command = self.ImportSpeciesFromFile)
		self.importSpecies.grid(column = 1, row = 3, columnspan = 2)
		
		#Using tk.Frame instead of the Frame (which would be ttk.Frame) because I want a border
		#Using a tk.Frame is probably the reason its a different color than the rest of the background.
		#the ttk Frames have a styled/colored background. I like how it looks though.
		self.canvasBorderFrame = tk.Frame(self.mainFrame, highlightbackground = "grey", highlightthickness = 2)
		self.canvasBorderFrame.grid(column = 1, row = 4)
		#tk.Canvas uses the tkinter canvas. Specifying nothing before a widget uses the stylable ttk widget.
		self.enteredSpeciesCanvas = tk.Canvas(self.canvasBorderFrame)
		self.enteredSpeciesCanvas.pack(anchor = "center")
		self.enteredSpeciesScrollbar = Scrollbar(self.mainFrame, orient = "vertical")
		self.enteredSpeciesScrollbar.grid(column = 2, row = 4, sticky = tk.N + tk.S)
		self.enteredSpeciesCanvas.configure(yscrollcommand = self.enteredSpeciesScrollbar.set)
		self.enteredSpeciesCanvas.bind("<Configure>", lambda e: self.enteredSpeciesCanvas.configure(scrollregion = self.enteredSpeciesCanvas.bbox("all")))
		self.enteredSpeciesFrame = Frame(self.enteredSpeciesCanvas)
		self.enteredSpeciesFrame.bind("<Configure>", self.ResetScrollregion)
		
		self.enteredSpeciesScrollbar.config(command = self.enteredSpeciesCanvas.yview)
		self.deletedSpeciesStack = []
		BindTree(self.mainFrame, "<Button-3>", self.RecoverDeletedSpecies)
		
		self.helpLabel = Label(self.mainFrame, justify = "center", text = "Click on a species to remove it from the list\nRight click to recover the last deleted species.")
		self.helpLabel.grid(column = 1, row = 5)

		#In a future version I should make this button in the same place as the back button on the game screen.
		self.backToMenuButton = Button(self.mainFrame, text = "Back to main menu", command = self.BackToMainMenu)
		self.backToMenuButton.grid(column = 0, row = 7, columnspan = 2, sticky = tk.S + tk.W, padx = (50, 0), pady = (0, 25))

		#Column configure makes the specified columns (0 and 3) have a different weight.
		#Weight makes them fill space basically, so it pushes the things in between 0 and 3 to the center
		self.mainFrame.grid_columnconfigure((0, 3), weight = 1)
		#This is necessary to make the bottom of the grid fill up the screen
		self.mainFrame.grid_rowconfigure(7, weight = 1)

	def PackSelf(self, mainmenu = None):
		if mainmenu != None:
			self.mainMenu = mainmenu
		self.mainFrame.pack(fill = "both", expand = True)
		#This stuff needs to be done after the grid is set up so it can get the actual width of the grid.
		x0 = self.mainFrame.grid_bbox(1, 3)[2] / 2

		self.enteredSpeciesCanvas.create_window((x0, 0), window = self.enteredSpeciesFrame, anchor = "n")

	def ResetScrollregion(self, event):
		#This function just makes sure the size of the scrollbar is right... I think.
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
		if len(self.speciesList) == 0:
			return
		for i in self.deletedSpeciesStack:
			i.cableText.destroy()
		del self.deletedSpeciesStack[:]
		self.UnpackSelf()
		self.gameScreen.PackSelf(self.speciesList, self)
	
	def BackToMainMenu(self):
		self.UnpackSelf()
		self.mainMenu.PackSelf()

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

	def EnableCat(self):
		catImages[1] = catImages[1].resize((360, 640), Image.LANCZOS)
		catImages[1] = ImageTk.PhotoImage(catImages[1])
		self.enteredSpeciesCanvas.create_image(12, 0, anchor = tk.NW, image = catImages[1])
		self.helpLabel.configure(text = "This is my mom's (MY) cat Smokey. She likes sleeping and licking people.\nShe is proud of you.")
		CatEnabledFunc()



class SpeciesListItem:

	#I'll probably want to change the name of this variable info.
	#Its the name and info of a species. Kinda confusing.
	info = None
	dStack = None
	speciesList = None

	def __init__(self, info, parent, delstack, specieslist):
		#Info is a tuple of data in the species list. (NAME, INFORMATION). Setting the label text to the name.
		self.cableText = Label(parent, text = "", cursor = "pirate", justify = "center")
		self.cableText.bind("<Button-1>", self.LeftClicked)
		self.cableText.pack()
		self.dStack = delstack
		self.info = info
		self.speciesList = specieslist
		self.UpdateText()
		
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

	def UpdateText(self):
		self.cableText.configure(text = self.info["name"] + ": " + self.info["info"][:32] + "...")

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

		self.speciesInfoFrame = Frame(self.mainFrame)
		self.speciesInfoScrollbar = Scrollbar(self.speciesInfoFrame, orient = "vertical")
		#bd -2 gets rid of the canvas border which is set at 2 pixels automatically
		self.speciesInfoCanvas = tk.Canvas(self.speciesInfoFrame, height = 50, bd = -2)
		self.speciesInfoScrollingFrame = Frame(self.speciesInfoCanvas, height = 50)
		self.speciesInfoScrollingFrame.bind("<Configure>", self.ResetScrollregion)
		self.speciesInfo = Label(self.speciesInfoScrollingFrame, text = "", justify = "center")
		self.speciesInfoCanvas.configure(yscrollcommand = self.speciesInfoScrollbar.set)
		self.speciesInfoCanvas.bind("<Configure>", lambda e: self.speciesInfoCanvas.configure(scrollregion = self.speciesInfoCanvas.bbox("all")))
		self.speciesInfoScrollbar.config(command = self.speciesInfoCanvas.yview)
		self.speciesInfoCanvas.grid(column = 1, row = 0)
		self.speciesInfoScrollbar.grid(column = 2, row = 0, sticky = tk.N + tk.S)
		self.speciesInfoFrame.grid_columnconfigure((0, 3), weight = 1)
		self.speciesInfo.pack()
		#Below line makes it so the frame is the size of the canvas, fills the canvas
		self.speciesInfoCanvasFrame = self.speciesInfoCanvasFrame = self.speciesInfoCanvas.create_window((0, 0), window = self.speciesInfoScrollingFrame, anchor = "n")
		self.speciesInfoCanvas.bind("<Configure>", self.FrameWidth)

		self.imageCanvas = tk.Canvas(self.mainFrame, height = 400, background = "black")
		self.showNameButton = Button(self.mainFrame, text = "Show name", command = self.ShowName)
		self.guessSpeciesEntry = Entry(self.mainFrame)
		self.guessSpeciesEntry.bind("<KeyPress>", self.GuessSpecies)
		self.speciesGuessResultFrame = Frame(self.mainFrame)
		self.speciesGuessResult = Label(self.speciesGuessResultFrame, text = "Enter the species name", justify = "center", anchor = "center")
		self.pointsLabel = Label(self.mainFrame, text = "0 points")
		self.previousSpeciesButton = Button(self.mainFrame, text = "Previous species", command = lambda: self.NextImage(-1))
		self.nextSpeciesButton = Button(self.mainFrame, text = "Next species", command = lambda: self.NextImage(1))
		self.exitButton = Button(self.mainFrame, text = "Back to enter species", command = self.BackButton)

		self.pointsLabel.grid(row = 0, column = 2, sticky = tk.N + tk.E, columnspan = 2, padx = (0, 100))
		self.speciesName.grid(row = 0, column = 1, columnspan = 2)
		self.imageCanvas.grid(row = 1, column = 1, columnspan = 2)
		self.showNameButton.grid(row = 2, column = 1, sticky = tk.N + tk.S + tk.E + tk.W, columnspan = 2)
		self.guessSpeciesEntry.grid(row = 3, column = 1, sticky = tk.E + tk.W)
		self.speciesGuessResultFrame.grid(row = 3, column = 2, sticky = tk.W + tk.E)
		self.speciesGuessResult.pack(fill = "both", expand = True)
		self.previousSpeciesButton.grid(row = 4, column = 1, sticky = tk.E + tk.W)
		self.nextSpeciesButton.grid(row = 4, column = 2, sticky = tk.E + tk.W)
		self.exitButton.grid(row = 6, column = 0, sticky = tk.W + tk.S, columnspan = 2, padx = (50, 0), pady = (0, 25))
		
		#Row configure/column configuremake these columns/rows fill space
		self.mainFrame.grid_columnconfigure((0, 3), weight = 2)
		self.mainFrame.grid_rowconfigure((6), weight = 1)

	def PackSelf(self, speciesList, readygamescreen):

		self.speciesInfoCanvas.configure(width = self.speciesInfoCanvas.winfo_width() - self.speciesInfoScrollbar.winfo_width())

		self.readyGameScreen = readygamescreen
		self.speciesList = speciesList
		self.MakeOrder()
		self.mainFrame.pack(fill = "both", expand = True)
		#If the minsize is smthn else then itll fuck w the buttons. If the text changes, the whole column size will change.
		#This prevents that.
		self.mainFrame.grid_columnconfigure((2), minsize = self.speciesInfoCanvas.winfo_width() / 2)
		self.mainFrame.grid_columnconfigure((1), minsize = self.speciesInfoCanvas.winfo_width() / 2)


		self.nextSpeciesButton.configure(width = self.imageCanvas.winfo_width() / 2)
		self.previousSpeciesButton.configure(width = self.imageCanvas.winfo_width() / 2)
		self.speciesGuessResultFrame.configure(width = self.mainFrame.grid_bbox(4, 2)[2])
		
		#These next few lines are just loading the previous and next images to be shown basically.
		#The NextImage function does basically the same thing. Could probably make this better.

		while self.GetImageUrls(self.randomizedList[1]["name"]) == 0:
			self.RemoveSpeciesFromList(self.randomizedList[1]["name"])
		imageDownload = self.DownloadImage(self.speciesDict[self.randomizedList[1]["name"]][self.randomizedList[1]["index"]]["url"])
		self.speciesDict[self.randomizedList[1]["name"]][self.randomizedList[1]["index"]]["image"] = imageDownload

		while self.GetImageUrls(self.randomizedList[0]["name"]) == 0:
			self.RemoveSpeciesFromList(self.randomizedList[0]["name"])
		imageDownload = self.DownloadImage(self.speciesDict[self.randomizedList[0]["name"]][self.randomizedList[0]["index"]]["url"])
		self.speciesDict[self.randomizedList[0]["name"]][self.randomizedList[0]["index"]]["image"] = imageDownload

		self.NextImage(1)
		

	def ResetScrollregion(self, event):
		#This function just makes sure the size of the scrollbar is right... I think.
		self.speciesInfoCanvas.configure(scrollregion = self.speciesInfoCanvas.bbox("all"))

	def FrameWidth(self, event):
		canvasWidth = event.width
		self.speciesInfoCanvas.itemconfig(self.speciesInfoCanvasFrame, width = canvasWidth)

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
		if species in self.speciesDict:
			#If this species is already in the keys, just return.
			return
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
		self.speciesInfoFrame.grid_forget()
		self.speciesName.config(text = "Which species?")
		self.speciesInfo.config(text = "", justify = "center")
		self.guessSpeciesEntry.delete(0, len(self.guessSpeciesEntry.get()))
		self.speciesGuessResult.config(text = "Enter the species name")
		self.currentImage += increment
		#all this modulo math just makes it iterate through the list
		index = self.currentImage % len(self.randomizedList)
		#This next line is mildly beefy lmao. I'm sorry to whoever has to read this bullshit.
		#But--explanation.
		#speciesDict is a dict (wow) of species (no way). Go to the species name, then for each species
		#There is a list of dicts. These dicts have URLS for images, and the PIL images themselves.
		#randomizedList has the name of the species and index of the image to be grabbed.
		#NEED TO CHANGE CURRENTIMAGE AND SELF.CURRENTIMAGE. Just the names lol wtf was i thinking.
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

	def ShowName(self):
		species = self.randomizedList[self.currentImage % len(self.randomizedList)]
		self.speciesName.config(text = species["name"])
		
		if len(species["info"]) > 0:
			#If there is information about the species entered, it will show up on screen.
			self.speciesInfo.config(text = species["info"])
			self.speciesInfoFrame.grid(row = 5, column = 1, columnspan = 2)

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
			if self.points == 100 and catEnabled == False:
				self.speciesGuessResult.config(text = "New cat unlocked! Press back!")
				self.readyGameScreen.EnableCat()
			self.pointsLabel.config(text = str(self.points) + " points")

	def UnpackSelf(self):
		self.speciesList = []
		self.randomizedList = []
		self.speciesDict = {}
		self.imageCanvas.delete("all")
		self.currentImage = 0
		self.mainFrame.pack_forget()

class StudySetMaker(Screen):
	#I copied and pasted the ready game screen for this one.
	#DRY or whatever. don't care.
	#I'll fix it later.
	deletedSpeciesStack = []
	#speciesList is a dict - {"name": species, "info": info}
	speciesList = []
	mainMenu = None

	#For keeping track of which species is the last one that was typed in.
	#The entry box alternates between adding a species, and adding information about it.
	#This is like pretty clearly a shitty way to do it, but I'll figure out a better way later.
	currentSpecies = None
	
	def __init__(self, window):
		self.mainFrame = Frame(window)
		self.instructionLabel = Label(self.mainFrame, text = "Type a species name (e.g Viola sororia) then press enter to add to the list.\nCheck your spelling!", justify = "center")
		self.instructionLabel.grid(column = 1, row = 0)
		self.saveSetButton = Button(self.mainFrame, text = "Save", command = self.SaveToFile)
		self.saveSetButton.grid(column = 1, row = 1, columnspan = 2)
		self.enterSpecies = tk.Entry(self.mainFrame)
		self.enterSpecies.bind("<KeyPress>", self.StuffEntered)
		self.enterSpecies.grid(column = 1, row = 2, columnspan = 2)
		
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
		
		self.helpLabel = Label(self.mainFrame, justify = "center", text = "Click on a species to remove it from the list\nRight click to recover the last deleted species.")
		self.helpLabel.grid(column = 1, row = 4)

		#In a future version I should make this button in the same place as the back button on the game screen.
		self.backToMenuButton = Button(self.mainFrame, text = "Back to main menu", command = self.BackToMainMenu)
		self.backToMenuButton.grid(column = 0, row = 5, columnspan = 2, sticky = tk.S + tk.W, padx = (50, 0), pady = (0, 25))

		#Column configure makes the specified columns (0 and 3) have a different weight.
		#Weight makes them fill space basically, so it pushes the things in between 0 and 3 to the center
		self.mainFrame.grid_columnconfigure((0, 3), weight = 1)
		#This is necessary to make the bottom of the grid fill up the screen
		self.mainFrame.grid_rowconfigure(5, weight = 1)

	def PackSelf(self, mainmenu = None):
		if mainmenu != None:
			self.mainMenu = mainmenu
		self.mainFrame.pack(fill = "both", expand = True)
		#This stuff needs to be done after the grid is set up so it can get the actual width of the grid.
		x0 = self.mainFrame.grid_bbox(1, 3)[2] / 2

		self.enteredSpeciesCanvas.create_window((x0, 0), window = self.enteredSpeciesFrame, anchor = "n")

	def ResetScrollregion(self, event):
		#This function just makes sure the size of the scrollbar is right... I think.
		self.enteredSpeciesCanvas.configure(scrollregion = self.enteredSpeciesCanvas.bbox("all"))

	def StuffEntered(self, event):
		#Function for when the enter key is pressed in the enterspecies entry.
		if event.keysym == "Return":
			entered = ""
			entered = self.enterSpecies.get()
			self.enterSpecies.delete(0, len(entered))
			if self.currentSpecies == None:
				#If the last thing entered was not a species, then we add a species.
				self.AddSpecies(entered)
				self.instructionLabel.configure(text = "Now enter information about the species--\nLike the family, distinguishing characteristics, etc.", foreground = "red")
				
			else:
				#if the last thing entered was a species, then we add info about that species
				self.AddInfo(self.currentSpecies.info, entered)
				self.instructionLabel.configure(text = "Type a species name (e.g Viola sororia) then press enter to add to the list.\nCheck your spelling!", foreground = "black")

	def AddSpecies(self, species, info = ""):
		#Adds a species entered to the species list
		self.currentSpecies = SpeciesListItem({"name": species, "info": ""}, self.enteredSpeciesFrame, self.deletedSpeciesStack, self.speciesList)
		
		self.speciesList.append(self.currentSpecies.info)
		self.currentSpecies.BindRecoverDeletedSpecies(self.RecoverDeletedSpecies)
		
	def AddInfo(self, dict, info):
		#The dict passed is the dictionary held by a SpeciesListItem object, it is the info attribute.
		dict["info"] = info
		self.currentSpecies.UpdateText()
		self.currentSpecies = None

	def RecoverDeletedSpecies(self, event):
		#When right clicked, the last species deleted from the list reappears
		if len(self.deletedSpeciesStack) > 0:
			species = self.deletedSpeciesStack.pop()
			species.Reappear()
			self.speciesList.append(species)
	
	def SaveToFile(self):
		if len(self.speciesList) > 0:
			try:
				extension = [('Text Document', '*.txt')]
				file = filedialog.asksaveasfile(filetypes = extension, defaultextension = '.txt')
				dump(self.speciesList, file)
				file.close()
				self.instructionLabel.configure(text = "Your study set has been written to a file!\nTo use it, press the 'import from file' button on the studying start screen.", foreground = "green")
			except Exception as e:
				eInfo = exc_info()
				handle_exception(e, eInfo[1], eInfo[2])
				self.instructionLabel.configure(text = "There was an error writing your data to a file.\nmb", foreground = "red")

	def BackToMainMenu(self):
		self.instructionLabel.configure(text = "Type a species name (e.g Viola sororia) then press enter to add to the list.\nCheck your spelling!", foreground = "black")
		self.UnpackSelf()
		self.mainMenu.PackSelf()





				
mainWindow = AppWindow()