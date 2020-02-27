#!/bin/bash
filename='../model/t2/FOFT'
fi_out_file='../model/t2/test/t2.out'

temp_file="t0"

while read line; do
	grep $line $fi_out_file | awk -F" "  'NF==11 {print $1,$3,$4,$5,$6,$7,$8,$9,$10,$11}'
done<$filename


#rm -f t0