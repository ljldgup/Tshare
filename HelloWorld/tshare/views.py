from django.shortcuts import render
from . import models as tmd
from . import dbtools
from datetime import datetime
import time
from django.http import JsonResponse,HttpResponse,HttpResponseRedirect
# Create your views here.

dbrefreshed = False

#html response
def trade_report(request):
	global dbrefreshed
	if dbrefreshed == False:
		dbtools.refresh_k_data('k_bfq',)
		dbrefreshed = True
	note = tmd.Note.objects.filter()
	data = {}
	try:
		st_date = request.GET['st_date']
		ed_date = request.GET['ed_date']
		r_name = request.GET['r_name']
		data['st_date'] = st_date
		data['ed_date'] = ed_date
		data['r_name'] = r_name

	except Exception as e:
		print(e)
	data['note'] = note
	#保存页面数据

	return render(request, 'tshare/trade_report.html',data)
	
def trade_detail(request,r_code):

	#store_k_data to tmp table
	dbtools.storekdata(r_code)
	ori_data = tmd.OriginalTradeData.objects.filter(code = r_code)
	r_name = ori_data[0].name
	k_data = tmd.K_days.objects.filter(code = r_code)
	note = tmd.Note.objects.filter(t_name = r_name)
	note = note.filter(t_type = "个股操作")
	try:
		st_date = request.GET['st_date']
		if st_date != "":
			st_date_dtm = datetime.strptime(st_date, "%Y-%m-%d")
			ori_data = ori_data.filter(date__gte = st_date_dtm)
	except Exception as e:
		print(e)
		
	try:
		ed_date = request.GET['ed_date']
		if ed_date != "":
			ed_date_dtm = datetime.strptime(ed_date, "%Y-%m-%d") 
			ori_data = ori_data.filter(date__lte = ed_date_dtm)
	except Exception as e:
		print(e)
	note = note.order_by('-t_date','-t_stamp')
	data = {}
	data['ori_data'] = ori_data;
	data['r_code'] = r_code
	data['k_data'] = k_data
	data['r_name'] = r_name
	data['note'] = note
	return render(request, 'tshare/trade_detail.html',data)

def all_note(request):
	data = {}
	
	try:
		st_date = request.GET['st_date']
		ed_date = request.GET['ed_date']
		data['st_date'] = st_date
		data['ed_date'] = ed_date
	except Exception as e:
		print(e)
		
	return render(request, 'tshare/all_note.html',data)
	
def note_editor(request):
	data = {}
	try:
		r_stamp = request.GET['r_stamp']
		r_note = tmd.Note.objects.get(t_stamp = r_stamp)
		data['r_name'] = r_note.t_name
		data['r_type'] = r_note.t_type
		data['r_content'] = r_note.t_content
		data['r_date'] = r_note.t_date
		data['r_stamp'] = r_stamp
	except Exception as e:
		print(e)
		
	return render(request, 'tshare/note_editor.html',data)

def trade_statistics(request):
	data = {}
	try:
		st_date = request.GET['st_date']
		ed_date = request.GET['ed_date']
		data['st_date'] = st_date
		data['ed_date'] = ed_date

	except Exception as e:
		print(e)
	return render(request, 'tshare/trade_statistics.html',data)
	

def add_note(request):
	r_date = request.POST['r_date']
	r_name = request.POST['r_name']
	r_type = request.POST['r_type']
	r_url = request.POST['r_url']
	r_content = request.POST['r_content']
	
	try:
		#修改
		r_stamp = request.POST['r_stamp']
		r_note = tmd.Note.objects.filter(t_stamp = r_stamp)
		if(len(r_note) == 1):
			r_note.update(t_name = r_name)
			r_note.update(t_type = r_type)
			r_note.update(t_date = r_date)
			r_note.update(t_content = r_content)
		else:
			r_stamp = time.time()
			tmd.Note.objects.create(t_stamp = str(r_stamp), t_date = r_date, t_name = r_name, t_type = r_type, t_content = r_content)
			return HttpResponseRedirect(r_url.split('?')[0] + '?r_stamp=' + str(r_stamp))
	except Exception as e:
			print(e)
			r_stamp = time.time()
			tmd.Note.objects.create(t_stamp = str(r_stamp), t_date = r_date, t_name = r_name, t_type = r_type, t_content = r_content)
			if 'note_editor' in r_url:
				return HttpResponseRedirect(r_url.split('?')[0] + '?r_stamp=' + str(r_stamp))
			else:
				return HttpResponseRedirect(r_url)
	return HttpResponseRedirect(r_url)

#json data response
def note_json(request):
	note_list = []
	
	try:
		#单条数据
		r_stamp = request.GET['r_stamp']
		if r_stamp != "":
			try:
				i = tmd.Note.objects.get(t_stamp = r_stamp)
				note_list.append([i.t_stamp, i.t_name, i.t_type,  i.t_date, i.t_content])
			except Exception as e:
				print(e)
				
				
	except Exception as be:
		print(be)
		
		note = tmd.Note.objects.all()
		try:
			st_date = request.GET['st_date']
			if st_date != "":
				st_date_dtm = datetime.strptime(st_date, "%Y-%m-%d")
				note = note.filter(t_date__gt = st_date_dtm)
		except Exception as e:
			print(e)
		
		try:
			ed_date = request.GET['ed_date']
			if ed_date != "":
				ed_date_dtm = datetime.strptime(ed_date, "%Y-%m-%d") 
				note = note.filter(t_date__lte = ed_date_dtm)
		except Exception as e:
			print(e)
			
		#多个提取
		for i in note:
			note_list.append([i.t_stamp, i.t_name, i.t_type,  i.t_date, i.t_content])

	return JsonResponse(note_list, safe=False)
	
def k_data_json(request,r_code):

	#store_k_data to tmp table
	dbtools.storekdata(r_code)
	k_data = tmd.K_days.objects.filter(code = r_code)
	k_list = []
	for i in k_data:
		k_list.append([str(i.date),i.open,i.close,i.low,i.high,i.volume])
		
	return JsonResponse(k_list, safe=False)

def trade_data_json(request):

	#store_k_data to tmp table
	stat_data = tmd.StatisticTradeData.objects.all().order_by('o_date')
	
	#买入时间大于等于st_date
	try:
		st_date = request.GET['st_date']
		if st_date != "":
			st_date_dtm = datetime.strptime(st_date, "%Y-%m-%d")
			stat_data = stat_data.filter(i_date__gt = st_date_dtm)
	except Exception as e:
		print(e)
	
	#卖出时间小于等于ed_date	
	try:
		ed_date = request.GET['ed_date']
		if ed_date != "":
			ed_date_dtm = datetime.strptime(ed_date, "%Y-%m-%d") 
			stat_data = stat_data.filter(o_date__lte = ed_date_dtm)
	except Exception as e:
		print(e)
	
	try:
		r_name = request.GET['r_name']
		if r_name != "":
			stat_data = stat_data.filter(name = r_name)
	except Exception as e:
		print(e)
	stat_list = []
	for i in stat_data:
		stat_list.append([i.code,i.name,str(i.i_date),str(i.o_date),i.i_total,i.time,i.earning,i.pct])
	return JsonResponse(stat_list, safe=False)