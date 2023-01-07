#!/bin/zsh

# query TNS for each of requested months [MM: 01-12] in a given year (YYYY)
# output: header line, folllowed by lines, one line per event, tsv format
#
# qTNSm [-t type] YYYY [START_MONTH [END_MONTH]]]
# ..  -t type where type=unclassified (u), classified [c]
#
# output:
# TNSc_YYYY_MM.tsv (classified)
# TNSu_YYYY_MM.tsv (unclasffied)
#
# usage:
# qTNSm      2021 1      % classified events for Jan, 2021
# qTNSm -t u 2021 1      % unclassified events for Jan, 2021
# qTNSm      2020 1 2    % classified events for Jan & Feb  2020
# qTNSm      2020        % classified events for all of 2020
#
#YETI: FRB option not implemented
#YETI=yet to be implemented
#
# S.R.Kulkarni, 3-January-2021
#=======================================================================
# internal function: gets TNS events for a given month-year
get1month () {
#-----------------------------------------------------------------------

PAGENO=0; N=1
s0="https://www.wis-tns.org/search?&"

printf "%d %d- " $YEAR $MONTH
while [ $N -ne 0 ]
do

  s2="date_start%5Bdate%5D=$YEAR-$MONTH-01&date_end%5Bdate%5D=$YEAR-$MONTH-31&"
  s3="num_page=$NMAX&page=$PAGENO&format=tsv"

  printf "%d:" $PAGENO

  curl -s -o $TFILE "${s0}${s1}${s2}${s3}" -A $USER_AGENT
  sleep 5
  echo "" >> $TFILE        #supplying \n for last record
  N=$(($(wc -l < $TFILE)-1))    #number of records (header not counted)

        #delete header line for subsequent pages
  [ $PAGENO -gt 0 ] && sed -it 1d $TFILE

  cat $TFILE >> $OFILE

  printf "%d " $N


  PAGENO=$((PAGENO+1))

done
return $?
}

#-----------------------------------------------------------------------
#set defaults
#-----------------------------------------------------------------------
    USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/108.0";
    DIRNAME="sneparse/resources/tns-data/";
    NMAX=500; TYPE=c; INVALID=
    FNAME="TNS"
        TFILE="z_$$.tsv"; touch $TFILE ${TFILE}t  #temporary files
    trap "rm $TFILE ${TFILE}t" EXIT          #clean up after exit

#-----------------------------------------------------------------------
#decode options
#-----------------------------------------------------------------------
  while getopts t: OPTION
  do
      case $OPTION in
    t) TYPE=$OPTARG;;        #classified (c) or unclassified (u)
    *) INVALID=1;;
      esac
  done
  [ $INVALID ] && exit -1
  shift $(($OPTIND-1))
    
    #call to database determined by request (classified/unclassified)
    #name of output file, $FNAME, constructed accordingly
  case $TYPE in
    [cC]) s1="unclassified_at=0&classified_sne=1&include_frb=0&"
        FNAME=$FNAME"c";;
    [uU]) s1="unclassified_at=1&classified_sne=0&include_frb=0&"
        FNAME=$FNAME"u";;
    *) echo "quit - invalid choice of type " $TYPE; exit -1;
  esac

#-----------------------------------------------------------------------
# decode & verify: year (YEAR), start-month (MSTART) & end-month (MEND)
#-----------------------------------------------------------------------

    # at minimum, the YEAR has to be specified
    # note: TNS started in YEAR=2016

  [ $# -lt 1 ] && {echo "quit - year not specified"; exit -1}
  [ $1 -lt 2016 ] && {echo "quit - TNS started in 2016"; exit -1}   
  YEAR=$1; shift

            #Decode the months
  case $# in
    0) MSTART=01; MEND=12;;
    1) MSTART=$1; MEND=$1;;
    2) MSTART=$1; MEND=$2;;
    *) echo "quit - parameters exceed pair for month start and end"; exit -1;;
  esac
        #months should be on a scale of 01 to 12 (zero prefix)
  MSTART=$(printf "%02d" $MSTART); MEND=$(printf "%02d" $MEND);    

        #simple sanity checks
  if [ $MSTART -gt $MEND ]; then
    echo "quit - start month $MSTART > end month $MEND"; exit -1
  fi
  if [ $MSTART -gt 12 ] || [ $MSTART -lt 1 ] || [ $MEND -gt 12 ] || [ $MEND -lt 1 ]
  then
    echo "quit - invalid month values $MSTART, $MEND"; exit -1
  fi
 
#-----------------------------------------------------------------------
# Loop through the months
#-----------------------------------------------------------------------

  for MONTH in {$MSTART..$MEND}
  do
            #request month-year in the future?
    YR=$(date "+%Y"); M=$(date "+%m");
    if [ $YEAR -gt $YR ] || ([ $YEAR -eq $YR  ] && [ $MONTH -gt $M ]); then
      echo "quit - unable to access the future"; exit
    fi

    OFILE="${DIRNAME}${FNAME}_${YEAR}_$MONTH.tsv"; :>$OFILE

    get1month

    n=$(sed '/^"ID/d' $OFILE | wc -l)
    print " $OFILE (${n// /} events)"    #elegant way to get rid of blanks in $n

  done
