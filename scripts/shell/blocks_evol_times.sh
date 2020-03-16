#!/bin/bash

#!/bin/bash

#Argument 1, list of blocks
#Well name

file_out="../output/PT/evol/${2}_PT_"
fi_out_file="../model/t2/t2.out"


#Times
echo "TIME">times_temp
grep "OUTPUT DATA AFTER"  $fi_out_file  | cut -c  117-127>>times_temp

echo "$1" | head -n -1 > temp

while read line; do
	layer=${line:0:1}
	echo  'ELEM,P,T,SG,SW,X(WAT1),X(WAT2),PCAP,DG,DW'>"${file_out}${layer}temp.dat"
	grep $line $fi_out_file | awk -F" "  'NF==11 {print $1,",",$3,",",$4,",",$5,",",$6,",",$7,",",$8,",",$9,",",$10,",",$11}'>>"${file_out}${layer}temp.dat"
	paste -d , "${file_out}${layer}temp.dat" times_temp >"${file_out}${layer}_evol.dat"
	rm -f  "${file_out}${layer}temp.dat"
	done<temp

rm -f  temp, times_temp
