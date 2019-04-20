var url = self.location.href;
var url_param;
var r_code = url.split('/')[4]

//交易数据
var trendData = []

$.ajaxSetup({async:false});
$.getJSON("/trend_data_json/" + r_code , function(data){
    trendData = data;
})

function getTrendMarkLine(){
    var MarkLine={}
    
    MarkLine.lineStyle = {
      normal: {
        type: 'dash',
        color: '#0A0A0A',
      }
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