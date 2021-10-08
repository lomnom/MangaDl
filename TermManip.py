black="\033[30m"
red="\033[31m"
green="\033[32m"
yellow="\033[33m"
blue="\033[34m"
magenta="\033[35m"
cyan="\033[36m"
white="\033[37m"
default="\033[39m"
reset="\033[0m"

first= yellow+'─'+reset #─ mangaSite.com
middle=yellow+'├'+reset #  ├ chapter 1
end=  yellow+"└"+reset #  │ └ part 1
tree=  yellow+"│"+reset

upcolcurs="\033[{}A\033[{}G" #up,col
downcolcurs="\033[{}B\033[{}G" #down,col
colcurs="\033[{}G"
clrtoeol="\033[0K"
bars=["","▏","▎","▍","▌","▋","▊","▉","█"]

def loadingBar(width,percentage):
	units=(width*8)*(percentage/100)
	if units>width*8:
		units=width*8
	return ((bars[8]*int(units/8))+bars[int(units%8)]).ljust(width," ")

prefixes=[]
def node(key,data="",bracketed="",last=False):
	global prefixes
	if len(prefixes)==0:
		output=first
	else:
		output=yellow+"".join(prefixes[:-1])+"  "+reset
		if last:
			output+=end
		else:
			output+=middle
	output+=" "
	if data=='\n' or data=='':
		output+=blue
	else:
		output+=cyan
	output+=key
	if bracketed!="":
		output+=green+" ("+bracketed+")"
	if data=="\n":
		output+=yellow+":"
	elif data!="":
		output+=cyan+": "+blue+data+reset
	print(output)

	if last and not data=='\n':
		prefixes.pop(-1)
		for prefix in reversed(range(len(prefixes))):
			if prefixes[prefix]=="   ":
				prefixes.pop(prefix)
			else:
				break
	if data=='\n':
		if last:
			prefixes[-1]="   "
		prefixes+=["  │"]