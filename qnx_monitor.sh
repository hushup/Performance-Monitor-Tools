rm /fota/qnx_status.log
while true
do
	echo "#############################Start dump "$(date)"#############################" >> /fota/qnx_status.log

	echo "Start showmem------------------------------------" >> /fota/qnx_status.log
	showmem -s >> /fota/qnx_status.log
	echo "End showmem------------------------------------" >> /fota/qnx_status.log
	
	echo "Start top------------------------------------" >> /fota/qnx_status.log
	top -i 1 >> /fota/qnx_status.log
	echo "End top------------------------------------" >> /fota/qnx_status.log
	sleep 1
	
	echo "Start hogs------------------------------------" >> /fota/qnx_status.log
	hogs -i 1 >> /fota/qnx_status.log
	echo "End hogs------------------------------------" >> /fota/qnx_status.log
	
	sleep 1
	
	echo "Start df------------------------------------" >> /fota/qnx_status.log
	df -h >> /fota/qnx_status.log
	echo "End df------------------------------------" >> /fota/qnx_status.log
	echo "#############################End dump "$(date)"##############################" >> /fota/qnx_status.log
	
done
