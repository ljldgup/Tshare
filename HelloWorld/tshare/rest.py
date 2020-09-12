from . import models as tmd
from datetime import datetime
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse

from tools import share_trend_statistic
from tools import trade_statistic
from tools import commom_tools

# 每次启动时把db里数据清一下，因为日期可能不是最新的
trade_statistic.store_trade()


def delete_note(request):
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
    # 先检测后存储
    k_data = commom_tools.get_k_data(r_code, 'd', 'bfq')
    k_data = k_data[['date', 'open', 'close', 'low', 'high', 'volume']].values.tolist()

    return JsonResponse(k_data, safe=False)


def ori_trade_data_json(request):
    r_code = request.GET['r_code']
    ori_data_w = tmd.OriginalTradeData.objects.filter(code=r_code)
    stat_list = []
    for i in ori_data_w:
        stat_list.append([str(i.date), i.name, i.amount, i.price, i.sum])
    return JsonResponse(stat_list, safe=False)


def trade_data_json(request):
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
        # 这里从sqlite取出的数据有精度问题，但sqlite数据库中数据是没问题的所以应该是db映射框架有问题,使用round进行截断
        # print(i.pct)
        stat_list.append([i.code, i.name, str(i.i_date), str(i.o_date), i.i_total, i.time, i.earning, round(i.pct, 2)])
    return JsonResponse(stat_list, safe=False)


# 前复权数据，趋势数据
def trend_data_json(request, r_code):
    share = share_trend_statistic.Share(r_code)

    if r_code == 'sh' or r_code == 'sz' or r_code == 'cyb':
        # 深沪，创业板
        share.set_judge_condition(0.1, 4, 6, 0.1, 4, -6)
    else:
        share.set_judge_condition(0.1, 4, 18, 0.1, 4, -18)
    share.statistic()

    data_list = {}
    data_list['qfq_data'] = share.ori_data_w[
        ['date', 'open', 'close', 'high', 'low', 'volume']].values.tolist()
    data_list['trend_data'] = share.trend_data[
        ['start_pos', 'end_pos', 'open', 'close', 'pct', 'last_periods']].values.tolist()
    data_list['secondary_trend_data'] = share.secondary_trend[
        ['start_pos', 'end_pos', 'open', 'close', 'pct', 'last_periods', 'space_pct', 'time_pct']].values.tolist()
    data_list['merged_trend_data'] = share.merged_trend[
        ['start_pos', 'end_pos', 'open', 'close', 'pct', 'last_periods']].values.tolist()

    return JsonResponse(data_list, safe=False)
