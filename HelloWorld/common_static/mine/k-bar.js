
/*基于准备好的dom，初始化echarts实例*/
var myChart = echarts.init(document.getElementById('main'));


//是否有日期参数，没有则显示全部范围
var url = self.location.href;
var url_param;
var r_code = url.split('/')[4]

// 数据意义：开盘(open)，收盘(close)，最低(lowest)，最高(highest)
//从json中获取数据
var rData = []

$.ajaxSetup({async:false});
$.getJSON("/k_data_json/" + r_code + "/", function(data){
    rData = data;
})

var detailData = []
$.getJSON("/ori_trade_data_json/?r_code=" + r_code , function(data){
    detailData = data;
})

var markData=[]
detailData.forEach(function(oriData){
    tmpData={}
    tmpData.name = oriData[1];
    tmpData.coord = [oriData[0], oriData[3]];
    tmpData.value = oriData[2];
    if(tmpData.value < 0) tmpData.itemStyle = {color:'rgb(0,128,0)'}
    else tmpData.itemStyle = {color:'rgb(128,0,0)'}
    markData.push(tmpData)
})

var r_name = $('#title').text().split("(")[0];

//切割数组，把数组中的日期和数据分离，返回数组中的日期和数据
function splitData(rawData) {
    var categoryData = [];
    var values = [];
    var volumns = [];
    for (var i = 0; i < rawData.length; i++) {
        categoryData.push(rawData[i].splice(0, 1)[0]);
        values.push(rawData[i]);
        volumns.push(rawData[i][4]);
    }
    return {
        categoryData: categoryData,
        values: values,
        volumns: volumns
    };
}

var data0 = splitData(rData);

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
//计算涨幅等百分比数据
function calculatePct(type) {
    var pct = [];
    var tmp
    
    for (var i = 0, len = data0.values.length; i < len; i++) {
    
        if (i < 1) {
            pct.push('-');
            //alert(result);
            continue;   //结束单次循环，即不输出本次结果
        }
        
        switch(type)
            {
                //涨幅
                case 1:
                    tmp = ((data0.values[i][1] - data0.values[i-1][1]) / data0.values[i-1][1]*100).toFixed(2);
                    break;
                //振幅
                case 2:
                    tmp = ((data0.values[i][3] - data0.values[i][2]) / data0.values[i-1][1]*100).toFixed(2)  
                    break;

                //最高点
                case 3:
                    tmp = ((data0.values[i][3] - data0.values[i-1][1]) / data0.values[i-1][1]*100).toFixed(2);
                    break;
                //最低点
                case 4:
                    tmp = ((data0.values[i][2] - data0.values[i-1][1]) / data0.values[i-1][1]*100).toFixed(2);
                    break;
                default:
                    tmp = '-';
                    break;
            }
        
        pct.push(tmp);
       // alert(result);
    }
    return pct;
}

//四种涨幅
var pct_data1 = calculatePct(1);
var pct_data2 = calculatePct(2);
var pct_data3 = calculatePct(3);
var pct_data4 = calculatePct(4);

option = {
    title: {    //标题
        text: r_name,
        left: 0
    },
    tooltip: {  //提示框
        trigger: 'axis',
        axisPointer: {
            type: 'cross'
        },
        backgroundColor: 'rgba(245, 245, 245, 0.8)',
        borderWidth: 1,
        borderColor: '#ccc',
        padding: 10,
        textStyle: {
            color: '#000'
        }
    },
    legend: {   //图例控件，点击图例控制哪些系列不现实
        data: ['日K', 'MA10', 'MA20', 'MA60']
    },
    grid: [
        {
            left: '4%',
            right: '0%',
            height: '60%'
        },
        {
            left: '4%',
            right: '0%',
            bottom: '15%',
            height: '8%'
        }
    ],
    xAxis: [
        {
            type: 'category',
            data: data0.categoryData,
            scale: true,
        },
        {
            type: 'category',
            gridIndex: 1,
            data: data0.categoryData,
        }
    ],
    yAxis: [
        {
            scale: true,
            splitArea: {
                show: true
            }
        },
        {
            scale: true,
            gridIndex: 1,
            splitNumber: 2,
        }
    ],
    dataZoom: [
        {
            type: 'inside',
            //k线图 和成交量同时缩放
            xAxisIndex: [0, 1],
        },
        {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            top: '85%',
        }
    ],
    series: [   //图表类型
        {
            name: '日K',
            type: 'candlestick',    //K线图
            data: data0.values,     //y轴对应的数据
            itemStyle: {
                normal: {
                    color: 'red', // 阳线填充颜色
                    color0: 'lightgreen', // 阴线填充颜色
                    lineStyle: {
                        width: 2,
                        color: 'orange', // 阳线边框颜色
                        color0: 'lightgreen' // 阴线边框颜色
                    }
                }
            }
        },
        
        //成交量
        {
            name: 'Volumn',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: data0.volumns,
            itemStyle: {
                normal: {
                    color: function(params) {
                        var colorList;
                        if (this.pct_data1[params.dataIndex] > 0 ) {
                            colorList = '#ef232a';
                        } else {
                            colorList = '#14b143';
                        }
                        return colorList;
                    },
                }
            }
        }
    ]
};

if ( $('#title').text().indexOf("交易") > 0 ){
    
    option.tooltip.formatter = calculateEarning;
    
    option.legend.data = ['日K', 'MA10', 'MA20', 'MA60'];
    
    pos = getViewPostion();
    option.dataZoom.forEach(function(zoom){
        zoom.start = pos.st_pos;
        zoom.end = pos.ed_pos;
    });
    
    option.series[0].markPoint = {
        label: {
            normal: {
                formatter: function (param) {
                    return param.value;
                }
            }
        },
        
        data: getOperationMark(),
        
        tooltip: {
            show: true,
            formatter: function(e) {
                // return e.data.displayname;
                return 'hello';
            },
            // position: [500, 10],
            triggerOn: 'click'
        },
        
        symbol:"arrow",
        symbolSize:15,
        tooltip: {
        }
    };
    
}

if ( $('#title').text().indexOf("趋势") > 0 ){
    option.series[0].markLine = getTrendMarkLine();
}

// 使用刚指定的配置项和数据显示图表
myChart.setOption(option);