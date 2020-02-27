#!/bin/bash

#Argument 1, list of blocks
#Well name
file_out="../output/PT/txt/${2}_PT.dat"
fi_out_file='../model/t2/t2.out'

echo "$1" > temp
echo  'ELEM,P,T,SG,SW,X(WAT1),X(WAT2),PCAP,DG,DW'>$file_out
while read line; do
	grep $line $fi_out_file | awk -F" "  'NF==11 {print $1,",",$3,",",$4,",",$5,",",$6,",",$7,",",$8,",",$9,",",$10,",",$11}' >>$file_out
	done<temp

rm -f temp