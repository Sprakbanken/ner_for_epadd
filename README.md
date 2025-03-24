# NER for ePADD
This repo contains a script the extracts named entities from the text of an .mbox file.

## Installation
You need python >=3.10, pip, and venv   
Create a virtual environment and install dependencies like this:  
```
python3 -m venv venv_epadd
. venv_epadd/bin/activate
pip install .
```

## Running the script
Run `python3 ner_for_epadd.py --help` for argument explanation.

If the default argumentents fit, you can run the script like this: 
```
python3 ner_for_epadd.py --mbox [path_to_mbox_file]
```

You can use the output file as input to [https://github.com/NationalLibraryOfNorway/epadd-nb/tree/feat/read-entities-from-json-file](https://github.com/NationalLibraryOfNorway/epadd-nb/tree/feat/read-entities-from-json-file)