import requests
import re
try: 
	from BeautifulSoup import BeautifulSoup
except ImportError:
	from bs4 import BeautifulSoup
from TermManip import *

def removeWWW(link): #www.google.com -> google.com
	return re.sub(
				r'w{1,3}\d{0,2}\.',
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

class InvalidSite(Exception):
	pass

class Manga: 
	def __init__(self,link):
		self.link=link.strip("/")+"/"
		self.refresh()

	def refresh(self):
		self.page=requests.get(self.link).text 
		self.page=BeautifulSoup(self.page,features="lxml")

		if self.page.body.find('div', attrs={'id':'Chapters_List'})==None: #check if site is valid by looking for chapter list
			raise InvalidSite

		chapterList=self.page.body.find('div', attrs={'id':'Chapters_List'}).ul.ul #get ul of chapters
		if not chapterList.li.a['href'].startswith(self.link): #mandle irregular wwws
			self.chapterLink=re.sub(
				r"\d[\d-]+",
				"",
				removeWWW(chapterList.li.a['href']).replace(self.link+"manga/","")
					[:-1]
			)
		else:
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

		try:
			self.info=self.page.find('section',attrs={'id':'text-2'}).div.p.text.strip("\n") #get first paragraph of info
		except:
			self.info=""

		try:
			self.summary=self.page.find('div',attrs={'class':'entry-content'}).find('p').next_sibling.text.strip("\n") #get second paragraph
		except:
			self.summary=""

		self.thumbnails=[]
		for thumbnail in self.page.find('div',attrs={'class':'entry-content'}).ul.find_all('img'): #get all thumbnails
			try: #get around lazy loading, if present
				self.thumbnails+=[makeLinkFull(thumbnail['data-src'],self.link)]
			except KeyError:
				self.thumbnails+=[makeLinkFull(thumbnail['src'],self.link)]
		self.thumbnails=list(dict.fromkeys(self.thumbnails))

		self.header=makeLinkFull(
			re.findall( #parsing css with regex be like
				r"(?<=background: url\()[^\)]+(?=\))",
				str(self.page.find('style',attrs={'id':"custom-header-css"}))
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
				except requests.exceptions.ConnectionError: #fix irregular wwws
					try:
						self.link=removeWWW(self.link)
						self.page=requests.get(self.link).text #lmao
					except Exception as e:
						raise InvalidSite
						
				self.available=True
				self.page=BeautifulSoup(self.page,features="lxml")

				self.title=self.page.title.contents[0].replace(" - "+self.manga.manga+" Manga Online","")\
					.strip("   ").split("\n")[0] 

				try: #find the long title, if present
					longtitle=self.page.find_all('meta',attrs={'property':'og:description'})[1]['content']\
						.strip("   ").split("\n")[0] #remove common garbage
					if len(longtitle)>len(self.title):
						self.title=longtitle
				except IndexError: 
					pass

				self.title=self.title.replace("\r","") #making wierd ?s in filename

				self.created=re.findall(
					r'(?<="datePublished":")\d\d\d\d-\d\d-\d\d(?=T\d\d:\d\d:\d\d\+\d\d:\d\d")',
					self.page.find('script',attrs={
						'type':'application/ld+json'
					}).contents[0]
				)[0]

				try:
					self.edited=re.findall(
						r'(?<="dateModified":")\d\d\d\d-\d\d-\d\d(?=T\d\d:\d\d:\d\d\+\d\d:\d\d")',
						self.page.find('script',attrs={
							'type':'application/ld+json'
						}).contents[0]
					)[0]
				except IndexError:
					self.edited=None

				navigation=self.page.find('div',attrs={'class':'nav-links'})
				if navigation==None: #even if theres only one chapter it'll still be present
					raise InvalidSite

				self.next=navigation.find('a',attrs={'rel':'next'}) 
				try: #last chapter
					self.next=[self.next['href'],self.next.find('span',attrs={'class':'post-title'}).text]
				except TypeError:
					self.next=None
				self.prev=navigation.find('a',attrs={'rel':'prev'})
				try: #first chapter
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

				if len(self.pages)==0:
					self.available=False

			def __len__(self):
				return len(self.pages)

		def refresh(self): #get parts
			self.parts=[]
			if self.chapter>self.manga.chapters: #make self a nonexistent chapter if its out of bounds
				return
			try:
				self.parts+=[ #get first part
					self.Part(
						self,
						self.parentObj.link+"manga/"+self.parentObj.chapterLink+str(self.chapter)
					)
				]
			except InvalidSite: #get self from last part of previous chapter if invalid
				if self.chapter>1: 
					prevPart=type(self)(self.manga,self.chapter-1).parts[-1]
					try:
						self.parts+=[
							self.Part(
								self,
								prevPart.next[0],
							)
						]
					except InvalidSite: #hope first chapter isnt invalid
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