#!/bin/bash
input_fi_file="../model/t2/t2"
input_incon="../model/t2/t2.sav"


initial_eleme=$(grep -hnr "ELEME" $input_fi_file | awk -F: '{print $1}')
incon_line=$(grep -hnr "INCON" $input_fi_file | awk -F: '{print $1}')

if [ -z $incon_line ];
then
	awk "NR<="$initial_eleme"-1" $input_fi_file > new_fi
	echo "INCON">>new_fi
	tail -n +2 $input_incon | head -n -2| awk '{if (NR%2==1) {printf ("%5s%25s\n"),$1,$4} else {print $0}  }'  >> new_fi
	awk "NR>="$initial_eleme"-1" $input_fi_file>>new_fi
else
	awk "NR<="$incon_line"-1" $input_fi_file > new_fi
	echo "INCON">>new_fi
	tail -n +2 $input_incon | head -n -2| awk '{if (NR%2==1) {printf ("%5s%25s\n"),$1,$4} else {print $0}  }' >> new_fi
	awk "NR>="$initial_eleme"-1" $input_fi_file>>new_fi
fi

rm -f $input_fi_file
cat new_fi> $input_fi_file
rm -f new_fi
