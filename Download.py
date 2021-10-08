from Mangas import *
from sys import argv
from PIL import Image
from PyPDF2 import PdfFileMerger
from os import remove,mkdir
import sys

mangas=[
	"https://w17.read-beastarsmanga.com/",
	"https://toilet-bound-hanako-kun.com/",
	"https://neverland-manga.com/"
]

from TermManip import *

def textRange(textRange):
	if textRange=='': return []
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

if argv[1]=="-h":
	print(green+"MangaDl, a tool to download mangas from manga sites!")
	print("Run as "+blue+"python Download.py [[site][range]]+ "+green)
	print(
		"For example,"+blue+" python Download.py https://toilet-bound-hanako-kun.com 1,36-82"+
		green+" to download chapters 1 and 36-82 of 'toilet-bound hanako-kun'"
	)
	print(green+"Some valid sites are "+blue+(green+", "+blue).join(
		["https://toilet-bound-hanako-kun.com","https://neverland-manga.com/","https://w17.read-beastarsmanga.com/"]
	)+reset)
	exit(0)

args=argv[1:]

def showPart(part):
	if part.available:
		node("Name",data=part.title)
		node("Pages",bracketed=str(len(part)),data="\n",last=True)
		for page in range(len(part)-1):
			node(str(page+1),data=part.pages[page])
		node(str(page+2),data=part.pages[page+1],last=True)
	else:
		node("Available",data=str(False),last=True)

def addImgToMerger(page,merger):
	pagePage=requests.get(page).content
	imgFile="page.{}".format(page.split(".")[-1].strip("/"))
	open(imgFile,'wb').write(pagePage)

	image=Image.open(imgFile).convert('RGB')
	image.save("page.pdf")
	remove(imgFile)

	merger.append("page.pdf")
	remove("page.pdf")

for site in range(len(args)//2): #site,range
	manga=Manga(args[site*2])
	node(manga.manga,bracketed=manga.link,data="\n")

	node("Chapters",data=str(len(manga)))
	node("Info",data=manga.info)
	node("Summary",data=manga.summary)
	node("Thumbnails",data="\n")
	for thumbnail in range(len(manga.thumbnails)):
		node(manga.thumbnails[thumbnail],last=thumbnail==(len(manga.thumbnails)-1))
	node("ToDownload",data=args[site*2+1])
	node("Chapters",data="\n",last=True)

	toDownload=textRange(args[site*2+1])
	for chapterN in range(len(toDownload)):
		chapter=toDownload[chapterN]
		chapter=manga.chapter(chapter)
		if len(chapter.parts)==1:
			chapter=chapter.parts[0]
			node(
				"Chapter {}".format(chapter.chapter.chapter),
				bracketed=chapter.link,data="\n",
				last=chapter.chapter.chapter==int(",".join(args[site*2+1].split("-")).split(",")[-1])
			)
			showPart(chapter)
			merger = PdfFileMerger()
			for pageN in range(len(chapter.pages)):
				print(
					colcurs.format(1)+
					blue+"["+loadingBar(10,((pageN+1)/len(chapter.pages))*100)+"] "+
					cyan+"Currently downloading page {} of chapter {} ({}/{})"
						.format(pageN,chapter.chapter.chapter,chapterN+1,len(toDownload))+
					clrtoeol,
					end=""
				)
				sys.stdout.flush()
				page=chapter.pages[pageN]
				addImgToMerger(page,merger)
			merger.write("{}.pdf".format(chapter.title))
			merger.close()
			print(colcurs.format(1)+clrtoeol,end="")
		else:
			node(
				"Chapter {}".format(chapter.chapter),
				data="\n",
				last=chapter.chapter==int(",".join(args[site*2+1].split("-")).split(",")[-1])
			)
			for partN in range(len(chapter.parts)):
				part=chapter.parts[partN]
				node(
					"Part {}".format(partN+1),data="\n",
					last=partN==(len(chapter.parts)-1)
				)
				showPart(part)

			for partN in range(len(chapter.parts)):
				merger = PdfFileMerger()
				part=chapter.parts[partN]
				for pageN in range(len(part.pages)):
					print(
						colcurs.format(1)+
						blue+"["+loadingBar(10,((pageN+1)/len(part.pages))*100)+"] "+
						cyan+"Currently downloading page {} in part {}/{} of chapter {} ({}/{})"
							.format(pageN,partN,len(chapter.parts),chapter.chapter,chapterN+1,len(toDownload))+
						clrtoeol,
						end=""
					)
					sys.stdout.flush()
					page=part.pages[pageN]
					addImgToMerger(page,merger)
				merger.write("{}.pdf".format(part.title))
				merger.close()
			print(colcurs.format(1)+clrtoeol,end="")

print(reset,end="")