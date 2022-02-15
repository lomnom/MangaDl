from sys import argv
from os.path import exists
from TermManip import *

################### (confusing) help screen
if len(argv)==1 or argv[1]=="-h": 
	print(green+"MangaDl, a tool to download mangas from manga sites!")
	print(
		"Syntax: "+blue+
		"python3 Download.py ((<link to website> <range of chapters>|<link to website at manga chapter>) [to <folder>])..."
	)
	print(" "*30+"^https?://.../    ^refer to {ranges}  ^https?://.../manga/...                 ^folder syntax"+green)
	print("Ranges are [number-number] or [number], seperated by commas ("
		  "69-12,109,21-22 and 129) or "+blue+"-"+green+" for none and "+blue+"+"+green+" for all"
		 )
	print("Some valid websites are: "+blue+(green+", "+blue).join(
			[
				"https://toilet-bound-hanako-kun.com",
				"https://neverland-manga.com/",
				"https://w17.read-beastarsmanga.com/"
			]
		 )+green
	)
	print(
		"For example,"+blue+" python3 Download.py toilet-bound-hanako-kun.com 1,36-82 to ../Mangas"
		+green+" to download chapters 1 and 36-82 of 'toilet-bound hanako-kun' to a folder named 'Mangas' in the parent directory,"+
		" and "+blue+"python3 Download.py toilet-bound-hanako-kun.com/manga/toilet-bound-hanako-kun-chapter-71/ to ../Mangas"+green+
		" to just download chapter 71"
	+green)
	print("Find less confusing documentation at https://github.com/lomnom/MangaDl"+reset)
	exit(0)

################### needed libraries
from Mangas import *
from PIL import Image
import PIL
from PyPDF2 import PdfFileMerger
from os import remove,mkdir
import sys
import io

################### utility functions and objects
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

def showPart(part): #show chapter part
	if part.available:
		node("Name",data=part.title)
		if part.created:
			node("Creation date",data=part.created)
		if part.edited:
			node("Edited at",data=part.edited)
		node("Pages",bracketed=str(len(part)),data="\n",last=True)
		for page in range(len(part)): #show all page links
			node(str(page+1),data=part.pages[page],last=page==len(part)-1)
	else:
		node("Available",data=str(False),last=True)

def addImgToMerger(page,merger,attempt=0): #add a image referenced by a link to a PDFFileMerger
	assert(attempt<5)
	pagePage=requests.get(
		page,
		headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0'}
	).content #download while pretending to be a browser

	#convert page to pdf in file on ram
	image=Image.open(io.BytesIO(pagePage),formats=["JPEG","PNG","WEBP","TIFF"]).convert('RGB') 
	pagePage=io.BytesIO()

	image.save(pagePage,"pdf")

	merger.append(pagePage) #add pdf to merger

class Target: #represents a manga to download
	def __init__(self,link,chapters,file):
		self.link=link
		self.chapters=chapters
		self.file=file

################### argument proccesing
args=list(argv)[1:]
targets=[]
while args!=[]:
	try:
		link=args.pop(0)
		if len(args)>0 and (args[0][0].isnumeric() or args[0][0]=="-" or args[0][0]=="+"):
			chapters=args.pop(0)
		else:
			linkParts=link.split("/manga/")
			if len(linkParts)==1:
				raise ValueError
			link=linkParts[0]
			chapters=str(int(re.findall(
				r"\d+",
				linkParts[1]
			)[0].replace("-",".")))
		if len(args)>0 and args[0]=="to":
			args.pop(0)
			file=args.pop(0)
			if not file.endswith(".pdf"):
				file=file.rstrip("/")+"/{}.pdf"
		else:
			file="{}.pdf"
		targets+=[Target(link,chapters,file)]
	except ValueError:
		node("error",data=red+"Invalid arguments!"+reset)
		exit(1)

################### main loop
for target in targets: 
	################### validate link and file
	try:
		if not target.link.startswith("http"):
			target.link="https://"+target.link
		manga=Manga(target.link)
	except InvalidSite: #handle sites that arent the correct format (see https://github.com/lomnom/MangaDl)
		node("error",data=red+"Site {} is not a valid manga site or a manga site that this script is not meant for! "
			  "See https://github.com/lomnom/MangaDl for site requirements!".format(target.link)+
			  reset)
		continue

	if not target.file=="{}.pdf":
		folder="/".join(target.file.split("/")[:-1])
		if not exists(folder):
			node("error",data=red+"Folder {} does not exist!".format(folder)+
				  reset)
			continue

	################### print manga info
	node(manga.manga,bracketed=manga.link,data="\n")

	node("Chapters",data=str(len(manga))) #show manga info
	if manga.info!="":
		node("Info",data=manga.info)
	if manga.summary!="":
		node("Summary",data=manga.summary)
	node("Header Image",data=manga.header)

	node("Thumbnails",data="\n",last=target.chapters=='' or target.chapters=='-')
	for thumbnail in range(len(manga.thumbnails)):
		node(manga.thumbnails[thumbnail],last=thumbnail==(len(manga.thumbnails)-1))

	######### validate range to download
	try:
		if target.chapters!="+":
			toDownload=list(dict.fromkeys(textRange(target.chapters)))
			if toDownload==[]:
				continue
		else:
			toDownload=list(range(1,manga.chapters+1))
	except ValueError:
		node(
			"error",
			data=yellow+"'"+target.chapters+"'"+red+" doesnt seem like a valid range! "+
			"Valid ranges are [number-number] or [number], seperated by commas ("
			"69-12,109,21-22 and 129) or "+yellow+"-"+red+" for none and "+yellow+"+"+red+" for all"+reset,
			last=True
		)
		continue

	node(
		"ToDownload",data="\n",
		bracketed=target.chapters+": "+str(len(toDownload))+(" to "+target.file if target.file!="{}.pdf" else "")
	,last=True)

	################### download chapter by chapter
	for chapterN in range(len(toDownload)):
		chapter=toDownload[chapterN]
		chapter=manga.chapter(chapter)

		######### download single-part chapter
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
						node(
							"error",data=red+"Page {}'s data was invalid!".format(pageN+1)+reset,
						)
				merger.write(target.file.format(chapter.title.replace("/","\\/"))) #write chapter to [chapter title].pdf
				merger.close()
				print(colcurs.format(1)+clrtoeol,end="")

		elif len(chapter)==0:
			node(
				"Chapter {}".format(chapter.chapter),
				data=red+"Nonexistent"+reset,
				last=chapter.chapter==toDownload[-1]
			)

		################### download multi-part chapters
		else: 
			node(
				"Chapter {}".format(chapter.chapter),
				data="\n",
				last=chapter.chapter==toDownload[-1]
			)
			for partN in range(len(chapter)): #show data on all parts
				part=chapter.parts[partN]
				node(
					"Part {}".format(partN+1),data="\n",
					last=partN==(len(chapter)-1),
					bracketed=part.link
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
								data=red+"Part {}'s page {}'s data was invalid!".format(partN+1,pageN+1)+reset,
							)
					merger.write(target.file.format(part.title.replace("/","\\/")))
					merger.close()

			print(colcurs.format(1)+clrtoeol,end="")

print(reset,end="")