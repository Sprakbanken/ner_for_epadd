# NER for ePADD
This repo contains a script the extracts named entities from the text of an .mbox file.  
The text extaction part is not very robust, and might not work on your .mbox files.

## Installation
You need python >=3.10, pip, and venv   
Create a virtual environment and install dependencies like this:  
```
python3 -m venv .venv
. .venv/bin/activate
pip install .
```

## Running the script
Run `python3 -m ner_for_epadd --help` for argument explanation.

If the default argumentents fit, you can run the script like this: 
```
python3 -m ner_for_epadd --mbox [path_to_mbox_file.mbox] --output [path_to_ouput.json]
```

You can use the output file as input to [https://github.com/NationalLibraryOfNorway/epadd-nb](https://github.com/NationalLibraryOfNorway/epadd-nb/)