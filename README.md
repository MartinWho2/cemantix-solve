# Cémantix-solver
This repository was created to make an automatic solver for cémantix. 
It now also includes the code of a reddit bot that gives some hints to the players. 

## Quick installation
Go to https://fauconnier.github.io/#data and download a word2vec file of your choice. 
I personally recommend the frWac with 494 MB (dim=700, cut=50,train=skip,lem,no_pos,no_phrase).

Clone the repository and launch the main cemantix solve.py script : 
```shell
git clone https://github.com/MartinWho2/cemantix-solve
cd cemantix-solve
python3 -m pip install -r requirements.txt
python3 cemantix-solve.py
```
ARGUMENTS :

`--help : shows you this page`

`--reddit : Sends some hints to the daily reddit page (please do not spam it!)`

`--no-ui : Launches the browser without graphical interface`

`--cemantle : Uses cemantle instead of cemantix (be careful to use an english word2vec file)`

`--vector-file : Select the name of the pretrained word2vec file you want to use (default is frWac_no_postag_no_phrase_700_skip_cut50.bin)`

`--browser : Chooses the browser to use (default is firefox) (possibilities : firefox, chrome, edge, safari)`


Credits for the word2vec file : https://fauconnier.github.io/#data