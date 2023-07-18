# Cémantix-solver
This repository was created to make an automatic solver for cémantix. 
It now also includes the code of a reddit bot that gives some hints to the players. 

## Quick installation
### Get the database
For a french database, go to https://fauconnier.github.io/#data and download a word2vec file of your choice. 
I personally recommend the frWac with 229 MB (dim=500, cut=100,train=skip,lem,no_pos,no_phrase).

For an english one, go to https://code.google.com/archive/p/word2vec/ and download the file `GoogleNews-vectors-negative300.bin.gz` (I only found one).
However for this one, the script will not really work properly because the database is just too large...
### Get the script

Clone the repository and launch the main cemantix solve.py script : 
```shell
git clone https://github.com/MartinWho2/cemantix-solve
cd cemantix-solve
python3 -m pip install -r requirements.txt
python3 cemantix-solve.py
```
ARGUMENTS : (All arguments are optional)

`--help : shows you this page`

`--reddit : Sends some hints to the daily reddit page (please do not spam it!)`

`--no-ui : Launches the browser without graphical interface`

`--cemantle : Uses cemantle instead of cemantix (be careful to use an english word2vec file)`

`--vector-file : Select the name of the pretrained word2vec file you want to use (default is frWac_no_postag_no_phrase_500_skip_cut100.bin)`

`--browser : Chooses the browser to use (default is chrome) (possibilities : firefox, chrome, edge, safari, chromium)`

`--browser-path : Only use if the path of your browser can't be detected by selenium (aka using chromium)`

`--abs-path : Only use if you are not launching the program from the same folder as the python file`

Credits for the word2vec file : https://fauconnier.github.io/#data, google