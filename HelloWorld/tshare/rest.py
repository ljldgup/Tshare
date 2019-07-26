from . import models as tmd
from datetime import datetime
from django.http import JsonResponse
from . import dbtools

import sys
sys.path.append("..")
from tools import share_statistic

def delete_note(request):
    data = {}
    try:
        r_stamp = request.GET['r_stamp']
        tmd.Note.objects.filter(t_stamp = r_stamp).delete()
    except Exception as e:
        print(e)

    return HttpResponseRedirect('../all_note/')

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

def ori_trade_data_json(request):
    r_code = request.GET['r_code']
    ori_data = tmd.OriginalTradeData.objects.filter(code = r_code)
    stat_list = []
    for i in ori_data:
        stat_list.append([str(i.date), i.name, i.amount, i.price, i.sum])
    return JsonResponse(stat_list, safe=False)

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
    
    #买入时间小于等于ed_date    
    try:
        ed_date = request.GET['ed_date']
        if ed_date != "":
            ed_date_dtm = datetime.strptime(ed_date, "%Y-%m-%d") 
            stat_data = stat_data.filter(i_date__lte = ed_date_dtm)
    except Exception as e:
        print(e)
    

    stat_list = []
    for i in stat_data:
        stat_list.append([i.code,i.name,str(i.i_date),str(i.o_date),i.i_total,i.time,i.earning,i.pct])
    return JsonResponse(stat_list, safe=False)
    
    
def trend_data_json(request, r_code):
    trendData = share_statistic.Share(r_code, 'W', '1995-05-18', '2019-07-06')
    trendData.setJudgeCondition(4, 4, 15, -4, 4, -15)
    trendData.statistic()
    
    data_list = {}
    
    data_list['qfqData'] = []
    for i in trendData.oriData.index:
        data_list['qfqData'].append([trendData.oriData.date[i], trendData.oriData.open[i], trendData.oriData.close[i], trendData.oriData.high[i], trendData.oriData.low[i], trendData.oriData.volume[i]])

    data_list['trendData'] = []
    for i in trendData.trendData.index:
        data_list['trendData'].append([trendData.trendData.start_date[i], trendData.trendData.end_date[i], trendData.trendData.open[i], trendData.trendData.close[i], trendData.trendData.pct[i], int(trendData.trendData.last_weeks[i])])

    return JsonResponse(data_list, safe=False)