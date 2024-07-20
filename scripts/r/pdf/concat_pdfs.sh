pdftk A="$1" B="$2" cat $PAGES_TO_CONCAT output concatenated_"$(date +%Y%m%d_%H%M%S)".pdf
