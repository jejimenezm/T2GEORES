#!/bin/bash

fi_out_file="../model/t2/t2.out"

#Print differents GEN's
grep "GEN[0-9]" $fi_out_file | awk -F" " 'NF==7&&$3~ /[0-9]/ {print $2}'| sort | uniq > dif_gen

#Times
echo "TIME">times_temp

grep "OUTPUT DATA AFTER"  $fi_out_file  | cut -c  117-127>>times_temp

while read line; do

	block=`grep "GEN[0-9]" $fi_out_file | awk -F" " -v var="$line" 'NF==7&&$2==var {print $1}'| sort | uniq`

	file_out_temp="${line}_${block}_evol_mh_temp.dat"

	echo "ELEMENT,SOURCE,INDEX,GENERATION RATE,ENTHALPY,X1,X2" >$file_out_temp

	grep "GEN[0-9]" $fi_out_file | awk -F" " -v var="$line" 'NF==7&&$2==var  {print $1,$2,$3,$4,$5,$6,$7}' OFS=',' >>$file_out_temp

	paste -d , $file_out_temp times_temp >"../output/mh/txt/${line}_${block}_evol_mh.dat"

	rm -f  $file_out_temp

	done<dif_gen


rm -f times_temp dif_gen

