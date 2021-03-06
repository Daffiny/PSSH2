#!/bin/bash
## batch_run_generate_pssh2.sh <inputDirPath> <ouputDirPath> <arrayjob_nr> <subjob_nr> <list of md5sums> 
## to be executed by SGE on cluster-nodes as a single arrayjob unit 

# PARAMETERS
tmp_loc="/tmp/pssh2/" 
script_path="/mnt/project/pssh/pssh2_project/src/"
fetch_uniprot="/mnt/project/rost_db/src/fetchUniprot20_hhblits"

big_option=$1   # whether to increase the memory for hhblits
shift
queries_dir=$1  # directory containing the fasta sequences named by md5 sum
shift
out_pssh2=$1    # permanent output directory for pssh2 files of multiple sequences
shift
arrayjob_nr=$1  # number of currently running arrayjob (nicely formatted)
shift
subjob_nr=$1    # number of currently running subjob (nicely formatted)
shift
tmp_hhblits="$tmp_loc/hhblits_files/$arrayjob_nr"
mkdir -p $tmp_hhblits 2>/dev/null
tmp_pssh2="$tmp_loc/pssh2_files/$arrayjob_nr"   
mkdir -p $tmp_pssh2 2>/dev/null
#out_pssh2="/mnt/project/pssh/pssh2_files"

echo fetching data
echo $fetch_uniprot
$fetch_uniprot
echo $script_path/pdb_full/fetch_pdb_full_hhblits_pssh.pl
$script_path/pdb_full/fetch_pdb_full_hhblits_pssh.pl 
#(for pssh/pdb_full/db copy) 
#thisdate=`date +%s`

if [ $big_option == 'b' ] ;
then
    big=" -b "
else 
    big=" "
fi

out_file=$tmp_pssh2/$arrayjob_nr'_'$subjob_nr'.pssh2'  # name of concatenated pssh2 files of this subjob
out_file_failed=$out_file'.failed_md5'
rm $out_file   # make sure there are no left-overs from last time we ran this!
time (
for md5sum in $* ; do
    echo $md5sum
    $script_path/pssh2/generate_pssh2.pl -m $md5sum -d $queries_dir -t $tmp_hhblits -o $tmp_pssh2 $big
# concatenate the parsed output files into one file with the subjob number
    if [ -s $tmp_pssh2/$md5sum'.pssh2'  ] ;
    then
	cat $tmp_pssh2/$md5sum'.pssh2' >> $out_file 
    else
	echo $md5sum >> $out_file_failed
    fi
done
)

# gzip the subjob otput file and copy it to $out_pssh2
zip_file="$out_file.gz" 
gzip -c $out_file > $zip_file
cp $zip_file $out_pssh2
if [ -s $out_file_failed ] ; 
then
    cp $out_file_failed $out_pssh2
fi
