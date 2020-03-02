from . import models as tmd
from datetime import datetime
from django.http import JsonResponse, HttpResponseRedirect
from . import dbtools

import sys

sys.path.append("..")
from tools import share_statistic
from tools import trade_analysis

dbrefreshed = False


def delete_note(request):
    data = {}
    try:
        r_stamp = request.GET['r_stamp']
        tmd.Note.objects.filter(t_stamp=r_stamp).delete()
    except Exception as e:
        print(e)

    return HttpResponseRedirect('../all_note/')


# json data response
def note_json(request):
    note_list = []

    try:
        # 单条数据
        r_stamp = request.GET['r_stamp']
        if r_stamp != "":
            try:
                i = tmd.Note.objects.get(t_stamp=r_stamp)
                note_list.append([i.t_stamp, i.t_name, i.t_type, i.t_date, i.t_content])
            except Exception as e:
                print(e)


    except Exception as be:
        print(be)

        note = tmd.Note.objects.all()
        try:
            st_date = request.GET['st_date']
            if st_date != "":
                st_date_dtm = datetime.strptime(st_date, "%Y-%m-%d")
                note = note.filter(t_date__gt=st_date_dtm)
        except Exception as e:
            print(e)

        try:
            ed_date = request.GET['ed_date']
            if ed_date != "":
                ed_date_dtm = datetime.strptime(ed_date, "%Y-%m-%d")
                note = note.filter(t_date__lte=ed_date_dtm)
        except Exception as e:
            print(e)

        # 多个提取
        for i in note:
            note_list.append([i.t_stamp, i.t_name, i.t_type, i.t_date, i.t_content])

    return JsonResponse(note_list, safe=False)


# 注意这里是不复权的k线数据，为了匹配买卖情况
def k_data_json(request, r_code):
    # store_k_data to tmp table
    dbtools.storekdata(r_code)
    k_data = tmd.K_days.objects.filter(code=r_code)
    k_list = []
    for i in k_data:
        k_list.append([str(i.date), i.open, i.close, i.low, i.high, i.volume])

    return JsonResponse(k_list, safe=False)


def ori_trade_data_json(request):
    r_code = request.GET['r_code']
    ori_data_w = tmd.OriginalTradeData.objects.filter(code=r_code)
    stat_list = []
    for i in ori_data_w:
        stat_list.append([str(i.date), i.name, i.amount, i.price, i.sum])
    return JsonResponse(stat_list, safe=False)


def trade_data_json(request):
    global dbrefreshed
    if dbrefreshed == False:
        trade_analysis.store_trade()
        dbrefreshed = True

    # store_k_data to tmp table
    stat_data = tmd.StatisticTradeData.objects.all().order_by('o_date')

    # 买入时间大于等于st_date
    try:
        st_date = request.GET['st_date']
        if st_date != "":
            st_date_dtm = datetime.strptime(st_date, "%Y-%m-%d")
            stat_data = stat_data.filter(i_date__gt=st_date_dtm)
    except Exception as e:
        print(e)

    # 买入时间小于等于ed_date
    try:
        ed_date = request.GET['ed_date']
        if ed_date != "":
            ed_date_dtm = datetime.strptime(ed_date, "%Y-%m-%d")
            stat_data = stat_data.filter(i_date__lte=ed_date_dtm)
    except Exception as e:
        print(e)

    stat_list = []
    for i in stat_data:
        stat_list.append([i.code, i.name, str(i.i_date), str(i.o_date), i.i_total, i.time, i.earning, i.pct])
    return JsonResponse(stat_list, safe=False)


# 趋势数据
def trend_data_json(request, r_code):
    share = share_statistic.Share(r_code)

    if r_code == 'sh' or r_code == 'sz' or r_code == 'cyb':
        # 深沪，创业板
        share.set_judge_condition(1, 2, 6, -1, 2, -6)
    else:
        share.set_judge_condition(3, 3, 15, -3, 3, -15)

    share.statistic()
    data_list = {}

    ori_data_w = share.ori_data_w
    trend_data = share.trend_data
    secondary_trend_data = share.secondary_trend_data
    merged_trend_data = share.merged_trend_data

    data_list['qfq_data'] = []
    for i in ori_data_w.index:
        data_list['qfq_data'].append(
            [ori_data_w.date[i], ori_data_w.open[i], ori_data_w.close[i], ori_data_w.high[i], ori_data_w.low[i],
             ori_data_w.volume[i]])

    data_list['trend_data'] = []
    for i in trend_data.index:
        data_list['trend_data'].append(
            [trend_data.start_pos[i], trend_data.end_pos[i], trend_data.open[i], trend_data.close[i], trend_data.pct[i],
             int(trend_data.last_weeks[i])])

    data_list['secondary_trend_data'] = []
    for i in secondary_trend_data.index:
        data_list['secondary_trend_data'].append(
            [secondary_trend_data.start_pos[i], secondary_trend_data.end_pos[i], secondary_trend_data.open[i],
             secondary_trend_data.close[i], secondary_trend_data.pct[i], int(trend_data.last_weeks[i]),
             secondary_trend_data.space_pct[i], secondary_trend_data.time_pct[i]])

    data_list['merged_trend_data'] = []
    for i in merged_trend_data.index:
        data_list['merged_trend_data'].append([merged_trend_data.start_pos[i], merged_trend_data.end_pos[i],
                                               merged_trend_data.open[i], merged_trend_data.close[i],
                                               merged_trend_data.pct[i],
                                               int(merged_trend_data.last_weeks[i])])

    return JsonResponse(data_list, safe=False)
