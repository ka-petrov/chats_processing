"""
WhatsApp doesn't seem to have a public API or any other "legal" means to pull the messages
history. Some online guides suggest to retrieve the msgstore.db.crypt12 file and
the key file from the user's phone and decrypt it, but this approach is:
a) platform specific (I would need to write separate manuals/scripts for iOS, Android, etc.)
b) requires root access, which might not be suitable for everyone.

So here I decided to go another way that requires some hand work, but that everyone can replicate
for sure.

1) Open WhatsApp app on your phone, open a chat you want to download,
    tap 3 dots in the top-right corner of the screen to open the menu and select
    "More"->"Email chat".
2) The dialog will appear and suggest to send the chat with or without media; since we only need
    the text, choose the "no media" option.
3) The default Email app will open; type in your Email address and send the message
4) Repeat 1-3 for each chat you want to download

The following script will log-in to your mail account, download and parse chat history files, and
save them in HDF and/or CSV format.

Note that some mail providers may require to tweak the security settings for unknown apps.
For example, to enable insecure apps for Gmail, use this link: https://myaccount.google.com/lesssecureapps
"""
import settings
import os, glob, re
import pandas as pd
from datetime import datetime
import imaplib, email, email.header


user_name = settings.wa_username
# all chat history files will start with this default pattern
fname_pattern = 'WhatsApp Chat with '
# messages with photo / video / sound will be replaced by this text pattern
skip_msg = ['<Media omitted>']

data_path = os.path.join(settings.data_dir, 'wa')
if not os.path.exists(data_path):
    os.makedirs(data_path)


def messages_from_email():
    """
    Pull WhatsApp chats from the email and save them as plain text files
    """
    mail = imaplib.IMAP4_SSL(settings.imap_ssl)
    mail.login(settings.mail_login, settings.mail_pass)
    mail.select(settings.mail_dir)
    mail.literal = fname_pattern.encode('utf-8')
    res, data = mail.uid('SEARCH', 'CHARSET', 'UTF-8', 'SUBJECT')
    if res != 'OK' or len(data) == 0:
        print('No matching messages found in the mailbox')
    uids = data[0].split()
    print('Found %d emails' % len(uids))
    for uid in uids:
        res, data = mail.uid('FETCH', uid, '(RFC822)')
        if res != 'OK':
            print('Failed to fetch email, skipping..')
            continue
        msg = email.message_from_bytes(data[0][1])
        for part in msg.walk():
            fname = part.get_filename()
            if fname:
                text, enc = email.header.decode_header(fname)[0]
                text = text.decode(enc)
                print(text)
                with open(os.path.join(data_path, text), 'wb') as fh:
                    fh.write(part.get_payload(decode=True))


def get_peer_name(fname):
    s = fname.index(fname_pattern) + len(fname_pattern)
    return fname[s:-4]


def process_messages():
    """
    Process plain text WhatsApp chats and save them in a structured format to HDF/CSV
    """
    uname = user_name + ': '
    file_mask = os.path.join(settings.data_dir, 'wa', '*.txt')
    files = glob.glob(file_mask)
    # loop through all text files in the data directory
    df = pd.DataFrame()
    for f in files:
        # extract the name of the chat peer from the file name
        peer = get_peer_name(f)
        print('Processing peer: %s' % peer)
        with open(f, 'r') as fh:
            text = fh.read()

        # To extract individual messages I split the text file using the date-time pattern at the
        # beginning of each message. Splitting by line endings ('\n') may look easier, but in
        # practice it makes multi-line messages processing trickier than it should be. Also,
        # I thought it's extremely unlikely that someone would use this exact date-time pattern in
        # their messages anyway :)
        r_list = re.split(settings.wa_date_pattern, text)
        # filter out empty lines
        r_list = [x for x in r_list if len(x) > 0]
        # split dates and message bodies (initially, r_list has both dates (even rows)
        #   and message bodies (odd rows))
        dates = [r_list[i] for i in range(0, len(r_list), 2)]
        messages = [r_list[i] for i in range(1, len(r_list), 2)]
        print(len(messages), 'messages')
        # iterate over all items and add only user's messages
        for d, m in zip(dates, messages):
            if m.startswith(uname):
                # start after the username and remove last '\n'
                body = m[len(uname):-1]
                if body not in skip_msg:
                    # in the date string, remove the last characters ' - '
                    dt = datetime.strptime(d[:-3], settings.wa_date_format)
                    df = df.append([{'date': dt, 'source': 'wa', 'peer': peer, 'body': body}])

    df.to_hdf(os.path.join(data_path, 'data_wa.h5'), 'messages')
    # df.to_csv(os.path.join(data_path, 'data_wa.csv'))


if __name__ == '__main__':
    messages_from_email()
    process_messages()
