#!/usr/bin/python

#import requests
import re
import json
import time
import sys, os, argparse
import colorsys
import requests
from itertools import groupby
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.Alphabet import generic_protein
from Bio.Seq import Seq
from bs4 import BeautifulSoup
import socket,time,commands

from enable.savage.svg.css.values import length
from win32netcon import USER_NAME_INFOLEVEL

sys.path.insert(0,'/path/to/src/python/DatabaseTools')

from DatabaseTools import SequenceStructureDatabase


# preprequisite for this import to work on local Mac:
# set up tunnel:
# ssh -L 3307:192.168.1.47:3306 andrea@rostlab
# have local config file


def main(argv):

	parser = argparse.ArgumentParser()
	parser.add_argument("-s", "--seq", help="fasta sequence to process")
	parser.add_argument("-u", "--uniprotAcc", help="uniprot Accession number of sequence to process")
	parser.add_argument("-m", "--md5", help="md5 sum of sequence to process")
	parser.add_argument("-d", "--details", help="flag to specify whether to give details or just a summary", action='store_true')
	parser.set_defaults(details=False)
	args = parser.parse_args()

	sequence = ''
	uniprotAcc = ''
	md5 = ''
	mysqlClause = ''
	fastaString = ''
	name = ''
	if (args.seq):
		name = 'usrSequence_'
		timestamp = int(100*time.time())
		name += str(timestamp) 
		sequence = args.seq
		fastaString = ">" + name + " \n"
		fastaString += sequence + "\n"
	elif (args.uniprotAcc):
		uniprotAcc = args.uniprotAcc
		sequenceHandler = SequenceStructureDatabase.SequenceHandler()
		fastaString = sequenceHandler.getFastaSequenceByAccession(uniprotAcc)
		name = uniprotAcc
	elif (args.md5):
		md5 = args.md5
		sequenceHandler = SequenceStructureDatabase.SequenceHandler()
		fastaString = sequenceHandler.getFastaSequenceByMd5(md5)
		name = md5
	else:
		sys.exit(2)

	details = False
	if (args.details):
		details = True
	
	# if we got a sequence really, then retrieve PP result location
	predictionPath = ''
	if (fastaString):
		predictionPath = queryPP(name, fastaString)
	
	# if we got a PP result location, start parsing
	if (predictionPath):
		predictions = []
#		isis_json = parse_isis(predictionPath)
#		someNA_json = parse_someNA(predictionPath)
		if (details):
			PHDhtm_annot = parse_PHDhtm_details(predictionPath)
		else:
			PHDhtm_annot = parse_PHDhtm_summary(predictionPath)

		if (PHDhtm_annot):
			predictions.append(PHDhtm_annot)
	
	predictionObj =  predictions 
	jsonText = json.dumps(predictionObj)
	print jsonText
	# ...

def queryPP(sequences):
	"""write fasta sequence to a file
		call ppc_fetch for the file
		return the directory the predictions are stored in
		"""
	# TODO
	file_store_path="/mnt/project/aquaria/public_html/snap4aquaria"
	#id is named from time
	id= str(time.time()).split('.')[0] #catch time

	Seq_Rercord = SeqRecord(Seq(sequences, generic_protein),
					 id=id,
					 description=id+" submission")
	file_name = id+".fasta"
	print Seq_Rercord
	fasta_file = SeqIO.write(Seq_Rercord, file_store_path, "fasta")
	'''
	client = paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


	#=========delete afterward======

	hostname = 'rostssh.informatik.tu-muenchen.de'
	user_name = 'yichunlin'
	Password = 'daffinylin'

	client.connect(hostname=hostname, port = 8574,username=user_name, password= Password)
	channel = client.invoke_shell()

	# scp file from rost to jobtest
	channel.send("scp "+full_file_name+" "+ user_name+ "@n03:"+file_store_path_n03+"\n")

	buff = ''
	while not buff.endswith('\'s password: '):
		time.sleep(3)
		resp = channel.recv(2024)
		buff += resp

	# Send the password and wait for a prompt.
	channel.send(Password+'\n')
	buff = ''
	while buff.endswith(user_name +'@n03:~$'):
		time.sleep(3)
		resp = channel.recv(2024)
		buff += resp
	#===================

	channel.send('ssh jobtest \n')
	buff = ''
	while not buff.endswith('\'s password: '):
		time.sleep(3)
		resp = channel.recv(2048)
		buff += resp

	# Send the password and wait for a prompt.
	channel.send(Password+'\n')
	buff = ''
	while buff.endswith(user_name +'@n03:~$'):
		time.sleep(3)
		resp = channel.recv(2048)
		buff += resp

	buff = ''
	while channel.recv_ready():
		channel.recv(2048)

	output = []
	#call(["ppc_fetch --seqfile "+file_store_path_n03+"/"+file_name+" \n"])
	channel.send("ppc_fetch --seqfile "+file_store_path_n03+"/"+file_name+" \n")
	channel.settimeout(5)
	text = commands.getoutput("ppc_fetch --seqfile "+file_store_path_n03+"/"+file_name+" \n")

	buff = ''
	try:
		while buff.find('/mnt/'):
			time.sleep(3)
			resp = channel.recv(9999)
			buff += resp
			output.append(resp)
	except socket.timeout:
			print "Timeout"
	'''
	output = commands.getoutput("ppc_fetch --seqfile "+file_store_path+"/"+file_name+" \n")

	# filter the string
	s = output[0].split('\r\n')
	i = 0
	filter_output = []
	for i in range(0, len(s)-1):
		if s[i].startswith('/mnt/',0,5):
			filter_output.append(s[i])

	# return dirctory
	predictiondirectory = ""
	splitstr = filter_output[0].split('/')
	for j in range(1,len(splitstr)-1):
		predictiondirectory = predictiondirectory+'/'+splitstr[j]

	return predictiondirectory


def parse_PHDhtm_summary(predictionPath):

	source = 'phdHTM'
	description = 'Predicted transmembrane helices'
	url = 'https://rostlab.org/owiki/index.php/PredictProtein_-_Documentation#Transmembrane_helices_.28PHDhtm.29'

	rexp = re.compile('PHDRhtm \|[\sH]*\|')


	#get position ranges for which a tm was predicted
	global  rangeList,annotationObj
	rangeList=[]
	annotationObj = {}
	s=''
	phd=0
	rexp = re.compile('[H]+')
	with open(predictionPath+'\query.phdPred','r') as f:
		for line in f:
			if line.startswith("#")|line.startswith("-"):
				continue
			if "PHDRhtm" in line:
				s+=line.split('|',2)[1]

		p=[(s.start() +phd, s.end()+ phd) for s in rexp.finditer(s)]

        for i in range(0,len(p)):
                featureObj = {'Name': 'PHDhtm regions', 'Residues':p[i]}
                rangeList.append(featureObj)

	# first look whether there is anything in the range list!
	if len(rangeList) > 0:
		annotationObj = {'Transmembrane regions (Prediction by PHDhtm)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features':rangeList}}

	#JSONstr = json.dumps(annotationObj)
	return annotationObj

def parse_PHDhtm_details(predictionPath):
	"""parse out details of  PHDhtm output (transmembrane helix predictions with reliablity)"""

#	JSONstr = ''

	source = 'phdHTM'
	description = 'predictions -- colored by reliablities -- for transmembrane residues and topology: inside / ouside'
	url = 'https://rostlab.org/owiki/index.php/PredictProtein_-_Documentation#Transmembrane_helices_.28PHDhtm.29'

	phdFile = open(predictionPath+'/query.phdRdb','r')

	# check whether any transmembrane helices ar predicted (changes output format)
	htmString = 'NHTM_BEST'
	# skip until the beginning of predictions
	reHeader = re.compile('4N\t1S\t1S\t1N\t1N')
	# then read the actual data
#   1	M	L	9	0	9	  2	 97	L	L	o
	reData = re.compile('\s*(\d+)\t\w\t\w\t(\d)\t\d\t\d\t\s*(\d+)\t\s*(\d+)\t(\w)\t\w\t(\w)')

	# for colors see e.g. http://colorizer.org/
#	membraneBaseColHsv = (16, 1.0, 1.0)    # orange: rgb(252, 67, 0)   hsv(16, 100%, 100%)
#	insideBaseColHsv =   (54, 1.0, 1.0)    # yellow: rgb(255, 229, 0)  hsv(54, 100%, 100%)
#	outsideBaseColHsv = (202, 1.0, 1.0)    # blue: rgb(0, 162, 255) hsv(202, 100%, 100%)
	membraneHue = 16.0 /360   # orange: rgb(252, 67, 0)   hsv(16, 100%, 100%)
	insideHue   = 54.0 /360   # yellow: rgb(255, 229, 0)  hsv(54, 100%, 100%)
	outsideHue = 202.0 /360   # blue: rgb(0, 162, 255) hsv(202, 100%, 100%)

	features = []

	print 'start'
	hasHtm = False
	for line in phdFile:
		#print line, ": "
		if (not hasHtm):
			if htmString in line:
				hasHtm = True
				#print 'has htm'
				continue
			elif reHeader.match(line):
				# we haven't found an indicator that there are Htms, but we have reached the header,
				# so we can stop parsing
				#print 'no htm, but header -> break'
				break
		else:
			match = reData.match(line)
			if match:
#				print 'matches ', reData, ': ', match.group(0)
				residueNumber = int(match.group(1))
				if (residueNumber > 0):

					name = ''
					reliabilityRgb = ()

					# get out the info
					topology = match.group(6)
					if (topology == 'o'):
						hue = outsideHue
						name = 'outside '
					elif (topology == 'i'):
						hue = insideHue
						name = 'inside '
					elif (topology == 'T'):
						hue = membraneHue
						name = 'transmembrane '

					tmhState = match.group(5)
					if (tmhState == 'H'):
						name += 'helix'
						predictionStrength = match.group(3)   #OtH
					elif (tmhState == 'L'):
						name += 'loop'
						predictionStrength = match.group(4)  #OtL

#					reliablityRatio = int(match.group(2))/9.0
					reliablityRatio = int(predictionStrength)/100.0
#					hsvColor = hue, 1.0, reliablityRatio
					#print hue, " ", 1.0, " ", reliablityRatio
					rgbColor = colorsys.hsv_to_rgb(hue, 1.0, reliablityRatio)
					#print rgbColor
					reliabilityRgb = reformatColor(rgbColor)
#					reliabilityRgb = reformatColor(colorsys.hsv_to_rgb(hue, 1.0, reliablityRatio))
					colorHex = '#%02x%02x%02x' % reliabilityRgb
					#print colorHex

					# make a feature

					featureObj = {'Name': name, 'Residue':residueNumber, 'Color': colorHex}
					features.append(featureObj)

	if (len(features) > 0):
		annotationObj = {'Transmembrane regions (Prediction by PHDhtm)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features': features }}
	else:
		annotationObj =[]
		print 'not annoations found!'

	return annotationObj

def reformatColor(color):
    return int (round (color[0] * 255)), \
           int (round (color[1] * 255)), \
           int (round (color[2] * 255))

def parse_prof_summary(predictionPath):

	source = 'prof'
	description = 'Predicted secondary structure and solvent accessibility'
	url = 'https://rostlab.org/owiki/index.php/PredictProtein_-_Documentation#Secondary_Structure.2C_Solvent_Accessibility_and_Transmembrane_Helices_Prediction'

	profFile = open(predictionPath+'\query.profAscii','r')
	profText = profFile.read()

	#get secondary structure
	h, e = re.compile("H+"), re.compile("E+")
	sm=0
	m=''
	SecList=[]
	with open(predictionPath+'\query.profAscii','r') as f:
		for line in f:
			#print line
			if line.startswith("#")|line.startswith("|"):
				continue
			if " PROF_sec" in line:
				m+=line.split('|',2)[1]

	SecHList=([(s.start() +sm, s.end()+ sm) for s in h.finditer(m)])
	SecEList=([(s.start() +sm, s.end()+sm) for s in e.finditer(m)])

	List=SecHList+SecEList
	for i in range(0,len(List)):
		list={'Name':'prof','Residues':List[i]}
		SecList.append(list)

		# first look whether there is anything in the range list!

	if (len(SecList)) > 0:
		secannotationObj = {'Secondary structure (Prediction by prof)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features':SecList}}


	#get solvent accessibility\
	accList=[]
	acc=0
	a=''
	List=" "
	accb, e = re.compile("b+"), re.compile("e+")
	with open(predictionPath+'\query.profAscii','r') as f:
		for line in f:

			if line.startswith("#")|line.startswith("|"):
				continue
			if "SUB_acc" in line:
				a+=line.split('|',2)[1]

		accbList=([(s.start() +acc, s.end()+ acc) for s in accb.finditer(a)])
		acceList=([(s.start() +acc, s.end()+acc) for s in e.finditer(a)])
		List=accbList+acceList
		for i in range(0,len(List)):
			alist={'Name':'prof','Residues':List[i]}
			accList.append(alist)

	# first look whether there is anything in the range list!
	if len(accList) > 0:
		accannotationObj = {'Solvent accessibility (Prediction by prof)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features':accList}}

	#		JSONstr = json.dumps(obj)
	return secannotationObj,accannotationObj

def parse_prof_details(predictionPath):
	"""parse out details of  prof output """

#	JSONstr = ''

	source = 'prof'
	description = 'predictions -- colored by reliablities -- for secondary structure residues and Solvent Accessibility'
	url = 'https://rostlab.org/owiki/index.php/PredictProtein_-_Documentation#Secondary_Structure.2C_Solvent_Accessibility_and_Transmembrane_Helices_Prediction'

	profFile = open(predictionPath+'/query.profRdb','r')

	# then read the actual data
	# for colors see e.g. http://colorizer.org/
#	membraneBaseColHsv = (16, 1.0, 1.0)    # orange: rgb(252, 67, 0)   hsv(16, 100%, 100%)
#	insideBaseColHsv =   (54, 1.0, 1.0)    # yellow: rgb(255, 229, 0)  hsv(54, 100%, 100%)
#	outsideBaseColHsv = (202, 1.0, 1.0)    # blue: rgb(0, 162, 255) hsv(202, 100%, 100%)
	membraneHue = 100.0 /360   # yellow: rgb(85, 255, 0)  hsv(100, 100%, 100%)
	insideHue   = 350.0 /360   # pink: rgb(255, 0, 50)   hsv(350, 100%, 100%)
	outsideHue = 202.0 /360   # blue: rgb(0, 162, 255) hsv(202, 100%, 100%)

	features = []
	accfeatures = []

	global hue
	hue = ""
	for line in profFile:
		if line.startswith('#')| line.startswith('No'):
			continue

		line=line.split('\t')

		if len(line) != 30:
			continue
		residueNumber = line[0]

		if (residueNumber > 0):
			#=======Secondary structure======
			name = ''
			reliabilityRgb = ()

			# get out the info
			structure = line[3] #PHEL
			if (structure == 'H'):
				hue = outsideHue
				name = 'helix '
			elif (structure == 'E'):
				hue = insideHue
				name = 'extended '
			elif (structure == 'L'):
				hue = membraneHue
				name = 'other '

			predictionStrength = line[4] #RI_S

			reliablityRatio = (float(predictionStrength)+1)/10.0
			#print 'reliablityRatio:',reliablityRatio
#					hsvColor = hue, 1.0, reliablityRatio


			rgbColor = colorsys.hsv_to_rgb(hue, 1.0, reliablityRatio)
			#print 'rgbColor',rgbColor
			reliabilityRgb = reformatColor(rgbColor)
#					reliabilityRgb = reformatColor(colorsys.hsv_to_rgb(hue, 1.0, reliablityRatio))
			colorHex = '#%02x%02x%02x' % reliabilityRgb
			#print colorHex

			# make a feature
			secfeatureObj = {'Name': name, 'Residue':residueNumber, 'Color': colorHex, 'Description': predictionStrength}
			features.append(secfeatureObj)


			#=======Solvent accessibility======
			accname = ''

			# get out the info
			states = line[14] #Pbe
			if (states == 'b'):
				hue = outsideHue
				accname = 'buried '
			elif (states == 'e'):
				hue = membraneHue
				accname = 'exposed '

			accpredictionStrength = line[9] #RI_A

			accreliablityRatio = (float(accpredictionStrength)+1)/10.0
			#print 'accreliablityRatio:',accreliablityRatio

			rgbColor = colorsys.hsv_to_rgb(hue, 1.0, accreliablityRatio)
			#print 'rgbColor',rgbColor
			accreliabilityRgb = reformatColor(rgbColor)

			acccolorHex = '#%02x%02x%02x' % accreliabilityRgb
			#print acccolorHex

			# make a feature
			accfeatureObj = {'Name': accname, 'Residue':residueNumber, 'Color': acccolorHex,'Description':accpredictionStrength}
			accfeatures.append(accfeatureObj)

	if (len(accfeatures) > 0):
		accannotationObj = {'Solvent Accessibility (Prediction by prod)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features': accfeatures }}
#			JSONstr = json.dumps(annotationObj)
	else:
		accannotationObj =[]
		print 'not solvent accessibility annoations found!'

	if (len(features) > 0):
		secannotationObj = {'Secondary Structure (Prediction by prod)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features': features }}
	else:
			secannotationObj =[]
			print 'not secondary structure annoations found!'

	return secannotationObj,accannotationObj

def parse_isis_details(predictionPath):
	source = 'isis'
	description = 'Predicted Binding Sites'
	url = 'https://rostlab.org/owiki/index.php/PredictProtein_-_Documentation'

	#get Protein Binding Sites
	features=[]
	with open(predictionPath+'\query.isis','r') as f:
		for line in f:
			if line[0].isdigit()==True:
				line=line.split(' ')
				residueNumber=line[0]
				letter = line[1]
				number=int(line[2])
				#membraneHue = 16.0 /360   # orange: rgb(252, 67, 0)   hsv(16, 100%, 100%)
				#insideHue   = 54.0 /360   # yellow: rgb(255, 229, 0)  hsv(54, 100%, 100	%)

				if number > 0:

					reliablityRatio = (float(number)/100.0)+0.5

					rgbColor = colorsys.hsv_to_rgb(150, 1.0, reliablityRatio)
					print 'rgbColor',rgbColor
					accreliabilityRgb = reformatColor(rgbColor)
					acccolorHex = '#%02x%02x%02x' % accreliabilityRgb

					desc = 'protein binding site, ISIS score: '+ str(number)
					# make a feature
					featureObj = {'Name': "Binding site", 'Residue':residueNumber, 'Color': acccolorHex, 'Description': desc}
					features.append(featureObj)


	# first look whether there is anything in the range list!

	if (len(features)) > 0:
		annotationObj = {'Binding Sites (Prediction by isis)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features':features}}

	#		JSONstr = json.dumps(obj)
	return annotationObj

def parse_mdisorder_details(predictionPath):
	source = 'mdisorder'
	description = 'Predicted Protein Disorder'
	url = 'https://rostlab.org/owiki/index.php/PredictProtein_-_Documentation'
	file = open(predictionPath+'\query.mdisorder','r')
	global diorderObj
	diorderObj = []
	#get Protein Disorder
	List=[]
	with file as f:
		for line in f:
			line=line.split(' ')
			line=filter(None,line)
			line=line[0].split("\t")
			if line[0].isdigit()==True:

				if line[10] == "D\n": #MD2st
					residueNumber=line[0]
					letter = line[1]
					number=int(line[9]) #MD_rel
					hue = 54.0 /360   # yellow: rgb(255, 229, 0)  hsv(54, 100%, 100%)

					reliablityRatio = float(number+1)/10.0 #avoid 0/10

					rgbColor = colorsys.hsv_to_rgb(float(hue)+1, 1.0, reliablityRatio+0.3)
					#print 'rgbColor',rgbColor
					reliabilityRgb = reformatColor(rgbColor)

					colorHex = '#%02x%02x%02x' % reliabilityRgb

					desc = "Disordered: "+ str(number)
					# make a feature
					featureObj = {'Name': "Disordered", 'Residue':residueNumber, 'Color': colorHex,"Description": desc}
					List.append(featureObj)


	# first look whether there is anything in the range list!

	if (len(List)) > 0:
		diorderObj = {'Protein Disorder (Prediction by mdisorder)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features':List}}

	#		JSONstr = json.dumps(obj)
	return diorderObj

def parse_disulfinder_details(predictionPath):
	source = 'disulfinder'
	description = 'Predicted Disulphide Bridge'
	url = 'https://rostlab.org/owiki/index.php/PredictProtein_-_Documentation'

	profFile = open(predictionPath+'\query.disulfinder','r')
	soup = BeautifulSoup(profFile, 'html.parser')

	content = soup.get_text()
	AAList=""
	DB_stateList=""
	DB_confList=""
	List = []
	for line in content.splitlines():
		line = line.split(" ",1)
		if line[0] in['AA']:
			if len(line)>=2:
				AA = line[1].replace(" ","")
				AAList = AAList+AA.encode('utf-8')
		elif line[0] in ['DB_state']:
			if len(line)>=2:
				DB_state=line[1] #1=disulfide bonded, 0=not disulfide bonded
				DB_stateList=DB_stateList+DB_state.encode('utf-8')
		elif line[0] in ['DB_conf']:
			if len(line)>=2:
				DB_conf=line[1][1:]
				DB_confList=DB_confList+DB_conf.encode('utf-8')

	#get Protein Disorder
	global  hue

	for i in range(0,(len(AAList))):
		if DB_stateList[i] != " ":
			if DB_stateList[i] =="0": #0=not disulfide bonded
				hue = float(60*((int(DB_confList[i]))/2))/360
				#hue = 54.0 /360   # yellow: rgb(255, 229, 0)  hsv(54, 100%, 100%)
				desc="Not Disulfide bonded: " +DB_confList[i]
			elif DB_stateList[i] =="1":  #1=disulfide bonded
				hue = 0.0   # Gray: rgb(128,128,128)	 hsv(0, 0%, 50%)
				desc="Disulfide bonded: " + DB_confList[i]

			hue=float("{0:.1f}".format(hue))
			#	reliablityRatio = float(number+1)/10.0 #avoid 0/10
			if float(DB_confList[i])%2 == 0:
				reliablityRatio = 0.5 # 0.5
			else:
				reliablityRatio = 1.0 # 1

			rgbColor = colorsys.hsv_to_rgb(hue, 1.0, reliablityRatio)
			print 'rgbColor',rgbColor
			accreliabilityRgb = reformatColor(rgbColor)
			acccolorHex = '#%02x%02x%02x' % accreliabilityRgb
			featureObj = {'Name': "Disulphide Bridges", 'Residue':i+1, 'Color': acccolorHex,
						  "Description": desc}

			List.append(featureObj)

	# first look whether there is anything in the range list!

	if (len(List)) > 0:
		disulfinderObj = {'Protein Disulphide Bridge (Prediction by disulfinder)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features':List}}

	#		JSONstr = json.dumps(obj)
	return disulfinderObj

def pare_all_details(path):

	dic1=parse_PHDhtm_details(path)
	dic2,dic3 = parse_prof_details(path)
	dic4=parse_isis_details(path)
	dic5=parse_mdisorder_details(path)
	dic6=parse_disulfinder_details(path)

	all_dic=dic1.copy()
	all_dic.update(dic2)
	all_dic.update(dic3)
	all_dic.update(dic4)
	all_dic.update(dic5)
	all_dic.update(dic6)

	return all_dic
if __name__ == "__main__":
        main(sys.argv[1:])


