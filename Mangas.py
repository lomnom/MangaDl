import requests
import re
try: 
	from BeautifulSoup import BeautifulSoup
except ImportError:
	from bs4 import BeautifulSoup
from TermManip import *

def removeWWW(link): #www.google.com -> google.com
	return re.sub(
				r'ww?w?\d\d?\.',
				'www.',
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

class InvalidSite(Exception):
	pass

class Manga: 
	def __init__(self,link):
		self.link=link.strip("/")+"/"
		self.refresh()

	def refresh(self):
		self.page=requests.get(self.link).text #remove all wwws, because they mess with the regex
		self.page=BeautifulSoup(self.page,features="lxml")

		if self.page.body.find('div', attrs={'id':'Chapters_List'})==None: #check if site is valid by looking for chapter list
			raise InvalidSite

		chapterList=self.page.body.find('div', attrs={'id':'Chapters_List'}).ul.ul #get ul of chapters
		self.chapterLink=re.sub(
			r"\d[\d-]+",
			"",
			chapterList.li.a['href'].replace(self.link+"manga/","")
				[:-1]
		)

		self.manga=self.page.title.contents[0].replace(" Manga Online","") #get manga name from page title

		self.chapters=0
		for chapter in chapterList.find_all("li"): #get the biggest chapter
			if int(re.findall(r"\d+",chapter.a.contents[0])[0])>self.chapters:
				self.chapters=int(re.findall(r"\d+",chapter.a.contents[0])[0])

		self.info=self.page.find('section',attrs={'id':'text-2'}).div.p.contents[0].strip("\n") #get first paragraph of info

		self.summary=self.page.find('div',attrs={'class':'entry-content'}).find('p').next_sibling.text.strip("\n") #get second paragraph

		self.thumbnails=[]
		for thumbnail in self.page.find('div',attrs={'class':'entry-content'}).ul.find_all('img'): #get all thumbnails
			try: #get around lazy loading, if present
				self.thumbnails+=[makeLinkFull(thumbnail['data-src'],self.link)]
			except KeyError:
				self.thumbnails+=[makeLinkFull(thumbnail['src'],self.link)]

		self.header=makeLinkFull(
			re.findall(
				r"(?<=background: url\()[^\)]+(?=\))",
				self.page.find('style',attrs={'id':"custom-header-css"}).text
			)[0],
			self.link
		)

	def __len__(self):
		return self.chapters

	class Chapter:
		def __init__(self,parentObj,chapterNumber):
			if type(chapterNumber)!=int:
				raise TypeError("Chapter MUST BE INT")
			self.chapter=chapterNumber
			self.manga=parentObj
			self.parentObj=parentObj
			self.refresh()

		class Part:
			def __init__(self,chapter,link):
				self.link=link
				self.chapter=chapter
				self.manga=self.chapter.manga
				self.refresh()

			def refresh(self):
				try:
					self.page=requests.get(self.link).text #lmao
				except requests.exceptions.ConnectionError: #makes the neverland link work, for some reason
					self.link=removeWWW(self.link)
					self.page=requests.get(self.link).text #lmao

				if self.page.find("This Chapter is not available Yet")!=-1: #find untranslated chapters
					self.available=False
					return
				self.available=True
				self.page=BeautifulSoup(self.page,features="lxml")

				try: #find the long title, if present
					self.title=self.page.find_all('meta',attrs={'property':'og:description'})[1]['content'].strip("   ")
				except IndexError: #else, find short title
					self.title=self.page.title.contents[0].replace(" - "+self.manga.manga+" Manga Online","").strip("   ")

				navigation=self.page.find('div',attrs={'class':'nav-links'})
				if navigation==None:
					raise InvalidSite

				self.next=navigation.find('a',attrs={'rel':'next'})
				try:
					self.next=[self.next['href'],self.next.find('span',attrs={'class':'post-title'}).text]
				except TypeError:
					self.next=None
				self.prev=navigation.find('a',attrs={'rel':'prev'})
				try:
					self.prev=[self.prev['href'],self.prev.find('span',attrs={'class':'post-title'}).text]
				except TypeError:
					self.prev=None

				self.pages=[]
				for page in self.page.find('div',attrs={"class":'entry-content'}).find_all('img'): #find all pages
					try: #get around lazy loading
						self.pages+=[page['data-src']]
					except KeyError:
						self.pages+=[page['src']]
				self.pages=list(dict.fromkeys(self.pages))

			def __len__(self):
				return len(self.pages)

		def refresh(self): #get parts
			self.parts=[]
			if self.chapter>self.manga.chapters:
				return
			try:
				self.parts+=[
					self.Part(
						self,
						self.parentObj.link+"manga/"+self.parentObj.chapterLink+str(self.chapter)
					)
				]
			except InvalidSite:
				if self.chapter>=1: 
					prevPart=type(self)(self.manga,self.chapter-1).parts[-1]
					try:
						self.parts+=[
							self.Part(
								self,
								prevPart.next[0],
							)
						]
					except InvalidSite:
						return
				else:
					return
			#add more parts if next chapter of last part is continuous
			if self.parts[-1].next!=None:
				while int(float(self.parts[-1].next[1].split(" ")[-1]))==self.chapter: 
					self.parts+=[
						self.Part(
							self,
							self.parts[-1].next[0]
						)
					]

		def __len__(self):
			return len(self.parts)

	def chapter(self,chapter):
		return self.Chapter(self,chapter)