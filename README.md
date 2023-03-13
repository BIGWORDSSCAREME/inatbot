# iNaturalist study helper by BIGWORDSSSCAREME

## Downloads

### Windows: https://bigwordsscareme.github.io/inatbot/versions/windows/b0.9/inatbot.exe

### Mac: https://bigwordsscareme.github.io/inatbot/versions/mac/b0.9/inatbot

<sub>List of exam 1 plants for importing and studying--- https://bigwordsscareme.github.io/inatbot/data/plants/exam1plants.zip </sub>

#### ***Windows and mac anti-virus might get angry at these files.***

On windows there will be a pop-up saying "windows protected your PC". You can just click more info>Run Anyways.

On mac it is a larger pain in the ass to run, but it still works fine. Here's how you do it --
1. Open the terminal. If you don't know how to do this, just spotlight search "terminal" and it should come up.
2. In the terminal type "cd Downloads" By default downloads go to your downloads directory.  cd stands for change directory, so with this command you're just telling
the terminal that you want to go to the downloads directory -- where that file is.
3. In the terminal type "chmod +x inatbot" This command gives that inatbot file permissions to open basically.
4. In the terminal type "./inatbot" This command runs the program.
5. After you open it one time, you can right-click the inatbot file and under the "open with" tab set the default program to the terminal. After you do this, you can
move the inatbot file to wherever. You could put it on your desktop or another folder or wherever you want. And now if you double-click it, it should just open without
having to use the terminal or anything.

If you need any help with this, just email me. It may look like a lot but I can do this in two minutes so it is really not a problem.

## Other stuff

takes research grade images from inaturalist and puts them on your screen for you to ID. Enter the names of species, then press enter. For studying/learning to ID stuff 
from a bunch of different images.

The "List of exam 1 plants" is a .zip archive of .TXT json files about 80 plants that I used to study for exam 1. If you wanna mess around with them, just download it, 
extract the archive and on after clicking the "start studying!" button in the program, you can click the "Import from file button".

You can make study sets. All they are is a list of species names (e.g Viola sororia) followed by details about (maybe the common name, family, etc. Whatever you want to 
remember about it.) Once you make a list of species and extra information about them, you can save the file, then import it when studying to load all of those species 
and whatever information you wrote about them.

right now it is functional but it is not perfect. i plan on working on this more when i get the chance. this was born out of an incredible amount of boredom and an 
intense determination to not do my schoolwork, and those vices will likely be what maintains it.

any questions/whatever/ERRORS (please send me errors so i can fix them, they'll pop up in a log.txt file!) can be directed at ehlke2@wisc.edu

## Stuff for programmers (don't worry about this)

uses python libraries requests, tkinter, ttkthemes, PIL.

https://pypi.org/project/requests/

https://www.tutorialspoint.com/how-to-install-tkinter-in-python

https://ttkthemes.readthedocs.io/en/latest/installation.html

https://pillow.readthedocs.io/en/stable/installation.html
