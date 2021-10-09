import requests
import re
try: 
	from BeautifulSoup import BeautifulSoup
except ImportError:
	from bs4 import BeautifulSoup
from TermManip import *

def removeWWW(link): #www.google.com -> google.com
	return re.sub(
				r'ww?[\d]+\.|www\.',
				'',
				link
			)

def makeLinkFull(link,site): # //google.com/page -> https?://google.com/page
							 # /uploads/content -> https?://page.com/uploads/content
	if link.startswith("//"):
		link=site.split("//")[0]+link
	elif link.startswith("/"):
		link=site+link.strip("/")
	return link

def perhapsInt(number): # 1.0 -> 1, 1.1 -> 1.1
	if int(number)-number==0:
		return int(number)
	else:
		return number

class Manga: #TODO: grab header image (CSS?!??!?!)
	def __init__(self,link):
		self.link=removeWWW(link.strip("/")+"/")
		self.refresh()

	def refresh(self):
		self.page=removeWWW(requests.get(self.link).text) #remove all wwws, because they mess with the regex
		self.page=BeautifulSoup(self.page,features="lxml")

		if self.page.body.find('div', attrs={'id':'Chapters_List'})==None: #check if site is valid by looking for chapter list
			raise ValueError("Invalid site!")

		chapterList=self.page.body.find('div', attrs={'id':'Chapters_List'}).ul.ul #get ul of chapters
		self.chapterLink=re.sub(
			r"\d[\d-]+",
			"",
			chapterList.li.a['href'].replace(self.link+"manga/","")
				[:-1]
		)

		self.manga=self.page.title.contents[0].replace(" Manga Online","") #get manga name from page title

		self.chapters=[]
		for chapter in chapterList.find_all("li" , recursive=False): #get all chapters and store as [number,link]
			self.chapters+=[
				[
					float(chapter.a.contents[0].replace(self.manga+", Chapter ","")),
					chapter.a['href']
				]
			]

		self.chapterCount=0
		countedChapters=[]
		for chapter in self.chapters: #get number of chapters
			if not int(chapter[0]) in countedChapters:
				self.chapterCount+=1
				countedChapters+=[int(chapter[0])]

		self.info=self.page.find('section',attrs={'id':'text-2'}).div.p.contents[0].strip("\n") #get first paragraph of info

		self.summary=self.page.find('div',attrs={'class':'entry-content'}).find('p').next_sibling.text.strip("\n") #get second paragraph

		self.thumbnails=[]
		for thumbnail in self.page.find('div',attrs={'class':'entry-content'}).ul.find_all('img'): #get all thumbnails
			try: #get aaround lazy loading, if present
				self.thumbnails+=[makeLinkFull(thumbnail['data-src'],self.link)]
			except KeyError:
				self.thumbnails+=[makeLinkFull(thumbnail['src'],self.link)]

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
				if self.page.find("This Chapter is not available Yet")!=-1: #find untranslated chapters
					self.available=False
					return
				self.available=True
				self.page=BeautifulSoup(self.page,features="lxml")

				try: #find the long title, if present
					self.title=self.page.find_all('meta',attrs={'property':'og:description'})[1]['content'].strip("   ")
				except IndexError: #else, find short title
					self.title=self.page.title.contents[0].replace(" - "+self.manga.manga+" Manga Online","").strip("   ")

				self.pages=[]
				for page in self.page.find('div',attrs={"class":'entry-content'}).find_all('img'): #find all pages
					try: #get around lazy loading
						self.pages+=[page['data-src']]
					except KeyError:
						self.pages+=[page['src']]

			def __len__(self):
				return len(self.pages)

		def refresh(self): #get parts
			self.parts=[]
			for part in self.manga.chapters:
				if int(part[0])==self.chapter:
					self.parts+=[
						self.Part(
							self,
							part[0],
							part[1]
						)
					]

	def chapter(self,chapter):
		return self.Chapter(self,chapter)