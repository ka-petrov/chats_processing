import settings
import os
import pandas as pd
import glob

sources = ['wa', 'vk']
columns = ['date', 'body', 'peer', 'source']


def get_data():
    data = pd.DataFrame()
    for s in sources:
        file_mask = os.path.join(settings.data_dir, s, '*.h5')
        files = glob.glob(file_mask)
        for f in files:
            df = pd.read_hdf(f, key='messages')
            data = data.append(df[columns])
    return data

# if __name__ == '__main__':
#     get_data()
