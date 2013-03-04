#!/bin/bash
## to be executed by SGE on clusternodes
## this just needs the names of input pdb files *.ent
#$ -o /dev/null
#$ -e /mnt/project/pssh/pdb_full/log/hhblits

h=`hostname -s `
I="/mnt/project/pssh/pdb_full/files/seq"
O="/mnt/project/pssh/pdb_full/files/a3m"
T="/mnt/project/pssh/pdb_full/files/hhr"
db="/var/tmp/rost_db/data/hhblits/uniprot20_current"

#fetch uniprot20_current to the cluster node
echo "$h db ready?"

/mnt/project/rost_db/src/fetchUniprot20_hhblits

if [ -s $db"_a3m_db" ]
then
    time (
    for file in $* ; do
	pdbid=${file:0:6}

#	[ -s $O/$pdbid.a3m ] && ( echo $pdbid done ) || (
#		echo "working on $pdbid "
#		echo "hhblits -i $I/$file -d $db -oa3m $O/$pdbid.a3m -o $T/$pdbid.hhr"
#		hhblits -i $I/$file -d $db -oa3m $O/$pdbid.a3m -o $T/$pdbid.hhr
#	)

	until [ -s $O/$pdbid.a3m ] ; do
		echo "working on $pdbid "
		mkdir -p $T/$pdbid 2>/dev/null
		hhblits -i $I/$file -d $db -oa3m $O/$pdbid.a3m -o $T/$pdbid/$pdbid.hhr
	done
	echo "$pdbid done"
	/bin/rm -r $T/$pdbid 2>/dev/null
    done
    )
else
  echo "uniprot20_current_a3m_db is missing"  
fi
