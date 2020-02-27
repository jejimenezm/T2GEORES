#!/bin/bash
input_fi_file="fi"
input_incon="$1"

initial_incon=$(grep -n INCON "$input_fi_file" | cut -c -6)
final_incon=$(grep -n FOFT "$input_fi_file"| cut -c -6)

awk "NR<="$initial_incon"" $input_fi_file > new_fi
#cat "$input_incon"| tail -n +2 | tail -n -1 >> new_fi

#cat "$input_incon">> new_fi
#awk '{if (NR%2==1) {printf ("%5s%5s%5s\n"),$1,$2,$3} else {print $0}  }' $input_incon >> new_fi
#awk '{if (NR%2==1) {print $1} else {print $0}  }' $input_incon >> new_fi
awk '{if (NR%2==1) {printf ("%5s%25s\n"),$1,$4} else {print $0}  }' $input_incon >> new_fi
#awk '{if (NR%2==1) {printf ("%5s\n"),$1} else {print $0}  }' $input_incon >> new_fi
awk "NR>="$final_incon"-1" $input_fi_file>>new_fi

rm -f $input_fi_file
cat new_fi> $input_fi_file
rm -f new_fi
