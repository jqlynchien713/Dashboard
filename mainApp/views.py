from django.http import HttpResponse

# Create your views here.
from django.shortcuts import render
from .models import Order
import os
import sqlite3
from .forms import FormStatus
from .forms import FormSetID
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
# %matplotlib inline
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()  # for plot styling
import numpy as np
from io import BytesIO
import urllib, base64
from .forms import checkReturn

def template_test(request):
    return render(request, 'example.html')

def rrt(m):
    db = sqlite3.connect('mainApp.db')
    cursor = db.cursor()

    # if m==12: return render(request, 'test.html', {'order': ['no']})
    current = f'2021/{m}'
    prev = f'202{0 if m==1 else 1}/{12 if m==1 else m-1}'
    # （本期購買顧客數｜這些顧客也在前期購買）/ 前期購買顧客數
    sql = f"SELECT COUNT(*) FROM order_list o WHERE o.order_time LIKE '{current}/%' AND EXISTS (SELECT * FROM order_list o2 WHERE o2.client_id=o.client_id AND o2.order_time LIKE '{prev}/%')"
    cursor.execute(sql)
    fac = cursor.fetchall()[0][0]

    sql = f"SELECT COUNT(*) FROM order_list WHERE order_time LIKE '{prev}/%'"
    cursor.execute(sql)
    div = cursor.fetchall()[0][0]
    return round(fac/div,2)

def term(srt1, srt2, srt3):
    db = sqlite3.connect('mainApp.db')
    cursor = db.cursor()

    # if m==12: return render(request, 'test.html', {'order': ['no']})
    sql = f"SELECT COUNT(DISTINCT(client_id)) FROM order_list"
    cursor.execute(sql)
    total = cursor.fetchall()[0][0]
    return (srt1*total*1+srt2*total*2+srt3*total*3)/total

def client_group():    
    db = sqlite3.connect('mainApp.db')
    sql = "SELECT client_id, SUM(quantity) AS quantity, COUNT(*) AS order_nums, SUM(payment) AS total_payment, COUNT(channel) AS channels, COUNT(address) AS address_nums FROM order_list GROUP BY client_id"
    df = pd.read_sql_query(sql, db)

    print(df)

    kmeans = KMeans(init='k-means++', n_clusters=3, n_init=10)
    kmeans.fit(df)
    y = kmeans.predict(df)
    df['y'] = y
    colors = {0:'r', 1:'g', 2:'b'}

    uris = {}
    for col in df.columns:
        plt.switch_backend('AGG')
        plt.style.use('dark_background')
        plt.scatter(df.loc[:, ['client_id']], df.loc[:, [col]],c=df.y.map(colors),  s=50, cmap='viridis')
        centers = kmeans.cluster_centers_
        plt.scatter(centers[:, 0], centers[:, 1], s=200, alpha=0.5);
        plt.xlabel('client_id')
        plt.ylabel(col)
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        graph = base64.b64encode(image_png)
        uri = graph.decode('utf-8')
        buffer.close()
        uris[col] = uri
        plt.close('all')

    type0 = df.loc[df.y==0].to_html()
    type1 = df.loc[df.y==1].to_html()
    type2 = df.loc[df.y==2].to_html()
    
    return uris['quantity'], uris['order_nums'], uris['total_payment'],type0,type1,type2

def renderMarketing(request):
    u_q, u_o, u_p,type0,type1,type2 = client_group()

    rrt3 = rrt(3)
    rrt2 = rrt(2)
    rrt1 = rrt(1)
    lss3 = round(1-rrt3, 2)
    lss2 = round(1-rrt2, 2)
    lss1 = round(1-rrt1, 2)
    srt1 = round(rrt1,5)
    srt2 = round(rrt2*srt1,5)
    srt3 = round(rrt3*srt2,5)
    avg_term = round(term(srt1, srt2, srt3), 3)
    return render(request, 'marketing.html',locals())

    

def order(request):

    db = sqlite3.connect('mainApp.db')
    cursor = db.cursor()

    ###Show 訂單列表
    sql = "SELECT * FROM order_list"
    cursor.execute(sql)
    res = cursor.fetchall()
    orderlist = list(res)

    ### 輸入order id 

    if request.method == 'POST':
        form2 = FormSetID(request.POST)
        if form2.is_valid():
            print('form2 valid')
            set_orderid = request.POST.get('set_orderid')
            print('order id:',set_orderid)
    else:
        form2 = FormSetID()
    
    

    ###更改 訂單狀態
    form = FormStatus()
    if request.method == "POST":
        form = FormStatus(request.POST)		
        if form.is_valid():
            response = request.POST.get('response')
            print('form valid Response:',response)

            if response =='已審核':
                replysql = "UPDATE order_list SET status = '已審核' WHERE order_id = ?"
                cursor.execute(replysql, (set_orderid,))
                db.commit()

            elif response == '備貨中':
                print('按備貨中')
                replysql = "UPDATE order_list SET status = '備貨中' WHERE order_id = ?"
                cursor.execute(replysql, (set_orderid,))
                db.commit()

            elif response == '已達包裹中心':
                replysql = "UPDATE order_list SET status = '已達包裹中心' WHERE order_id = ?"
                cursor.execute(replysql, (set_orderid,))
                db.commit()

            elif response == '已達物流中心':
                replysql = "UPDATE order_list SET status = '已達物流中心' WHERE order_id = ?"
                cursor.execute(replysql, (set_orderid,))
                db.commit()
                
            elif response == '已出貨':
                replysql = "UPDATE order_list SET status = '已出貨' WHERE order_id = ?"
                cursor.execute(replysql, (set_orderid,))
                db.commit()
                
            elif response == '已到達':
                replysql = "UPDATE order_list SET status = '已到達' WHERE order_id = ?"
                cursor.execute(replysql, (set_orderid,))
                db.commit()

            elif response == '已辦理退貨':
                replysql = "UPDATE order_list SET status = '已辦理退貨' WHERE order_id = ?"
                cursor.execute(replysql, (set_orderid,))
                db.commit()

            elif response == '退貨審核不通過':
                replysql = "UPDATE order_list SET status = '退貨審核不通過' WHERE order_id = ?"
                cursor.execute(replysql, (set_orderid,))
                db.commit()
            
        else:
            form = FormStatus()
            print('fail')

    context = {'orderlist':orderlist, 'form':form, 'form2':form2}
    return render(request, 'order.html', context)


def refund(request):
    
    db = sqlite3.connect('mainApp.db')
    cursor = db.cursor()

    id_list = []
    ###抓退貨單商品資料列表
    sql = "SELECT order_id FROM return"
    cursor.execute(sql)
    res = cursor.fetchall()
    #print('RESSSS', res)
    return_id = list(res)
    #print('IDDDDDDD', return_id)
    for i in return_id:
        orderid, = i
        orderid = '{}'.format(orderid)
        id_list.append(orderid)
    #print(id_list)
    #orderid, = res
	#orderid1, orderid2, orderid3 = tem_teamid
    #data = '{}'.format(teamid)
    #data1 = '{}'.format(wholesaler)
    #get_teamid = int(data)
    #get_wholesaler = int(data1)
 

    namelist = []
    returnlist = []
    detaillist = []
    wholelist = []
    for i in return_id:
        orderid, = i
        orderid = '{}'.format(orderid)
        sqlorder = "SELECT * FROM order_list WHERE order_id = ?"
        cursor.execute(sqlorder, (orderid,))
        res2 = cursor.fetchall()
        returnlist.extend(res2)
        #returnlist.extend(res2)
        sqlreturn = "SELECT logistic_id, return_time, order_product_id, reason FROM return WHERE order_id = ?"
        cursor.execute(sqlreturn, (orderid,))
        res3 = cursor.fetchall()
        detaillist.extend(res3)
        sqlname = "SELECT product FROM order_list WHERE order_id = ?"
        cursor.execute(sqlname, (orderid,))
        res4 = cursor.fetchall()
        namelist.extend(res4)
    wholelist = list(x + y for x, y in zip(returnlist, detaillist))
    print('EVERYYYYYYY', wholelist)
    #print(returnlist)

    form = checkReturn()
    if request.method == 'POST':
        form2 = FormSetID(request.POST)
        if form2.is_valid():
            
            set_orderid = request.POST.get('set_orderid')
            #print('order id:',set_orderid)
            sql_sta = "SELECT status FROM order_list WHERE order_id = ?"
            cursor.execute(sql_sta, (set_orderid,))
            res = cursor.fetchall()
            rep, = res
            rep, = rep
            status = '{}'.format(rep)
            if status == "退貨審核不通過":
                form2 = '此訂單先前已被審核為不通過，貨品已退回顧客'
                #print("STATUS: ",status)
            elif status == "已辦理退貨":
                form2 = '此訂單先前已被審核為通過，貨品已退回倉庫'
            else:
                if request.method == "POST":
                    form = checkReturn(request.POST)		
                    if form.is_valid():
                        response = request.POST.get('response')
                        

                        if response =='資格不符':
                            replysql = "UPDATE order_list SET status = '退貨審核不通過' WHERE order_id = ?"
                            cursor.execute(replysql, (set_orderid,))
                            db.commit()
                            

                        elif response == '確認退貨':
                            sql = "SELECT quantity, product FROM order_list WHERE order_id = ?"
                            cursor.execute(sql, (set_orderid,))
                            res = cursor.fetchall()
                            num_name, = res
                            num, name = num_name
                            quantity = '{}'.format(num)
                            name = '{}'.format(name)
                            #print('name: ', name, 'quantity: ', quantity)

                            sql_inv = "SELECT inventory, safety_stock FROM product WHERE product_name = ?"
                            cursor.execute(sql_inv, (name,))
                            res = cursor.fetchall()
                            inv, = res
                            inventory, safety = inv
                            inventory = '{}'.format(inventory)
                            safety = '{}'.format(safety)
                            #print('inventory: ', inventory, 'safety: ', safety)
                            final_inv = int(inventory) + int(quantity)

                            sql_inv = "UPDATE product SET inventory = ? WHERE product_name = ?"
                            content = (final_inv, name)
                            cursor.execute(sql_inv, content)
                            db.commit()

                            replysql = "UPDATE order_list SET status = '已辦理退貨' WHERE order_id = ?"
                            cursor.execute(replysql, (set_orderid,))
                            db.commit()
                    else:
                        print("qqqqq")
    else:
        form2 = FormSetID()
    
    

    context = {'wholelist':wholelist, 'form':form, 'form2':form2, 'id_list':id_list}
    return render(request, 'return.html', context)   
