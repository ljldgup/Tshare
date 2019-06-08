from django.shortcuts import render
from . import models as tmd
from . import dbtools
import time
from django.http import HttpResponseRedirect

# Create your views here.

dbrefreshed = False

def homepage(request):
	return render(request, 'tshare/home.html',{})

#html response
def trade_report(request):
    global dbrefreshed
    if dbrefreshed == False:
        dbtools.refresh_k_data('k_bfq',)
        dbrefreshed = True
    data = {}
    try:
        st_date = request.GET['st_date']
        ed_date = request.GET['ed_date']
        data['st_date'] = st_date
        data['ed_date'] = ed_date

    except Exception as e:
        print(e)
    #保存页面数据

    return render(request, 'tshare/trade_report.html',data)
    
def trade_detail(request,r_code):

    #store_k_data to tmp table
    dbtools.storekdata(r_code)
    ori_data = tmd.OriginalTradeData.objects.filter(code = r_code)
    r_name = ori_data[0].name
    note = tmd.Note.objects.filter(t_name = r_name)
    note = note.filter(t_type = "个股操作")
    note = note.order_by('-t_date','-t_stamp')
    data = {}
    data['ori_data'] = ori_data;
    data['r_code'] = r_code
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
    st_date = ed_date = n = None
    try:
        st_date = request.GET['st_date']
        ed_date = request.GET['ed_date']
        data['st_date'] = st_date
        data['ed_date'] = ed_date

    except Exception as e:
        print(e)
        
    try:
        n = request.GET['n']
        data['n'] = int(n)

    except Exception as e:
        data['n'] = 20
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
    
def delete_note(request):
    try:
        r_stamp = request.GET['r_stamp']
        tmd.Note.objects.filter(t_stamp = r_stamp).delete()
    except Exception as e:
        print(e)

    return HttpResponseRedirect('../all_note/')


def share_analysis(request, r_code):
    dbtools.storekdata(r_code)
    ori_data = tmd.OriginalTradeData.objects.filter(code = r_code)
    r_name = ori_data[0].name
    note = tmd.Note.objects.filter(t_name = r_name)
    note = note.filter(t_type = "个股趋势")
    note = note.order_by('-t_date','-t_stamp')
    data = {}
    data['r_code'] = r_code
    data['r_name'] = r_name
    data['note'] = note
    return render(request, 'tshare/share_analysis.html',data)
