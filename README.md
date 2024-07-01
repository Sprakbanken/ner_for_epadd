# NER for ePADD
Dette repoet inneholder et skript som henter egennavn (named entities) fra teksten i en .mbox-fil og skriver disse til ePADD EntityList-formatet. 
Egennavn som blir funnet vil legges til, ikke overskrive de allerede eksisterende entitetene som har blitt funnet av ePADD.

## Installering
Du trenger python 3.x og pip   
Lag gjerne et virtuelt miljø og installer avhengigheter slik:  
```
python3 -m venv venv_epadd
. venv_epadd/bin/activate
pip install .
```

## Kjøring
Kjør `python3 ner_for_epadd.py --help` for forklaring av argumenter.

Hvis defaultargumenter ellers passer fint, kan du kjøre opp skriptet slik: 
```
python3 ner_for_epadd.py --mbox [path_til_mbox_fil] --entity_books [path_til_entitybooks]
```

