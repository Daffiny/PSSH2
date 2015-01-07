#!/usr/bin/python

#from DatabaseTools import *
import sys, os, argparse, re

# preprequisite for this import to work on local Mac:
# set up tunnel: 
# ssh -L 3307:192.168.1.47:3306 andrea@rostlab
# have local config file

# TODO: Either get the database to work or write a tsv and import by hand
# TODO: in any case: extract md5 sum from file path

def main(argv):

#	parser = argparse.ArgumentParser()
#	parser.add_argument("seqfile", help="fasta sequence file to upload")
#	args = parser.parse_args()
	# make a connection to the database
#	db_connection = DB_Connection()
#	db_name = 'pssh2'
#	submitConnection = db_connection.getConnection(db_name,'updating')
	
	# prepare our regexes
	hhmFilt = re.compile("^FILT\s+(\d+) out of (\d+) ")
	hhmNeff = re.compile("^NEFF\s+(\d+.\d+)")
	
	# loop over the result directories
	cacheDir = '/mnt/project/psshcache/result_cache_2014/'
#	testDir = '/mnt/project/psshcache/result_cache_2014/0b/00'
	testDir = '/mnt/project/psshcache/result_cache_2014/0b/'
	
#	for root, dirs, filenames in os.walk(cacheDir):
	for root, dirs, filenames in os.walk(testDir):
	
		# print root, ' ', dirs, ' ', filenames
	
		for f in filenames:
			fileName, fileExtension = os.path.splitext(f)
			# print fileName, ' ', fileExtension
			
			if (fileExtension == '.hhm'):
				filepath = os.path.join(root, f)
				print filepath
				
				filehandle = open(filepath)
				lines = filehandle.readlines()
				filehandle.close()

				# print 'file: ', filepath

				for line in lines:
					filterMatch = hhmFilt.match(line)
					if (not filterMatch is None):
						seqNum1 = filterMatch.group(1)
						seqNum2 = filterMatch.group(1)
						continue
					neffMatch = hhmNeff.match(line)
					if (not neffMatch is None):
						neff = neffMatch.group(1)
						# neff is the last match we are looking for
						break
						
				print 'file: ', filepath, ' -> neff, seqs: ', neff, ' ', seqNum1, ' ', seqNum2
						
			
		



if __name__ == "__main__":
	main(sys.argv[1:])
