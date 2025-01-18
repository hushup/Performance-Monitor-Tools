#!/system/bin/sh

FILE_PATH=/fota

FILE_PREFIX_SYSINFOLOG=sysinfo
FILE_SYSINFOLOG=$FILE_PATH/$FILE_PREFIX_SYSINFOLOG-android.log 

if [ ! -d $FILE_PATH ]
then
mkdir -p $FILE_PATH
fi
rm -rf $FILE_PATH/$FILE_PREFIX_SYSINFOLOG-*.log
logger_top()
{
	echo "Start top------------------------------------" >> $FILE_SYSINFOLOG
	top -m 30 -b -n 1 >> $FILE_SYSINFOLOG
	echo "End  top-------------------------------------" >> $FILE_SYSINFOLOG
}

logger_free()
{
	echo "Dump free-----------------"$(date)"-------------------" >> $FILE_SYSINFOLOG
	free >> $FILE_SYSINFOLOG
}

logger_buddyinfo()
{
	echo "Dump buddyinfo-----------------"$(date)"-------------------" >> $FILE_SYSINFOLOG
	cat /proc/buddyinfo >> $FILE_SYSINFOLOG
}

logger_procrank()
{
	echo "Start procrank----------------------------------" >> $FILE_SYSINFOLOG
	procrank >> $FILE_SYSINFOLOG
	echo "End procrank------------------------------------" >> $FILE_SYSINFOLOG
}

logger_dumpsys_meminfo()
{
	echo "Dump meminfo-------------------"$(date)"-------------------" >> $FILE_SYSINFOLOG
	dumpsys meminfo >> $FILE_SYSINFOLOG
}

logger_meminfo()
{
	echo "Start meminfo----------------------------------" >> $FILE_SYSINFOLOG
	cat /proc/meminfo >> $FILE_SYSINFOLOG
	echo "End meminfo------------------------------------" >> $FILE_SYSINFOLOG
}

logger_zoneinfo()
{
	echo "Start zoneinfo----------------------------------" >> $FILE_SYSINFOLOG
	cat /proc/zoneinfo >> $FILE_SYSINFOLOG
	echo "End zoneinfo----------------------------------" >> $FILE_SYSINFOLOG
}

logger_memtrigger()
{
	echo "Start mem trigger-------------------"$(date)"-------------------" > /dev/kmsg
	echo m >/proc/sysrq-trigger
	echo "End mem trigger-------------------"$(date)"-------------------" > /dev/kmsg
}

logger_df()
{
	echo "Start df----------------------------------" >> $FILE_SYSINFOLOG
	df -h >> $FILE_SYSINFOLOG
	echo "End df----------------------------------" >> $FILE_SYSINFOLOG
}

while (( 1 ))
do
	echo "#############################Start dump "$(date)"#############################" >> $FILE_SYSINFOLOG
	#vmstat
	#uptime
	#logger_free
	#logger_meminfo
	#logger_zoneinfo
	#logger_procrank
	#logger_buddyinfo
	logger_top
	logger_meminfo
	logger_zoneinfo
	logger_procrank
	logger_df
	
	#logger_memtrigger
	echo "#############################End dump "$(date)"##############################" >> $FILE_SYSINFOLOG
	#sleep 1s 
done

