//是否有日期参数，没有则显示全部范围
var url = self.location.href;
var url_param;
var r_code = url.split('/')[4]

//交易数据
$.ajaxSetup({async:false});
$.getJSON("/trend_data_json/" + r_code , function(data){
    rData = data.qfq_data;
    trendData = data.merged_trend_data;
    for(i=0;i<trendData.length;i++){
        trendData[i][4] = trendData[i][4].toFixed(2)
    }
})

//计算MA平均线，N日移动平均线=N日收盘价之和/N  dayCount要计算的天数(5,10,20,30)
function calculateMA(dayCount) {
    var result = [];
    for (var i = 0, len = data0.values.length; i < len; i++) {
        if (i < dayCount) {
            result.push('-');
            //alert(result);
            continue;   //结束单次循环，即不输出本次结果
        }
        var sum = 0;
        for (var j = 0; j < dayCount; j++) {
            //收盘价总和
            sum += data0.values[i - j][1];
            //alert(sum);
        }
        result.push(sum / dayCount);
       // alert(result);
    }
    return result;
}



function getTrendMarkLine(){
    var MarkLine={}
    
    MarkLine.lineStyle = {
      normal: {
        type: 'dash',
        color: '#0A0A0A',
      },
      symbolSize:5,
    }
    
    MarkLine.data = [];
    
    trendData.forEach( function(oriData){
        var startPoint={};
        var endPoint={}
        startPoint.xAxis = oriData[0];
        endPoint.xAxis = oriData[1];
        startPoint.yAxis = oriData[2];
        endPoint.yAxis = oriData[3];
        MarkLine.data.push([startPoint, endPoint])
    })
    return MarkLine;
}