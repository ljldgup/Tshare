
/*基于准备好的dom，初始化echarts实例*/
var myChart = echarts.init(document.getElementById('main'));

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
        volumns: volumns,
        //四种振幅
        pct_data1 : calculatePct(1, values),
        pct_data2 : calculatePct(2, values),
        pct_data3 : calculatePct(3, values),
        pct_data4 : calculatePct(4 ,values)
    };
}

// rawData数据意义：开盘(open)，收盘(close)，最低(lowest)，最高(highest)
//从json中获取数据

var data0 = splitData(rData);


//计算涨幅等百分比数据
function calculatePct(type, values) {
    var pct = [];
    var tmp
    
    for (var i = 0, len = values.length; i < len; i++) {
    
        if (i < 1) {
            pct.push('-');
            //alert(result);
            continue;   //结束单次循环，即不输出本次结果
        }
        
        switch(type)
            {
                //涨幅
                case 1:
                    tmp = ((values[i][1] - values[i-1][1]) / values[i-1][1]*100).toFixed(2);
                    break;
                //振幅
                case 2:
                    tmp = ((values[i][3] - values[i][2]) / values[i-1][1]*100).toFixed(2)  
                    break;

                //最高点
                case 3:
                    tmp = ((values[i][3] - values[i-1][1]) / values[i-1][1]*100).toFixed(2);
                    break;
                //最低点
                case 4:
                    tmp = ((values[i][2] - values[i-1][1]) / values[i-1][1]*100).toFixed(2);
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



//输出涨跌幅振幅
function calculateLatitude(params){
    param = params[0];
    var tmp = '日期: ' + param.name + '<hr size=1 style="margin: 3px 0">'
    
    //引入成交量后，两个图显示不一致，所以使用全局变量
    tmp += '开盘: ' + data0.values[param.dataIndex][0] + '<br/>'
    tmp += '收盘: ' + data0.values[param.dataIndex][1] + '<br/>'

    //这个函数是在外部调用的所以要写option
    if (data0.pct_data1[param.dataIndex] > 0 ) {
            tmp += '涨幅: <span style="color:red">' + data0.pct_data1[param.dataIndex] + '&#37;</span><br/>'; 
          } else {
            tmp += '涨幅: <span style="color:green">' + data0.pct_data1[param.dataIndex] + '&#37;</span><br/>';
    };
    tmp +='<hr size=1 style="margin: 3px 0">'
    tmp += '振幅: ' + data0.pct_data2[param.dataIndex] + '&#37;<br/>';
    
    if (data0.pct_data3[param.dataIndex] > 0 ) {
            tmp += '最高: <span style="color:red">' + data0.pct_data3[param.dataIndex] + '&#37;</span><br/>'; 
          } else {
            tmp += '最高: <span style="color:green">' + data0.pct_data3[param.dataIndex] + '&#37;</span><br/>';
    };
    
    if (data0.pct_data4[param.dataIndex] > 0 ) {
            tmp += '最低: <span style="color:red">' + data0.pct_data4[param.dataIndex] + '&#37;</span><br/>'; 
          } else {
            tmp += '最低: <span style="color:green">' + data0.pct_data4[param.dataIndex] + '&#37;</span><br/>';
    };
    return tmp;
}

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
                        if (data0.pct_data1[params.dataIndex] > 0 ) {
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
    
    option.tooltip.formatter = param => (calculateLatitude(param) + calculateEarning(param));
    
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

if ( $('#title').text().indexOf("分析") > 0 ){
    
    option.tooltip.formatter = calculateLatitude;
    option.dataZoom.forEach(function(zoom){
        var date = new Date();
        zoom.start = 100 < rData.length ? 100 -  100/rData.length * 100 : 1;
        zoom.end = 100 ;
    });
    option.series[0].markLine = getTrendMarkLine();
}

// 使用刚指定的配置项和数据显示图表
myChart.setOption(option);