var url = self.location.href;
var url_param;
var r_code = url.split('/')[4]

//交易数据
var detailData = []

$.ajaxSetup({async:false});
$.getJSON("/ori_trade_data_json/?r_code=" + r_code , function(data){
    detailData = data;
})

//操作标记点
function getOperationMark(){
    var markData=[]
    detailData.forEach(function(oriData){
        tmpData={}
        tmpData.name = oriData[1];
        tmpData.coord = [oriData[0], oriData[3]];
        tmpData.value = oriData[2];
        if(tmpData.value < 0) tmpData.itemStyle = {color:'rgb(0,128,0)'}
        else tmpData.itemStyle = {color:'rgb(128,0,0)'}
        markData.push(tmpData);
    })
    return markData;
}

//计算手数，成本
function calculateAmountCost(data) {
    var amount = [];
    var cost = [];
    var range = [0,data0.values.length-1];
    var t_amount;
    var t_cost;
    var len1 = this.data0.categoryData.length;
    var len2 = data.length
    
        //是否有日期参数，没有则显示全部范围
    if (url.indexOf("?") != -1){
        url_param = url.split('?')[1];
        if(url_param.indexOf("&") != -1){
            url_params = url_param.split('&');
        }
    }

    if(url_params == null ){
        url_params = [data0.categoryData[0],data0.categoryData[data0.categoryData.length - 1]];
    }

    for (var i = 0, k = 0; i < len1 ; i++) {
        //console.log(data0.categoryData[i] + "," + k + ","+ len2);
        if(url_params[0] == data0.categoryData[i]){
            range[0]=i;
        };
        if(url_params[1] == data0.categoryData[i]){
            range[1]=i;
        }
        
        if(k >= len2){
        //后续没有交易
            amount[i] = amount[i-1];
            cost[i] = cost[i-1];
            continue;
        }

        if (data0.categoryData[i] == data[k][0]) {
            //有可能一天进行多次交易当天进行交易
            if(i>0){
                amount[i] = amount[i-1];
                cost[i] = cost[i-1];
            }
            while(data0.categoryData[i] == data[k][0]){
                //有可能一天进行多次交易
                if(i == 0){
                    amount[0] = data[k][2]
                    cost[0] = -data[k][2]*data[k][3]
                }else{
                    amount[i] += data[k][2];
                    //成本买入为负，卖出为正
                    cost[i] += -data[k][2]*data[k][3];
                }
                
                k++;
                if(k >= len2) break;
            }
        }else{
            //console.log(data0.categoryData[i-1]);
            if(i == 0){
                //console.log("i==0");
                amount.push(0);
                cost.push(0);
            }else{
                if(amount[i-1] == 0 ){
                    //console.log("amount[amount.length-1] == 0 ");
                    amount[i] = 0;
                    cost[i] = 0;
                }
                else{
                    //console.log("amount[amount.length-1] == 0 else");
                    amount[i] = amount[i-1];
                    cost[i] = cost[i-1];
                }
            }
        }
        //console.log(k + ':' + data0.categoryData[i] + ":" + data[k][0]);

       // alert(result);
    }
    return {
        amount: amount,
        cost: cost,
        range: range
    };
}

function getViewPostion(){
    data1 = calculateAmountCost(detailData);
    st_pos = parseFloat((data1.range[0]/rData.length*100).toFixed(0)) - 0.4;
    ed_pos = parseFloat(((data1.range[1]-1)/rData.length*100).toFixed(0)) + 0.6;
    return { st_pos, ed_pos }
}


//计算持仓过程中的盈亏，用于echart中回调
function calculateEarning(params) {
    param = params[0];
    var tmp = '日期: ' + param.name + '<hr size=1 style="margin: 3px 0">'
    
    //引入成交量后，两个图显示不一致，所以使用全局变量
    tmp += '开盘: ' + this.data0.values[param.dataIndex][0] + '<br/>'
    tmp += '收盘: ' + this.data0.values[param.dataIndex][1] + '<br/>'

    //这个函数是在外部调用的所以要写option
    if (this.pct_data1[param.dataIndex] > 0 ) {
            tmp += '涨幅: <span style="color:red">' + this.pct_data1[param.dataIndex] + '&#37;</span><br/>'; 
          } else {
            tmp += '涨幅: <span style="color:green">' + this.pct_data1[param.dataIndex] + '&#37;</span><br/>';
    };
    tmp +='<hr size=1 style="margin: 3px 0">'
    tmp += '振幅: ' + this.pct_data2[param.dataIndex] + '&#37;<br/>';
    
    if (this.pct_data3[param.dataIndex] > 0 ) {
            tmp += '最高: <span style="color:red">' + this.pct_data3[param.dataIndex] + '&#37;</span><br/>'; 
          } else {
            tmp += '最高: <span style="color:green">' + this.pct_data3[param.dataIndex] + '&#37;</span><br/>';
    };
    
    if (this.pct_data4[param.dataIndex] > 0 ) {
            tmp += '最低: <span style="color:red">' + this.pct_data4[param.dataIndex] + '&#37;</span><br/>'; 
          } else {
            tmp += '最低: <span style="color:green">' + this.pct_data4[param.dataIndex] + '&#37;</span><br/>';
    };
    //个人持仓量
    var earning;
    if(param.dataIndex!=0 && this.data1.amount[param.dataIndex] == 0 && this.data1.amount[param.dataIndex-1] != 0){
        tmp +='<hr size=1 style="margin: 3px 0">'
        tmp += '持仓手数: ' + this.data1.amount[param.dataIndex] + '<br/>';
        tmp += '持仓金额: ' + (this.data1.amount[param.dataIndex]*this.data0.values[param.dataIndex][1]).toFixed(0)  + '<br/>';
        earning = this.data1.amount[param.dataIndex]*this.data0.values[param.dataIndex][1] + this.data1.cost[param.dataIndex];
        if(earning > 0 ){
            tmp += '盈亏金额: <span style="color:red">' + earning.toFixed(0) + '</span><br/>';
            tmp += '盈亏比例: <span style="color:red">' + parseInt(earning/(this.data1.amount[param.dataIndex-1]*this.data0.values[param.dataIndex][1])*10000)/100 + '&#37;</span><br/>';
        }else{
            tmp += '盈亏金额: <span style="color:green">' + earning.toFixed(0) + '</span><br/>';
            tmp += '盈亏比例: <span style="color:green">' + parseInt(earning/(this.data1.amount[param.dataIndex-1]*this.data0.values[param.dataIndex][1])*10000)/100 + '&#37;</span><br/>';
        }
    }
    else if(this.data1.amount[param.dataIndex] != 0){
        tmp +='<hr size=1 style="margin: 3px 0">'
        tmp += '持仓手数: ' + this.data1.amount[param.dataIndex] + '<br/>';
        tmp += '持仓金额: ' + (this.data1.amount[param.dataIndex]*this.data0.values[param.dataIndex][1]).toFixed(0)  + '<br/>';
        earning = this.data1.amount[param.dataIndex]*this.data0.values[param.dataIndex][1] + this.data1.cost[param.dataIndex];
        if(earning > 0 ){
            tmp += '盈亏金额: <span style="color:red">' + earning.toFixed(0) + '</span><br/>';
            tmp += '盈亏比例: <span style="color:red">' + parseInt(earning/(this.data1.amount[param.dataIndex]*this.data0.values[param.dataIndex][1])*10000)/100 + '&#37;</span><br/>';
        }else{
            tmp += '盈亏金额: <span style="color:green">' + earning.toFixed(0) + '</span><br/>';
            tmp += '盈亏比例: <span style="color:green">' + parseInt(earning/(this.data1.amount[param.dataIndex]*this.data0.values[param.dataIndex][1])*10000)/100 + '&#37;</span><br/>';
        }
    }
    return tmp;
}

