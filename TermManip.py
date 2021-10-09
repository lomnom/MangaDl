black="\033[30m" #escape codes to change terminal fg color
red="\033[31m"
green="\033[32m"
yellow="\033[33m"
blue="\033[34m"
magenta="\033[35m"
cyan="\033[36m"
white="\033[37m"
default="\033[39m"
reset="\033[0m"

first='─' 
middle='├' 
end="└"  
tree="│"

from os import get_terminal_size

colcurs="\033[{}G" #go to column {}-1
clrtoeol="\033[0K" #clear to end of line
bars=["","▏","▎","▍","▌","▋","▊","▉","█"]

def loadingBar(width,percentage): #make a bar of width width, percentage% filled
	units=(width*8)*(percentage/100)
	if units>width*8:
		units=width*8
	return ((bars[8]*int(units/8))+bars[int(units%8)]).ljust(width," ")

def wrap(string,chars):
	chunks=[]
	while len(string)>chars:
		chunks+=[string[:chars]]
		string=string[chars:]
	if string!="":
		chunks+=[string]
	return chunks

prefixes=[] #store existing branches
def node(key,data="",bracketed="",last=False):
	global prefixes
	if len(prefixes)==0: 
		output=yellow+first+reset #if there are no existing branches, the prefix is root
	else:
		output=yellow+"".join(prefixes[:-1])+"  " #if there are existing branches, add all branches but present
		if last: #add present branch according to context
			output+=end
		else:
			output+=middle
	output+=reset+" " #add padding for data
	if data=='': #if there is data, set to blue. 
		output+=blue 
	else: #else, set to cyan
		output+=cyan
	output+=key #add key, that can also be data if "data"==''

	if bracketed!="": #add bracketed data beside key
		output+=green+" ("+bracketed+")"
	if data=="\n": #if data='\n', make colon yellow to signify nesting
		output+=yellow+":"+reset
	elif data!="": #if not nesting and data present, add data after colon and key
		output+=cyan+": "+blue+data+reset
	print(output)

	if last and not data=='\n': #if need last node and not nesting, remove present branch and descend to most recent branch
		prefixes.pop(-1)
		for prefix in reversed(range(len(prefixes))):
			if prefixes[prefix]=="   ":
				prefixes.pop(prefix)
			else:
				break
	if data=='\n': #if going down one level, add own branch
		if last: #if last node, remove previous branch
			prefixes[-1]="   "
		prefixes+=["  │"]