# Chat messages analysis + NLP basics

This repository provides Python scripts to download chat history for WhatsApp messenger 
(`data/pull_data_wa.py`) and for VK.com (`data/pull_data_vk.py`) - the most popular Russian social
network. Data is stored in unified format as HDF files and can be merged into a single 
messages dataset with `data/merge_data.py` script. By default only outgoing messages are downloaded.

Check out sample Jupyter notebooks in the root directory for some examples on what kind of analysis 
you can do with this data. The preferred order of reading is: words_distribution -> message_length_count -> spelling.

**Note:** I've used my own message history in Russian language to develop this, so some of the
content may be specific to this language. But most of it should be applicable to English and many 
other languages as well.

 ### Installation:
 
 - Python 3.* is required
 - `git clone https://github.com/imaginary-unit/chats_processing.git`
 - `cd chats_processing`
 - `pip3 install -r requirements.txt`
 - `cp settings.py.template settings.py`, update the settings file with your data path, accounts
 details, etc.
 
 ### Usage:
 
 - `data/pull_data_...` scripts contain instructions at the top of the files, please read and follow
   them before running the script. For WhatsApp the data acquisition process is not 100% automatic,
   but it looks like a best option out there.
 - run `python3 data/pull_data_vk.py` and `python3 data/pull_data_wa.py`; data downloading may take
    a while, depending on your history size.
 - to read your dataset as a single `pd.DataFrame` use `data.merge_data.get_data()` function.
 - check out the Jupyter notebooks for insights on data analysis
