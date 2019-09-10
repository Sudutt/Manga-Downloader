import os
import sys
import requests
import threading
from bs4 import BeautifulSoup
from datetime import datetime

def search(query):
    query_ = query.lower().split(' ')
    query_ = ' '.join(query_).split(' ')
    query_ = '+'.join(query_)
    search = "https://isekaiscan.com/?s="+query+"&post_type=wp-manga&author=&artist=&release="
    cont = requests.get(search, allow_redirects=True).content
    soup = BeautifulSoup(cont, "lxml")
    samples = soup.find_all("div","post-title")
    return [ a.find('a') for a in samples ]

def check_page(url):
    r = requests.get(url, allow_redirects=True, stream=True, timeout=600)
    fname = r.url[r.url.rfind('/')+1:]
    cname = r.url[r.url.rfind('-')+1:r.url.rfind('/')]
    if r.status_code==200:
        with open(fname, 'wb') as f:
            for chunk in r:
                f.write(chunk)
        with open(fname) as f:
            pass
    else:
        print(fname+"failed at chapter-"+cname)

def download_chap(base_url, ch_no):
#make chapter
    print("Creating chapter "+str(ch_no)+"...")
    os.mkdir("Chapter "+str(ch_no))
    os.chdir("Chapter "+str(ch_no))
#get list of pages
    chap_url = base_url+str(ch_no)
    cont = requests.get(chap_url, allow_redirects=True).content
    soup = BeautifulSoup(cont, "lxml")
    samples = soup.find_all("div", "page-break no-gaps")
    pages = [ t.find("img").attrs["data-src"].strip() for t in samples ]
#download with async
    threads=[]
    for page in pages:
        t = threading.Thread(target=check_page, args = (page, ))
        t.start()
        threads.append(t)
    for thread in threads:
        thread.join()
#log as chapter done
    os.chdir('..')
    with open("index.txt",'a') as f:
        f.write("Chapter "+str(ch_no)+" done at "+datetime.now().strftime("%m/%d/%Y, %H:%M:%S")+"\n")

def get_last_chap(manga):
    home_url = manga.attrs["href"]
    cont = requests.get(home_url, allow_redirects=True).content
    soup = BeautifulSoup(cont, "lxml")
    last_chap = soup.find("li", "wp-manga-chapter").find("a")
    MAX_CHAP = last_chap.get_text().strip().split(' ')[1]
    return int(MAX_CHAP)

def update(manga):
#go to directory
    name = manga.get_text().strip()
    os.chdir(name)
#get last offline chap
    chaps = [ name for name in filter(os.path.isdir, os.listdir(os.getcwd())) ]
    if len(chaps)==0:
        last_offline=0
    else:
        chaps = [ int(n.split(' ')[1]) for n in chaps ]
        last_offline = max(chaps)
    MAX_CHAP = get_last_chap(manga)
#if not up-to-date
    if last_offline<MAX_CHAP:
        print(f"{MAX_CHAP-last_offline} chapters to be downloaded...")
        base = manga.attrs['href']+"chapter-"
        for i in range(last_offline+1, MAX_CHAP+1):
            download_chap(base, i)
#finish
    os.chdir('..')
    print("Manga is up-to-date!")

def create(manga):
#create directory
    name = manga.get_text().strip()
    print("Creating '"+name+"'...")
    os.mkdir("[MANGA] "+name)
    os.chdir("[MANGA] "+name)
#get all chapters
    MAX_CHAP = get_last_chap(manga)
    print(f"{MAX_CHAP} chapters to be downloaded...")
    base = manga.attrs['href']+"chapter-"
    for i in range(1,MAX_CHAP+1):
        download_chap(base, i)
#finish
    os.chdir('..')
    print("Manga is up-to-date!")

def main():
#get a valid query
    while True:
        q = input("Enter manga name: ")
        sample_set = search(q)
        if sample_set!=[]:
            break
        print("Error! No relevant manga found!")
#get a valid manga
    req_manga = None
    for sample in sample_set:
        ch = input("Did you mean: "+sample.get_text().strip()+" [Y/N]: ")
        if ch=='y' or ch=='Y':
            req_manga = sample
            break
    if req_manga==None:
        print("\nSorry! Not available on isekaiscans.com")
        return
#get status (existing/new)
    mangas = [ name for name in filter(os.path.isdir, os.listdir(os.getcwd())) ]
    req_name = req_manga.get_text().strip()
    if req_name in mangas:
        ch = input("Manga exists! Do you want to update? [Y/N]")
        if ch=='y' or ch=='Y':
            update(req_manga)
    else:
        create(req_manga)
    print("Thank you! Please feel free to contribute to the author & isekaiscans.com")

def full_update():
#get all names
    manga_names = [ name[8:0] for name in filter(os.path.isdir, os.listdir(os.getcwd())) if name[0] != '.']
    manga_pages = [ search(name) for name in manga_names]
#check if still online
    for page,name in zip(manga_pages, manga_names):
        if len(page)==0:
            print(f"\nSorry! '{name}' is not available on isekaiscans.com anymore")
        else:
            print(f"\nUpdating '{name}'...")
            update(page[0])
    print("\nThank you! Please feel free to contribute to the author & isekaiscans.com")


if __name__=="__main__":
    if len(sys.argv)==2 and sys.argv[1]=='-u':
        full_update()
    elif len(sys.argv)==2 and sys.argv[1]=='-s':
        main()
    else:
        print("Usage: python manga-downloader-v1.py -u|-s|-h")
        print()
        print("-u\t\tUpdate all existing manga in folder")
        print("-s\t\tSearch and/or update given manga")
        print("-h\t\tPrint this help")
#end of code
