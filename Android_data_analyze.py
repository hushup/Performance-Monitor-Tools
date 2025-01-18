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

sysinfo_log = "sysinfo-android.log"
file_cfg = "Custom.cfg"

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
app_memory_analyze = 1
#disk
disk_columns = 0
disk_rows = 1
disk_type = {}

disk_type['/dev/block/dm-0'] = [1, 'system', 0, 0, 0] #[index, name_match, Size, Used, Avail]
disk_type['/dev/block/dm-1'] = [2, 'vendor', 0, 0, 0]
disk_type['/dev/block/userdata'] = [3, 'userdata', 0, 0, 0]
disk_type['/dev/block/persist'] = [4, 'persist', 0, 0, 0]
disk_type['/dev/block/map'] = [5, 'map', 0, 0, 0]
disk_type['/dev/block/config'] = [6, 'configureg', 0, 0, 0]
disk_type['/dev/block/log'] = [7, 'log', 0, 0, 0]
disk_type['/dev/block/modem'] = [8, 'modem', 0, 0, 0]
disk_type['/dev/block/bluetooth'] = [9, 'bluetooth', 0, 0, 0]
disk_histogram_columns = 12

date_time = "0:0:0"
start_time = '0:0:0'

#创建excel表对象
wb = xlsxwriter.Workbook('Android_status.xlsx')
#Summary
ws = wb.add_worksheet('Summary')
#CPU
ws_cpu = wb.add_worksheet('CPU')
#Meminfo
ws_meminfo = wb.add_worksheet('Meminfo')
#procrank
ws_procrank = wb.add_worksheet('App')
#df -h
ws_disk = wb.add_worksheet('Disk')

def get_cfg():
	global app_memory_analyze
	with open(file_cfg) as cfg_fd:
		for line_contents in cfg_fd:
			if check_line_flag(line_contents, "app_memory_analyze") == True :
				app_memory_analyze = int(line_contents.split('=')[1])

def check_line_flag(line, arg):
    check_compile = re.compile(r'%s' %arg)
    result = check_compile.findall(line)
    if result:
        return True
    else:
        return False

def get_time(line):
	time_compile = re.compile(r'#*Start dump (.*?) CST*')
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
	chart_cpu.set_title({'name':'CPU使用情况'})
	for pro_key in process:
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

def create_meminfo_chart():
	#CPU 表头信息
	ws_meminfo.write(0, 0, 'Time')
	
	chart_meminfo = wb.add_chart({'type':'line'})
	chart_meminfo.set_title({'name':'内存总览(K)'})
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
	
def top_analyze(segment):
	#print(segment)
	#Clear process cpu data
	global process_columns
	global excel_rows
	for pro_key in process:
		process[pro_key][1] = 0
	#Set date time 
	#ws_cpu.write(0, 0, 'Time')
	ws_cpu.write(excel_rows, 0, date_time)
	#Get cpu total usage data
	total = 800.0 - float(segment[4].split()[4].split('%')[0])
	process["total"] = [1, float(total)]
	#ws_cpu.write(0, 1, 'Total')
	ws_cpu.write(excel_rows, 1, process["total"][1])
	#Start top------------------------------------
	#Tasks: 375 total,   2 running, 371 sleeping,   0 stopped,   2 zombie
	#Mem: 11353224K total, 10594732K used,   758492K free,  94642176 buffers
	#Swap:  4194300K total,   218508K used,  3975792K free,   873404K cached
	#   PID USER         PR  NI VIRT  RES  SHR S[%CPU] %MEM     TIME+ ARGS
	#   4316 u0_a146      20   0  15G  93M  46M S  110   0.8 199:24.15 com.yfve.upnpservice
	for index in range(6, len(segment)):
		line_context = segment[index].split()
		#print(line_context)
		process_name = line_context[11]
		if len(line_context) > 12 :
			process_name = process_name + line_context[12]
		if float(line_context[8]) < 2: #忽略cpu占用低于2%的，防止excel表格超出范文
			continue
		if process_name in process:
			process[process_name][1] = float(process[process_name][1]) + float(line_context[8])
			ws_cpu.write(excel_rows, process[process_name][0], process[process_name][1])
		else :
			#process[process_name] = {"process_name": [process_columns, cpu_value]}
			process_columns = process_columns + 1
			process[process_name] = [process_columns, float(line_context[8])]
			#创建表头
			ws_cpu.write(0, process[process_name][0], process_name)
			ws_cpu.write(excel_rows, process[process_name][0], process[process_name][1])
	#print(process)
	excel_rows = excel_rows + 1

def meminfo_analyze(segment):
	global meminfo_columns
	global meminfo_rows
	#Set date time 
	ws_meminfo.write(meminfo_rows, 0, date_time)
	
	for index in range(1, len(segment)):
		line_context = segment[index].split()
		mem_name = line_context[0].strip(':')
		if mem_name in memtype:
			memtype[mem_name][1] = float(line_context[1])
			ws_meminfo.write(meminfo_rows, memtype[mem_name][0], memtype[mem_name][1])
		else:
			meminfo_columns = meminfo_columns + 1
			memtype[mem_name] = [meminfo_columns, float(line_context[1])]
			#创建表头
			ws_meminfo.write(0, memtype[mem_name][0], mem_name)
			ws_meminfo.write(meminfo_rows, memtype[mem_name][0], memtype[mem_name][1])
	#print (memtype)
	meminfo_rows = meminfo_rows + 1
	
def procrank_analyze(segment):
	global procrank_columns
	global procrank_rows
	#Set date time 
	ws_procrank.write(procrank_rows, 0, date_time)
	
	for index in range(2, len(segment)):
		line_context = segment[index].split()
		if len(line_context) != 10:
			continue
		procrank_process_name = line_context[9]
		if procrank_process_name in procrank_process:
			procrank_process[procrank_process_name][1] = float(line_context[3].strip('K')) + float(line_context[6].strip('K'))
			ws_procrank.write(procrank_rows, procrank_process[procrank_process_name][0], procrank_process[procrank_process_name][1])
		else:
			procrank_columns = procrank_columns + 1
			procrank_process[procrank_process_name] = [procrank_columns, float(line_context[3].strip('K')) + float(line_context[6].strip('K'))]
			#创建表头
			ws_procrank.write(0, procrank_process[procrank_process_name][0], procrank_process_name)
			ws_procrank.write(procrank_rows, procrank_process[procrank_process_name][0], procrank_process[procrank_process_name][1])
	#print (procrank_process)
	procrank_rows = procrank_rows + 1

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
	for segment in segments:
		if check_line_flag(segment[0], "Start top") == True:
			top_analyze(segment)
		if check_line_flag(segment[0], "Start meminfo") == True:
			meminfo_analyze(segment)
		if check_line_flag(segment[0], "Start procrank") == True:
			procrank_analyze(segment)
		if check_line_flag(segment[0], "Start df") == True:
			disk_analyze(segment)
		else :
			print("恭喜发财")
def write_summary():
	ws.write(0, 0, "测试开始时间")
	ws.write(0, 1, "测试结束时间")
	ws.write(1, 0, start_time)
	ws.write(1, 1, date_time)


if __name__ == "__main__":
	#print("Fuck you code")
	segments = []
	segment = []
	get_start_time = 0
	
	get_cfg()
	now_date = datetime.datetime.now()
	if now_date < datetime.datetime(2022, 9, 22, 0, 0):
		print("白嫖结束")
		exit()
	if now_date > datetime.datetime(2026, 2, 22, 0, 0):
		print("白嫖结束")
		exit()
	
	with open(sysinfo_log) as sysinfo_fd:
		# 1.分段分割
		for line_contents in sysinfo_fd:
			if check_line_flag(line_contents, "Start dump") == True :
				date_time = get_time(line_contents)
				if get_start_time == 0:
					get_start_time = 1
					#print(date_time)
					start_time = date_time
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
	write_summary()
	create_cpu_chart()
	create_meminfo_chart()

	if app_memory_analyze == 1:
		create_procrank_chart()
	create_disk_chart()
	create_disk_histogram_chart()
	wb.close()