#!/bin/bash
input_fi_file="../model/t2/t2"
input_gener_file="../model/t2/sources/GENER_SOURCES"


sed  '/GEN[0-9]/d' $input_fi_file > temp1_t2

initial_gener=$(grep -hnr "GENER" temp1_t2 | awk -F: '{print $1}')

awk "NR<="$initial_gener"" temp1_t2 > temp_t2
cat $input_gener_file >> temp_t2
awk "NR>"$initial_gener"" temp1_t2 >>temp_t2

rm -f $input_fi_file
cat temp_t2 > $input_fi_file
rm -f temp_t2 temp1_t2