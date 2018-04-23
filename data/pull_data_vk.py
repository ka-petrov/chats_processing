"""
To use VK API you'll need a VK account and an access_token.
Go to this docs page https://vk.com/dev/implicit_flow_user for the full list of instructions.

My simplified instructions is as follows:
1) create a VK application: https://vk.com/editapp?act=create
2) find it here: https://vk.com/apps?act=manage, go to the app settings and copy the app ID
3) paste this link into your browser and replace 'YOUR_APP_ID' with the ID from the previous step:
https://oauth.vk.com/authorize?client_id=YOUR_APP_ID&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=friends,wall,messages&response_type=token&v=5.73&state=123456
4) you'll be redirected and your new URL will contain the 'access_token' field; copy it, paste
    to settings.vk_token and you're ready to go!
5) note that access_token has an expiry, so after it expires you'll have to repeat steps 3-4

"""

import vk
import time
import pandas as pd
import settings
import os
from datetime import datetime

# token used for authentication
access_token = settings.vk_token
# slow down API requests to avoid errors
api_delay = 0.3
# VK API limits the maximum number of items per request
max_items = 200
# to get messages from chat use: chat_id_offset + chat_id
chat_id_offset = 2000000000
# list of column names to fetch
columns_list = ['date', 'body', 'out']
# data directory
data_path = os.path.join(settings.data_dir, 'vk')
if not os.path.exists(data_path):
    os.makedirs(data_path)


def api_call(request, **kwargs):
    retry_delay = 5
    ok = False
    while not ok:
        try:
            ans = request(**kwargs)
            ok = True
        except Exception as e:
            # if we hit the API requests limit (error code = 6), wait for some time and retry
            if (isinstance(e, vk.api.VkAPIError) and e.code in [6])\
                    or isinstance(e, ConnectionError):
                print(e)
                print('Retrying in %d seconds' % retry_delay)
                time.sleep(retry_delay)
                retry_delay *= 2  # double the delay for each attempt
            else:
                raise e
    return ans


if __name__ == '__main__':
    # create VK API session
    session = vk.Session(access_token=access_token)
    vk_api = vk.API(session, v='5.71')

    # get dialogs count
    dialogs = vk_api.messages.getDialogs(count=0)
    n = dialogs['count']
    users = []
    chats = []
    # the outer loop iterates over the items chunks of the size limited by API
    print('Getting dialogs list...')
    for i in range(0, n, max_items):
        time.sleep(api_delay)
        print('%d / %d' % (i, n))
        dialogs = vk_api.messages.getDialogs(offset=i, count=max_items)
        # the inner loop iterates through all dialogs and saves user and chat ids for further processing
        for d in dialogs['items']:
            chat = d['message'].get('chat_id')
            user = d['message'].get('user_id')
            if chat is not None:
                chats.append((chat, d['message']['title']))
            # sometimes user is < 0, probably when account is deleted/banned
            elif user is not None and user > 0:
                users.append(user)

    # get messages for users
    print('Processing users...')
    for i, u in enumerate(users):
        df = pd.DataFrame()
        user = api_call(vk_api.users.get, user_ids=u)
        if len(user) == 0:
            continue
        username = '{0} {1}'.format(user[0]['first_name'], user[0]['last_name'])
        print('user = %s; %d / %d' % (username, i, len(users)))
        hist = api_call(vk_api.messages.getHistory, peer_id=u, count=0)
        n = hist['count']
        for i in range(0, n, max_items):
            time.sleep(api_delay)
            print('%d / %d' % (i, n))
            messages = api_call(vk_api.messages.getHistory, peer_id=u, offset=i, count=max_items)
            # select only outgoing messages and filter columns
            messages = [{c: x.get(c) for c in columns_list} for x in messages['items'] if x['out'] == 1]
            if len(messages) > 0:
                df = df.append(messages)
        if not df.empty:
            df['date'] = df['date'].apply(lambda x: datetime.fromtimestamp(x))
            df['source'] = 'vk'
            df['peer'] = username
            # save the results
            df.to_hdf(os.path.join(data_path, 'user_%d.h5' % u), key='messages')
            # df.to_csv(os.path.join(data_path, 'user_%d.csv' % u))

    # get messages for chats
    print('Processing chats...')
    for i, ch in enumerate(chats):
        df = pd.DataFrame()
        print('chat = %s; %d / %d' % (ch[1], i, len(chats)))
        hist = api_call(vk_api.messages.getHistory, peer_id=chat_id_offset+ch[0], count=0)
        n = hist['count']
        for i in range(0, n, max_items):
            time.sleep(api_delay)
            print('%d / %d' % (i, n))
            messages = api_call(vk_api.messages.getHistory, peer_id=chat_id_offset+ch[0], offset=i, count=max_items)
            # select only outgoing messages and filter columns
            messages = [{c: x.get(c) for c in columns_list} for x in messages['items'] if x['out'] == 1]
            if len(messages) > 0:
                df = df.append(messages)
        if not df.empty:
            df['date'] = df['date'].apply(lambda x: datetime.fromtimestamp(x))
            df['source'] = 'vk'
            df['peer'] = ch[1]
            # save the results
            df.to_hdf(os.path.join(data_path, 'chat_%d.h5' % ch[0]), key='messages')
            # df.to_csv(os.path.join(data_path, 'chat_%d.csv' % ch[0]))
