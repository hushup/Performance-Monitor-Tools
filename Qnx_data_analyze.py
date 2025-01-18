# -*- coding: utf-8 -*-
"""
Author: Hu Shupeng
Mail: 1158340263@qq.com
公众号:臭小胡
Description:Make a friend and dedicated to friends who do performance optimization.
"""
import csv
import os
import re
import logging
import subprocess
import time
import datetime
import copy
import sys
from openpyxl import Workbook
import xlsxwriter

qnxinfo_log = "qnx_status.log"
gpuinfo_log = "qnx_gpu.log"

#cpu
process_columns = 1
excel_rows = 1
process = {}
#meminfo
meminfo_columns = 0
meminfo_rows = 1
memtype = {}
skip_type = ["VmallocTotal", "Committed_AS"]
#procrank
procrank_columns = 0
procrank_rows = 1
procrank_process = {}
memory_config = 0
memconfig = {}
#gpu
gpu_rows = 1
#disk
disk_columns = 0
disk_rows = 1
disk_type = {}

disk_type['/dev/disk/uda0.3A06'] = [1, 'system', 0, 0, 0] #[index, name_match, Size, Used, Avail]
disk_type['/dev/disk/uda0.5319'] = [2, 'resource', 0, 0, 0]
disk_type['/dev/disk/uda0.732D'] = [3, 'log_data', 0, 0, 0]
disk_type['/dev/disk/uda0.B3CC'] = [4, 'fota', 0, 0, 0]
disk_type['/dev/disk/uda0.1B81'] = [5, 'var', 0, 0, 0]
disk_type['/dev/disk/uda0.6C95'] = [6, 'persist', 0, 0, 0]
disk_type['/dev/disk/uda0.ms.2'] = [7, 'firmware', 0, 0, 0]
disk_type['/dev/disk/uda0.901F'] = [8, 'vendor', 0, 0, 0]

disk_histogram_columns = 12

date_time = "0:0:0"
start_time = '0:0:0'
months = {
"Jan":1,
"Feb":2,
"Mar":3,
"Apr":4,
"May":5,
"June":6,
"July":7,
"Aug":8,
"Sep":9,
"Oct":10,
"Nov":11,
"Dec":12,
}
#创建excel表对象
wb = xlsxwriter.Workbook('Qnx_status.xlsx')
#Summary
ws = wb.add_worksheet('Summary')
#CPU
ws_cpu = wb.add_worksheet('CPU')
#Meminfo
ws_meminfo = wb.add_worksheet('Meminfo')
#procrank
ws_process_mem = wb.add_worksheet('App')
#df -h
ws_disk = wb.add_worksheet('Disk')
#Gpu
ws_gpu = wb.add_worksheet('Gpu')

def get_memory_config(segment):
	for index in range(3, len(segment)):
		line_context = segment[index].split()
		mem_name = line_context[0]
		memconfig[mem_name] = float(line_context[1])
	#print(memconfig)

def check_line_flag(line, arg):
    check_compile = re.compile(r'%s' %arg)
    result = check_compile.findall(line)
    if result:
        return True
    else:
        return False

def get_time(line):
	time_compile = re.compile(r'#*Start dump (.*?) GMT*')
	time = time_compile.findall(line)
	if time:
		return time[0]
	else:
		return False

def create_cpu_chart():
	#CPU 表头信息
	ws_cpu.write(0, 0, 'Time')
	ws_cpu.write(0, 1, 'Total')
	
	chart_cpu = wb.add_chart({'type':'line'})
	chart_cpu.set_title({'name':'CPU使用情况(%)'})
	for pro_key in process:
			if pro_key == "[idle]":
				continue
			process_row_max = excel_rows -1
			process_index = int(process[pro_key][0])
			chart_cpu.add_series({
			'name':['CPU', 0, process_index],
			'categories':['CPU', 1, 0, process_row_max, 0],
			'values': ['CPU', 1, process_index, process_row_max, process_index],
			#'line': {'color': 'blue'},#b--blue      c--cyan(青色)g--green     k--black m--magenta(紫红色)      r--red            w--white          y--yellow
	})
	chart_cpu.height = 500
	chart_cpu.width = 1000
	ws_cpu.insert_chart('B10', chart_cpu)
	
def create_process_mem_chart():
	#CPU 表头信息
	ws_process_mem.write(0, 0, 'Time')
	ws_process_mem.write(0, 1, 'Total')
	
	chart_process_chart = wb.add_chart({'type':'line'})
	chart_process_chart.set_title({'name':'应用内存(K)'})
	for pro_key in process:
			if pro_key == "[idle]":
				continue
			process_row_max = excel_rows -1
			process_index = int(process[pro_key][0])
			chart_process_chart.add_series({
			'name':['App', 0, process_index],
			'categories':['App', 1, 0, process_row_max, 0],
			'values': ['App', 1, process_index, process_row_max, process_index],
			#'line': {'color': 'blue'},#b--blue      c--cyan(青色)g--green     k--black m--magenta(紫红色)      r--red            w--white          y--yellow
	})
	chart_process_chart.height = 500
	chart_process_chart.width = 1000
	ws_process_mem.insert_chart('B10', chart_process_chart)

def create_meminfo_chart():
	#CPU 表头信息
	ws_meminfo.write(0, 0, 'Time')
	
	chart_meminfo = wb.add_chart({'type':'line'})
	chart_meminfo.set_title({'name':'QNX总内存(K)'})
	for pro_key in memtype:
			if pro_key in skip_type:
				continue
			meminfo_row_max = meminfo_rows -1
			meminfo_index = int(memtype[pro_key][0])
			chart_meminfo.add_series({
			'name':['Meminfo', 0, meminfo_index],
			'categories':['Meminfo', 1, 0, meminfo_row_max, 0],
			'values': ['Meminfo', 1, meminfo_index, meminfo_row_max, meminfo_index],
			#'line': {'color': 'green'},#b--blue      c--cyan(青色)g--green     k--black m--magenta(紫红色)      r--red            w--white          y--yellow
	})
	chart_meminfo.height = 500
	chart_meminfo.width = 1000
	ws_meminfo.insert_chart('B10', chart_meminfo)
	
def create_procrank_chart():
	#CPU 表头信息
	ws_procrank.write(0, 0, 'Time')
	
	chart_procrank = wb.add_chart({'type':'line'})
	chart_procrank.set_title({'name':'应用内存(K)'})
	for pro_key in procrank_process:
			procrank_row_max = procrank_rows -1
			procrank_index = int(procrank_process[pro_key][0])
			chart_procrank.add_series({
			'name':['App', 0, procrank_index],
			'categories':['App', 1, 0, procrank_row_max, 0],
			'values': ['App', 1, procrank_index, procrank_row_max, procrank_index],
			#'line': {'color': 'yellow'},#b--blue      c--cyan(青色)g--green     k--black m--magenta(紫红色)      r--red            w--white          y--yellow
	})
	
	chart_procrank.height = 500
	chart_procrank.width = 1000
	ws_procrank.insert_chart('B10', chart_procrank)
	
def create_gpu_chart():
	chart_gpu = wb.add_chart({'type':'line'})
	chart_gpu.set_title({'name':'GPU使用情况(%)'})
	#print("#####",gpu_rows)
	chart_gpu.add_series({
		'name':['Gpu', 0, 1],
		'categories':['Gpu', 1, 0, gpu_rows -1 , 0],
		'values': ['Gpu', 1, 1, gpu_rows -1 , 1],
		#'line': {'color': 'yellow'},#b--blue      c--cyan(青色)g--green     k--black m--magenta(紫红色)      r--red            w--white          y--yellow
	})
	
	chart_gpu.height = 500
	chart_gpu.width = 1000
	ws_gpu.insert_chart('D2', chart_gpu)

def create_disk_chart():
	#CPU 表头信息
	ws_disk.write(0, 0, 'Time')
	
	chart_disk = wb.add_chart({'type':'line'})
	chart_disk.set_title({'name':'磁盘使用情况(K)'})
	for pro_key in disk_type:
			#创建磁盘excel表头
			ws_disk.write(0, disk_type[pro_key][0], disk_type[pro_key][1])
			
			disk_row_max = disk_rows -1
			disk_index = int(disk_type[pro_key][0])
			chart_disk.add_series({
			'name':['Disk', 0, disk_index],
			'categories':['Disk', 1, 0, disk_row_max, 0],
			'values': ['Disk', 1, disk_index, disk_row_max, disk_index],
			#'line': {'color': 'yellow'},#b--blue      c--cyan(青色)g--green     k--black m--magenta(紫红色)      r--red            w--white          y--yellow
	})
	
	chart_disk.height = 500
	chart_disk.width = 1000
	ws_disk.insert_chart('B10', chart_disk)

def create_disk_histogram_chart():
	#Disk 表头信息
	ws_disk.write(0, disk_histogram_columns, 'Name')
	ws_disk.write(0, disk_histogram_columns + 1, 'Total')
	ws_disk.write(0, disk_histogram_columns + 2, 'Used')
	
	#填写表数据
	for pro_key in disk_type:
		ws_disk.write(disk_type[pro_key][0], disk_histogram_columns, disk_type[pro_key][1])#Name
		ws_disk.write(disk_type[pro_key][0], disk_histogram_columns + 1, disk_type[pro_key][2])#Total
		ws_disk.write(disk_type[pro_key][0], disk_histogram_columns + 2, disk_type[pro_key][3])#Used
	
	#生成柱状图
	chart_disk_histogram = wb.add_chart({'type':'column'})
	chart_disk_histogram.set_title({'name':'磁盘占用比(K)'})
	chart_disk_histogram.add_series({
		'name':['Disk', 0, disk_histogram_columns + 1],
		'categories':['Disk', 1, disk_histogram_columns, 9, disk_histogram_columns],
		'values': ['Disk', 1, disk_histogram_columns + 1, 9, disk_histogram_columns + 1],
	})
	chart_disk_histogram.add_series({
		'name':['Disk', 0, disk_histogram_columns + 2],
		'categories':['Disk', 1, disk_histogram_columns, 9, disk_histogram_columns],
		'values': ['Disk', 1, disk_histogram_columns + 2, 9, disk_histogram_columns + 2],
	})
	
	chart_disk_histogram.height = 500
	chart_disk_histogram.width = 500
	ws_disk.insert_chart('R10', chart_disk_histogram)
	
def create_memory_histogram_chart():
	#Disk 表头信息
	meminfo_histogram_columns = meminfo_columns + 2
	ws_meminfo.write(0, meminfo_histogram_columns, 'Name')
	ws_meminfo.write(0, meminfo_histogram_columns + 1, 'Total')
	ws_meminfo.write(0, meminfo_histogram_columns + 2, 'MaxUsed')
	
	#填写表数据
	memory_type_num = 0
	for pro_key in memtype: #[index, Used, Total, MaxUsed]
		ws_meminfo.write(memtype[pro_key][0], meminfo_histogram_columns, pro_key)#Name
		ws_meminfo.write(memtype[pro_key][0], meminfo_histogram_columns + 1, memtype[pro_key][2])#Total
		ws_meminfo.write(memtype[pro_key][0], meminfo_histogram_columns + 2, memtype[pro_key][3])#MaxUsed
		memory_type_num = memory_type_num + 1
	
	#生成柱状图
	chart_meminfo_histogram = wb.add_chart({'type':'column'})
	chart_meminfo_histogram.set_title({'name':'内存使用峰值(K)'})
	chart_meminfo_histogram.add_series({
		'name':['Meminfo', 0, meminfo_histogram_columns + 1],
		'categories':['Meminfo', 1, meminfo_histogram_columns, memory_type_num, meminfo_histogram_columns],
		'values': ['Meminfo', 1, meminfo_histogram_columns + 1, memory_type_num, meminfo_histogram_columns + 1],
	})
	chart_meminfo_histogram.add_series({
		'name':['Meminfo', 0, meminfo_histogram_columns + 2],
		'categories':['Meminfo', 1, meminfo_histogram_columns, memory_type_num, meminfo_histogram_columns],
		'values': ['Meminfo', 1, meminfo_histogram_columns + 2, memory_type_num, meminfo_histogram_columns + 2],
	})
	
	chart_meminfo_histogram.height = 500
	chart_meminfo_histogram.width = 500
	ws_meminfo.insert_chart('R10', chart_meminfo_histogram)

def top_analyze(segment):
	#print(segment)
	#Clear process cpu data
	global process_columns
	global excel_rows
	global memconfig
	for pro_key in process:
		process[pro_key][1] = 0
		process[pro_key][2] = 0
	#Set date time 
	#ws_cpu.write(0, 0, 'Time')
	ws_cpu.write(excel_rows, 0, date_time)
	#Get cpu total usage data
	#print("#######", segment)
	total_cpu = float(segment[2].split()[2].strip('%'))

	total_mem = memconfig["sysram"] - float(segment[11].split()[3].strip('M'))*1024
	#print("#####", memconfig["sysram"], float(segment[11].split()[3].strip('M'))*1024, total_mem)
	process["total"] = [1, float(total_cpu), total_mem] #[index , total_cpu, total_mem]

	ws_cpu.write(excel_rows, 1, process["total"][1])
	
	#process_mem write excel_rows
	ws_process_mem.write(excel_rows, 0, date_time)
	ws_process_mem.write(excel_rows, 1, process["total"][2])
	
def hogs_analyze(segment):
	#print(segment)
	#Clear process cpu data
	global process_columns
	global excel_rows
	for index in range(2, len(segment)):
		line_context = segment[index].split()
		if len(line_context) < 2:
			continue
		#print(line_context)
		process_name = line_context[1]

		if process_name in process:
			process[process_name][1] = float(process[process_name][1]) + float(line_context[3].strip('%')) #Cpu data
			process[process_name][2] = float(process[process_name][2]) + float(line_context[5].strip('k')) #Memory data
			ws_cpu.write(excel_rows, process[process_name][0], process[process_name][1]) #Write cpu sheet
			ws_process_mem.write(excel_rows, process[process_name][0], process[process_name][2]) #Write process_mem sheet
		else :
			#process[process_name] = {"process_name": [process_columns, cpu_value, memory_value]}
			process_columns = process_columns + 1
			process[process_name] = [process_columns, float(line_context[3].strip('%')), float(line_context[5].strip('k'))]
			#CPU创建表头
			ws_cpu.write(0, process[process_name][0], process_name)
			ws_cpu.write(excel_rows, process[process_name][0], process[process_name][1])
			#process_mem创建表头
			ws_process_mem.write(0, process[process_name][0], process_name)
			ws_process_mem.write(excel_rows, process[process_name][0], process[process_name][2])
	#print(process)
	excel_rows = excel_rows + 1

def meminfo_analyze(segment):
	global meminfo_columns
	global meminfo_rows
	#Set date time 
	ws_meminfo.write(meminfo_rows, 0, date_time)
	
	for index in range(3, len(segment)):
		line_context = segment[index].split()
		mem_name = line_context[0]
		if mem_name in memtype:
			memtype[mem_name][1] = float(line_context[2])
			if float(line_context[2]) > memtype[mem_name][3]:
				memtype[mem_name][3] = float(line_context[2])
			ws_meminfo.write(meminfo_rows, memtype[mem_name][0], memtype[mem_name][1])
		else:
			meminfo_columns = meminfo_columns + 1
			memtype[mem_name] = [meminfo_columns, float(line_context[2]), float(line_context[1]), 0] #[index, Used, Total, MaxUsed]
			#创建表头
			ws_meminfo.write(0, memtype[mem_name][0], mem_name)
			ws_meminfo.write(meminfo_rows, memtype[mem_name][0], memtype[mem_name][1])
	#print (memtype)
	meminfo_rows = meminfo_rows + 1

def parse_data_in_kb(unkown_data):
	if 'G' in unkown_data:
		return float(unkown_data.strip('G'))*1024*1024
	elif 'M' in unkown_data:
		return float(unkown_data.strip('M'))*1024
	else:
		return float(unkown_data.strip('K'))
	
def get_disk_data(line):
	disk_data = [0, 0, 0]
	#print("#################get_disk_data")
	#print(line)
	disk_data[0] = parse_data_in_kb(line[1])
	disk_data[1] = parse_data_in_kb(line[2])
	disk_data[2] = parse_data_in_kb(line[3])
	return disk_data
	
def disk_analyze(segment):
	global disk_columns
	global disk_rows
	#Set date time 
	ws_disk.write(disk_rows, 0, date_time)
	
	for index in range(1, len(segment)):
		line_context = segment[index].split()
		if line_context[0] in disk_type:
			data = get_disk_data(line_context)
			disk_type[line_context[0]] = [disk_type[line_context[0]][0], disk_type[line_context[0]][1], data[0], data[1], data[2]]
			ws_disk.write(disk_rows, disk_type[line_context[0]][0], disk_type[line_context[0]][3])
	#print(disk_type)
	disk_rows = disk_rows + 1

def segments_analyze(segments):
	global memory_config
	for segment in segments:
		if check_line_flag(segment[0], "Start top") == True:
			top_analyze(segment)
		if check_line_flag(segment[0], "Start hogs") == True:
			hogs_analyze(segment)
		if check_line_flag(segment[0], "Start showmem") == True:
			if memory_config == 0:
				memory_config = 1
				get_memory_config(segment)
			meminfo_analyze(segment)
		if check_line_flag(segment[0], "Start df") == True:
			disk_analyze(segment)
		else :
			print("恭喜发财")
def write_summary():
	ws.write(0, 0, "测试开始时间")
	ws.write(0, 1, "测试结束时间")
	ws.write(1, 0, start_time)
	ws.write(1, 1, date_time)
def time2sec(time, offset):
	return months[time[offset]]*30*24*60*60 + int(time[offset+1])*24*60*60 + int(time[offset+2].split(':')[0])*60*60 + int(time[offset+2].split(':')[1])*60 + int(time[offset+2].split(':')[2])
def data_time_compare(time_start, time_end):
	stime2sec =  time2sec(time_start, 1)
	etime2sec =  time2sec(time_end, 0)
	return etime2sec - stime2sec

def get_gpu_data():
	global gpu_rows
	ws_gpu.write(0, 0, "Time")
	ws_gpu.write(0, 1, "Percentage")
	with open(gpuinfo_log) as gpuinfo_fd:
		for line_contents in gpuinfo_fd:
			line_split = line_contents.split()
			time = (line_split[0] + ' ' + line_split[1] + ' ' + line_split[2]).split('.')[0]
			percentage = line_split[23].strip('%')
			#print("####", time, percentage, date_time)
			ret = data_time_compare(start_time.split(), time.split())
			if ret < 0:
				continue
			ret = data_time_compare(date_time.split(), time.split())
			if ret > 0:
				break
			ws_gpu.write(gpu_rows, 0, time)
			ws_gpu.write(gpu_rows, 1, float(percentage))
			gpu_rows = gpu_rows + 1

if __name__ == "__main__":
	segments = []
	segment = []
	get_start_time = 0
	
	now_date = datetime.datetime.now()
	if now_date < datetime.datetime(2022, 9, 22, 0, 0):
		print("白嫖结束")
		exit()
	if now_date > datetime.datetime(2026, 2, 22, 0, 0):
		print("白嫖结束")
		exit()
	
	with open(qnxinfo_log) as sysinfo_fd:
		# 1.分段分割
		for line_contents in sysinfo_fd:
			if check_line_flag(line_contents, "Start dump") == True :
				date_time = get_time(line_contents)
				if get_start_time == 0:
					get_start_time = 1
					#print(date_time)
					start_time = date_time
					segment.clear()
				continue	
			elif check_line_flag(line_contents, "End dump") == True :
				segments_analyze(segments)
				segments.clear()
				#print(segments)
			else :
				if check_line_flag(line_contents, "End ") == True :
					copy_segment = copy.copy(segment)
					segments.append(copy_segment)
					segment.clear()
				else :
					segment.append(line_contents)
	get_gpu_data()
	write_summary()
	create_cpu_chart()
	create_meminfo_chart()
	create_process_mem_chart()
	create_gpu_chart()
	create_disk_chart()
	create_disk_histogram_chart()
	create_memory_histogram_chart()
	wb.close()