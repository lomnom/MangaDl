import requests
import re
try: 
	from BeautifulSoup import BeautifulSoup
except ImportError:
	try:
		from bs4 import BeautifulSoup
	except ImportError:
		print("please install BeautifulSoup with 'pip install beautifulsoup4'")

def tryImport(module,pipName,part=""):
	try:
		if part!="":
			exec("global {};from {} import {}".format(part,module,part))
		else:
			exec("global {};import {}".format(module,module))
	except ImportError as error:
		print("please install {} with 'pip install {}'".format(module,pipName))
		raise error
tryImport("requests","requests",part="get")
get("https://google.com")

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

class Mangas:
	def __init__(self,link):
		self.link=removeWWW(link.strip("/")+"/")
		self.refresh()

	def refresh(self):
		self.page=removeWWW(requests.get(self.link).text) #lmao
		self.page=BeautifulSoup(self.page,features="lxml")

		if self.page.body.find('div', attrs={'id':'Chapters_List'})==None:
			raise ValueError(
				"Site {} is not a valid manga site! It should look like https://toilet-bound-hanako-kun.com!"
					.format(self.link)
			)

		chapterList=self.page.body.find('div', attrs={'id':'Chapters_List'}).ul.ul
		self.chapterLink=re.sub(
			r"\d[\d-]+",
			"",
			chapterList.li.a['href'].replace(self.link+"manga/","")
				[:-1]
		)

		self.chapters=[]
		for chapter in chapterList.find_all("li" , recursive=False):
			self.chapters+=[self.extractChapter(chapter.a['href'])]
		self.chapters.sort()

		self.title=self.page.title.contents[0].replace(" Manga Online","")

		self.info=self.page.find('section',attrs={'id':'text-2'}).div.p.contents[0].strip("\n")

		self.summary=self.page.find('div',attrs={'class':'entry-content'}).find('p').next_sibling.text.strip("\n")

		self.thumbnails=[]
		for thumbnail in self.page.find('div',attrs={'class':'entry-content'}).ul.find_all('img'):
			self.thumbnails+=[makeLinkFull(thumbnail['src'],self.link)]

	def extractChapter(self,link):
		return float(link.replace(self.link+"manga/"+self.chapterLink,"").replace("-",".")[:-1])