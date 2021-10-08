import requests
import re
try: 
	from BeautifulSoup import BeautifulSoup
except ImportError:
	try:
		from bs4 import BeautifulSoup
	except ImportError:
		print("please install BeautifulSoup with 'pip install beautifulsoup4'")
from TermManip import *

def tryImport(module,pipName,part=""):
	try:
		if part!="":
			exec("global {};from {} import {}".format(part,module,part))
		else:
			exec("global {};import {}".format(module,module))
	except ImportError as error:
		print("please install {} with 'pip install {}'".format(module,pipName))
		raise error

def removeWWW(link):
	return re.sub(
				r'ww?[\d]+\.|www\.',
				'',
				link
			)

def makeLinkFull(link,site):
	if link.startswith("//"):
		link=site.split("//")[0]+link
	elif link.startswith("/"):
		link=site+link.strip("/")
	return link

def perhapsInt(number):
	if int(number)-number==0:
		return int(number)
	else:
		return number

class Manga: #TODO: grab header image
	def __init__(self,link):
		self.link=removeWWW(link.strip("/")+"/")
		self.refresh()

	def refresh(self):
		self.page=removeWWW(requests.get(self.link).text) #lmao
		self.page=BeautifulSoup(self.page,features="lxml")

		if self.page.body.find('div', attrs={'id':'Chapters_List'})==None:
			raise ValueError(
				red+"\nSite {} is not a valid manga site or a manga site that this script is not meant for!"
				    "\nIt should look like https://toilet-bound-hanako-kun.com!".format(self.link)+
				    reset
			)

		chapterList=self.page.body.find('div', attrs={'id':'Chapters_List'}).ul.ul
		self.chapterLink=re.sub(
			r"\d[\d-]+",
			"",
			chapterList.li.a['href'].replace(self.link+"manga/","")
				[:-1]
		)

		self.manga=self.page.title.contents[0].replace(" Manga Online","")

		self.chapters=[]
		for chapter in chapterList.find_all("li" , recursive=False):
			self.chapters+=[
				[
					float(chapter.a.contents[0].replace(self.manga+", Chapter ","")),
					self.extractChapter(chapter.a['href'])
				]
			]
		self.chapters.sort()

		self.chapterCount=0
		countedChapters=[]
		for chapter in self.chapters:
			if not int(chapter[0]) in countedChapters:
				self.chapterCount+=1
				countedChapters+=[int(chapter[0])]

		self.info=self.page.find('section',attrs={'id':'text-2'}).div.p.contents[0].strip("\n")

		self.summary=self.page.find('div',attrs={'class':'entry-content'}).find('p').next_sibling.text.strip("\n")

		self.thumbnails=[]
		for thumbnail in self.page.find('div',attrs={'class':'entry-content'}).ul.find_all('img'):
			try:
				self.thumbnails+=[makeLinkFull(thumbnail['data-src'],self.link)]
			except KeyError:
				self.thumbnails+=[makeLinkFull(thumbnail['src'],self.link)]

	def extractChapter(self,link):
		return float(link.replace(self.link+"manga/"+self.chapterLink,"").replace("-",".")[:-1])

	def __len__(self):
		return self.chapterCount

	class Chapter:
		def __init__(self,parentObj,chapterNumber):
			self.chapter=chapterNumber
			self.manga=parentObj
			self.refresh()

		class Part:
			def __init__(self,chapter,part,link):
				self.link=link
				self.chapter=chapter
				self.manga=self.chapter.manga
				self.part=part
				self.refresh()

			def refresh(self):
				self.page=removeWWW(requests.get(self.link).text) #lmao
				if self.page.find("This Chapter is not available Yet")!=-1:
					self.available=False
					return
				self.available=True
				self.page=BeautifulSoup(self.page,features="lxml")

				try:
					self.title=self.page.find_all('meta',attrs={'property':'og:description'})[1]['content'].strip("   ")
				except IndexError:
					self.title=self.page.title.contents[0].replace(" - "+self.manga.manga+" Manga Online","").strip("   ")

				self.pages=[]
				for page in self.page.find('div',attrs={"class":'entry-content'}).find_all('img'):
					try:
						self.pages+=[page['data-src']]
					except KeyError:
						self.pages+=[page['src']]

			def __len__(self):
				return len(self.pages)

		def refresh(self):
			self.parts=[]
			for part in self.manga.chapters:
				if int(part[0])==self.chapter:
					self.parts+=[
						self.Part(
							self,
							part[0],
							self.manga.link+"manga/"+self.manga.chapterLink+str(perhapsInt(part[1])).replace(".","-")
						)
					]

	def chapter(self,chapter):
		return self.Chapter(self,chapter)