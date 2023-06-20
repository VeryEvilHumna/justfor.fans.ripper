print("Loading libraries")

import os
import shutil
import sys
import json
import requests

from tqdm import tqdm
from bs4 import BeautifulSoup

import config
from Class.JJFPost import JJFPost

print("Libraries loaded")

VERBOSE = config.VERBOSE

loopct = 0



def create_folder(tpost):
    fpath = os.path.join(config.save_path, tpost.name, tpost.type)

    if not os.path.exists(fpath):
        os.makedirs(fpath)
    
    return fpath



def photo_save(ppost):
    ii = 1
    photos_url = []

    photos_img = ppost.post_soup.select('div.imageGallery.galleryLarge img.expandable')

    if len(photos_img) == 0:
        ii = -1
        photos_img.append(ppost.post_soup.select('img.expandable')[0])

    for img in photos_img:

        if 'src' in img.attrs:
            imgsrc = img.attrs['src']
        elif 'data-lazy' in img.attrs:
            imgsrc = img.attrs['data-lazy']
        else:
            print("no image source, skipping")
            continue
        ext = imgsrc.split('.')[-1]
        
        ppost.photo_seq = ii
        ppost.ext = ext
        ppost.prepdata()

        folder = create_folder(ppost)
        ppath = os.path.join(folder, ppost.title)

        if not config.overwrite_existing and os.path.exists(ppath):
            print(f'p: <<exists skip>>: {ppath}')
            ii += 1
            continue

        photos_url.append([
            ppath, imgsrc
        ])

        ii += 1


    for img in photos_url:
        
        if VERBOSE:    
            print(f'p: {img[0]}')
            print(img[1])

        try:
            response = requests.get(img[1], stream=True)
            print("Downloading " + str(round(int(response.headers.get('content-length'))/1024/1024, 2)) + " MB")
            with open(img[0], 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response
        except Exception as e:
            print(e)


"""

VIDEO SAVING IS BROKEN FOR NOW, JFF STORE MOST NEW VIDEOS IN HLS FORMAT, WHICH IS NOT SUPPORTED BY THIS SCRIPT.

TODO:
    add support for segmented video delivery format (hls)
    fix broken tqdm progressbar

"""


def video_save(vpost):
    vpost.ext = 'mp4'
    vpost.prepdata()

    folder = create_folder(vpost)
    vpath = os.path.join(folder, vpost.title)

    if not config.overwrite_existing and os.path.exists(vpath):
        print(f'v: <<exists skip>>: {vpath}')
        return

    # print(vpost.post_soup)
    try:
        vidurljumble = vpost.post_soup.select('div.videoBlock a')[0].attrs['onclick']
        vidurl = json.loads(vidurljumble.split(', ')[1])

        vpost.url_vid = vidurl.get('1080p', '')
        vpost.url_vid = vidurl.get('540p', '') if vpost.url_vid == '' else vpost.url_vid

        if VERBOSE:
            print(f'v: {vpath}')
            print(vpost.url_vid)
            
        print("")
        
        response = requests.get(vpost.url_vid, stream=True)

        total_size = int(response.headers.get('content-length', 0))

        progress_bar = tqdm(response.iter_content(chunk_size=1024), total=total_size, unit='B', unit_scale=True, desc=vpost.title) # 20 June 2023: broken progressbar, TODO: fix. k is actually MB
                                                                                                                                   # 44.9k/47.1MB [00:04<1:24:24, 10.9kB/s]

        with open(vpath, 'wb') as out_file:
            for chunk in progress_bar:
                out_file.write(chunk)

    except Exception as e:
        print(e)



def text_save(tpost):
    tpost.ext = 'txt'
    tpost.prepdata()

    folder = create_folder(tpost)
    tpath = os.path.join(folder, tpost.title)

    if VERBOSE:
        print(f't: {tpath}') 

    with open(tpath, "w", encoding='utf-8') as file:
        file.write(tpost.full_text)
        file.close()



def parse_and_get(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')

    for pp in soup.select('div.mbsc-card.jffPostClass'):

        # time.sleep(random.randint(1, 2)) # @VeryEvilHumna: I tested for about 5 hours (left the computer overnight) and I did not get any "too frequent requests" errors 

        ptext = pp.select('div.fr-view')

        thispost = JJFPost()
        thispost.post_soup = pp
        thispost.name = pp.select('h5.mbsc-card-title.mbsc-bold span')[0].get("onclick").lstrip("location.href='/").rstrip("'")
        thispost.post_date_str = pp.select('div.mbsc-card-subtitle')[0].text.strip().strip()
        thispost.post_id = pp.attrs['id']
        thispost.full_text = ptext[0].text.strip() if ptext else ''
        thispost.prepdata()

        print(thispost.name)
        print(thispost.post_date_str)

        classvals = pp.attrs['class']
        
        if 'video' in classvals:
            thispost.type = 'video'
            video_save(thispost)

            if config.save_full_text:
                text_save(thispost)

        elif 'photo' in classvals:
            thispost.type = 'photo'
            photo_save(thispost)

            if config.save_full_text:
                text_save(thispost)
                
        elif 'text' in classvals:
            if config.save_full_text:
                thispost.type = 'text'
                text_save(thispost)



def get_html(loopct):
    geturl = config.api_url.format(userid=uid, seq=loopct, hash=hsh)
    # print(geturl)
    html_text = requests.get(geturl).text

    return html_text
        

if __name__ == "__main__":

    if VERBOSE:
        print("DEBUG MODE, VERBOSE OUTPUT.")

    if len(sys.argv) == 3:
        uid = sys.argv[1]
        hsh = sys.argv[2]
        print("Using uid and hash from command line parameters")
       
    else:
        uid = config.uid
        hsh = config.hsh
        if uid == "" or hsh == "":
            print("Specify UserID and UserHash4 in the config file or in the command line parameters and restart program. Aborted.")
            sys.exit(0)
        else:
            print("Using uid and hash from config file...")


    loopit = True


    while loopit:

        html_text = get_html(loopct)

        if 'as sad as you are' in html_text:
                print("No more posts to parse. Exiting.")
                print("If program is not downloaded any files, your token is expired or invalid. Get a new one.")
                loopit = False
            
        else:
            parse_and_get(html_text)
            loopct += 10


