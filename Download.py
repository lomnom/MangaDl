from Mangas import *

sites=[
	"https://w17.read-beastarsmanga.com/",
	"https://toilet-bound-hanako-kun.com/",
	"https://neverland-manga.com/"
]

for site in range(len(sites)):
	sites[site]=Mangas(sites[site])

for site in sites:
	print(site.thumbnails)
	print(site.title)
	print(site.info)
	print(site.summary)
	print(site.chapterLink)
	print(site.chapters)

Mangas("https://google.com")