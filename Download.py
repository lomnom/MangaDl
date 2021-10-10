from Mangas import *
from sys import argv
from PIL import Image
import PIL
from PyPDF2 import PdfFileMerger
from os import remove,mkdir
import sys
import io

from TermManip import *

def textRange(textRange): #converts stuff like 12-13 to [12,13]
	if textRange=='' or textRange=='-': return []
	ranges=textRange.split(",")
	values=[]
	for n in range(len(ranges)):
		ranges[n]=ranges[n].split("-")
		if len(ranges[n])==1:
			values+=[int(ranges[n][0])]
		elif len(ranges[n])==2:
			for n in range(int(ranges[n][0]),int(ranges[n][1])+1):
				values+=[n]
	return values

if len(argv)==1 or argv[1]=="-h": #handle help screen
	print(green+"MangaDl, a tool to download mangas from manga sites!")
	print("Run as "+blue+"python Download.py [[site][range]]+ "+green)
	print(
		"For example,"+blue+" python Download.py https://toilet-bound-hanako-kun.com 1,36-82"+
		green+" to download chapters 1 and 36-82 of 'toilet-bound hanako-kun'"
	)
	print(green+"Some valid sites are "+blue+(green+", "+blue).join(
		["https://toilet-bound-hanako-kun.com","https://neverland-manga.com/","https://w17.read-beastarsmanga.com/"]
	)+reset)
	print(green+"(Ranges can also be replaced with"+blue+" - "+green+"to just extract data)"+reset)
	exit(0)

if (len(argv)-1)%2!=0: #detect trash arguments
	print(red+"The number of arguments should be a multiple of 2! Run with -h to see argument format."+reset)
	exit(1)

def showPart(part): #show chapter part
	if part.available:
		node("Name",data=part.title)
		node("Pages",bracketed=str(len(part)),data="\n",last=True)
		for page in range(len(part)): #show all page links
			node(str(page+1),data=part.pages[page],last=page==len(part)-1)
	else:
		node("Available",data=str(False),last=True)

def addImgToMerger(page,merger): #add a image referenced by a link to a PDFFileMerger
	pagePage=requests.get(page).content #download

	#convert page to pdf in file on ram
	image=Image.open(io.BytesIO(pagePage),formats=["jpeg","png","webp","tiff"]).convert('RGB') 
	pagePage=io.BytesIO()
	image.save(pagePage,"pdf")

	merger.append(pagePage) #add pdf to merger

args=[]
for arg in range((len(argv)-1)//2): #split args into chunks of 2 ([1,2,3,4] -> [[1,2],[3,4]])
	args+=[[argv[arg*2+1],argv[arg*2+2]]]

for target in args: #site,range
	try:
		if not target[0].startswith("http"):
			target[0]="https://"+target[0]
		manga=Manga(target[0])
	except InvalidSite: #handle sites that arent the correct format (see https://github.com/lomnom/MangaDl)
		node("error",data=red+"Site {} is not a valid manga site or a manga site that this script is not meant for! "
			  "See https://github.com/lomnom/MangaDl for site requirements!".format(target[0])+
			  reset)
		continue
	node(manga.manga,bracketed=manga.link,data="\n")

	node("Chapters",data=str(len(manga))) #show manga info
	node("Info",data=manga.info)
	if manga.summary!="":
		node("Summary",data=manga.summary)
	node("Header Image",data=manga.header)

	node("Thumbnails",data="\n",last=target[1]=='' or target[1]=='-')
	for thumbnail in range(len(manga.thumbnails)):
		node(manga.thumbnails[thumbnail],last=thumbnail==(len(manga.thumbnails)-1))

	try: #get chapters to download and make sure valid
		toDownload=list(dict.fromkeys(textRange(target[1])))
		if toDownload==[]:
			continue
	except ValueError:
		node("error",data=red+"'{}' doesnt seem like a valid range! "
			  "Valid ranges are [number-number] or [number], seperated my commas: "
			  "69-12,109,21-22 and 129".format(target[1])+reset,last=True)
		continue

	node("ToDownload",data="\n",bracketed=target[1]+": "+str(len(toDownload)),last=True)

	for chapterN in range(len(toDownload)): #single-part chapters
		chapter=toDownload[chapterN]
		chapter=manga.chapter(chapter)
		if len(chapter)==1:
			chapter=chapter.parts[0]
			node(
				"Chapter {}".format(chapter.chapter.chapter),
				bracketed=chapter.link,data="\n",
				last=chapter.chapter.chapter==toDownload[-1]
			)
			showPart(chapter)
			merger = PdfFileMerger() #make pdf merger
			if chapter.available: #make sure chapter is translated
				for pageN in range(len(chapter.pages)): #iterate through all pages
					print( #draw loading bar
						colcurs.format(1)+
						blue+"["+loadingBar(10,((pageN+1)/len(chapter.pages))*100)+"] "+
						cyan+"Currently downloading page {}/{} of chapter {} ({}/{})"
							.format(pageN+1,len(chapter),chapter.chapter.chapter,chapterN+1,len(toDownload))+
						clrtoeol+reset,
						end=""
					)
					sys.stdout.flush()
					page=chapter.pages[pageN]
					try: #handle invalid pages
						addImgToMerger(page,merger)
					except PIL.UnidentifiedImageError:
						print(colcurs.format(1)+clrtoeol,end="")
						node("error",data=red+"Page {}'s data was invalid!".format(pageN+1)+reset)
				merger.write("{}.pdf".format(chapter.title)) #write chapter to [chapter title].pdf
				merger.close()
				print(colcurs.format(1)+clrtoeol,end="")
		elif len(chapter)==0:
			node(
				"Chapter {}".format(chapter.chapter),
				data=red+"Nonexistent"+reset,
				last=chapter.chapter==toDownload[-1]
			)
		else: #multi-part chapters
			node(
				"Chapter {}".format(chapter.chapter),
				data="\n",
				last=chapter.chapter==toDownload[-1]
			)
			for partN in range(len(chapter)): #show data on all parts
				part=chapter.parts[partN]
				node(
					"Part {}".format(partN+1),data="\n",
					last=partN==(len(chapter)-1)
				)
				showPart(part)

			for partN in range(len(chapter)): #iterate through all parts and download if translated
				part=chapter.parts[partN]
				if part.available:
					merger = PdfFileMerger()
					for pageN in range(len(part.pages)):
						print(
							colcurs.format(1)+
							blue+"["+loadingBar(10,((pageN+1)/len(part.pages))*100)+"] "+
							cyan+"Currently downloading page {}/{} in part {}/{} of chapter {} ({}/{})"
								.format(
									pageN+1,len(part),
									partN+1,len(chapter),
									chapter.chapter,
									chapterN+1,len(toDownload)
							)+
							clrtoeol+reset,
							end=""
						)
						sys.stdout.flush()
						page=part.pages[pageN]
						try: #handle invalid pages
							addImgToMerger(page,merger)
						except PIL.UnidentifiedImageError:
							print(colcurs.format(1)+clrtoeol,end="")
							node(
								"error",
								data=red+"Part {}'s page {}'s data was invalid!".format(partN+1,pageN+1)+reset
							)
					merger.write("{}.pdf".format(part.title))
					merger.close()
			print(colcurs.format(1)+clrtoeol,end="")

print(reset,end="")