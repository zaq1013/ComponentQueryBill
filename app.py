from flask import Flask, render_template, request, make_response, redirect, session, flash, send_file, send_from_directory, Response,jsonify
import pyodbc
import os
import shutil
import json
import datetime
import logging

app = Flask(__name__)

app.secret_key = 'pl112004'  # 設定一個安全的密鑰，用於加密session

server = '77.0.0.151'
database = 'plQuote_train'
username = 'plis'
password = 'spl_20765242'


@app.route('/component/<machine_number>', methods=['GET', 'POST'])
def component(machine_number,keyword=''):
    if 'agent_code' not in session:
        return redirect('/login')
    else:
        agent = session['agent_code']
    bom_rows = []
    part_rows = []
    if request.method == 'POST':
        machine_number = request.form.get("machine_number", default='')
        keyword = request.form.get("keyword", default='')
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()
    
    query = f"SELECT sbom_code,sbom_lot,sbom_comp,sbom_desc,sbom_group,sbom_qty_per,sbom_par,sbom_code_par,xsom_bill from sbom_det join xsom_refMC on sbom_code = xsom_code  WHERE sbom_code = '{machine_number}' AND xsom_bill = '{agent}' AND (sbom_comp LIKE '%{keyword}%' OR sbom_desc LIKE '%{keyword}%' OR sbom_group LIKE '%{keyword}%' OR sbom_par LIKE '%{keyword}%' OR sbom_group LIKE '%{keyword}%' OR sbom_code_par LIKE '%{keyword}%')"
    cursor.execute(query)
    data = cursor.fetchall()
    
    query_results = cursor.fetchall()
    for row in data:
        if row.sbom_code_par is None:
            bom_rows.append(row)
        else:
            part_rows.append(row)
        
    grouped_parts = {}
    current_group = None
    for row in part_rows:
        if current_group is None or row.sbom_code_par != current_group:
            current_group = row.sbom_code_par
            grouped_parts[current_group] = []

        grouped_parts[current_group].append(row)
    connection.close()

    return render_template('index2.html',query_results=query_results, bom_rows=bom_rows, part_rows=part_rows, machine_number=machine_number,grouped_parts=grouped_parts,keyword=keyword)


# 用於獲取代理商帳號列表的函數
def get_agent_accounts():
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()
    
    # 使用SQL語句獲取唯一的代理商帳號
    cursor.execute("SELECT DISTINCT cust_bill FROM customer")
    agent_accounts = [row[0] for row in cursor.fetchall()]
    
    connection.close()
    
    return agent_accounts

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        agent_code = request.form.get('agent_code', '')
        agent_accounts = get_agent_accounts()

        if agent_code in agent_accounts:
            session['agent_code'] = agent_code
            return redirect('/search')
        else:
            flash('登入失敗，請檢查代號')

    return render_template('login.html')
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

def perform_search(agent_code, customer_id, customer_name, machine_number):
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()

    query = f"""
        SELECT Xsom_cust as 客戶ID, cust_bill as 代理, Xsom_nbr as 訂單號碼, Xsom_code as 機號, Xsom_part as 機台料號,
        Xsom_cmmt as 機種, Xsom_inch as 尺吋, Xsom__chr01 as 工單ID, Xsom_cust_name as 客戶Name, Xsom_slspsn as 業務員,
        Xsom_acsh_date as 出貨日期, Xsom_desc1 as 說明一, xsom_feeder as 口數
        FROM customer
        JOIN xsom_refMC ON customer.cust_id = xsom_refMC.Xsom_cust
        WHERE cust_bill = ? AND customer.cust_id LIKE ? AND customer.cust_name LIKE ? AND xsom_code LIKE ? 
        ORDER BY xsom_code DESC
    """

    cursor.execute(query, (agent_code, f'%{customer_id}%', f'%{customer_name}%', f'%{machine_number}%'))
    query_results = cursor.fetchall()
    connection.close()

    return query_results

@app.route('/search', methods=['GET', 'POST'])
def search(message=''):
    if 'agent_code' not in session:
        return redirect('/login')

    query_results = []
    show_result_table = False
    if request.method == 'POST':
        agent_code = session['agent_code']
        customer_id = request.form.get('customer_id', '')
        customer_name = request.form.get('customer_name', '')
        machine_number = request.form.get('machine_number', '')

        query_results = perform_search(agent_code, customer_id, customer_name, machine_number)
        show_result_table = True

    elif 'agent_code' in session:
        agent_code = session['agent_code']
        query_results = perform_search(agent_code, '', '', '')  # 設置查詢條件
        show_result_table = True
    if message != '':
        flash('新增成功')
    return render_template('search.html', query_results=query_results, show_result_table=show_result_table)

def get_machine_file_name(machine_number):
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={"plis"};UID={username};PWD={password}')
    cursor = connection.cursor()

    query = f"""
        SELECT TOP(1) tmd_revPath 
        FROM TManual_mstr 
        JOIN TManuald_det ON xtm_Machine = tmd_machine 
        WHERE xtm_Build_lastRev = tmd_Build_Name AND xtm_Machine = ?
    """

    cursor.execute(query, (machine_number,))
    result = cursor.fetchone()[0]
    connection.close()
    if result == machine_number:
        return "Index.html"
    else:
        return result+"_Index.html"
@app.route('/get_machine_file_name/<machine_number>')
def get_machine_file_name_ajax(machine_number):
    machine_folder_path = os.path.join("file:\\\\77.0.0.134\\cd_output(mis)\\code", machine_number)
    machine_file_name = get_machine_file_name(machine_number)
    # 文件名為空或找不到檔案
    if not machine_file_name or not os.path.exists(os.path.join(machine_folder_path, machine_file_name)):
        machine_file_name = machine_number + "_Index.html"
    print(machine_file_name)
    return machine_file_name
@app.route('/link/<machine_number>')
def link(machine_number):
    # machine_folder_path = os.path.join("", machine_number)
    machine_folder_path = os.path.join("file:\\\\77.0.0.134\\cd_output(mis)\\code", machine_number)
    # 如果機號資料夾中沒有 tabs.css 文件，就將其複製到機號資料夾中
    # if not os.path.exists(os.path.join(machine_folder_path, 'tabs.css')):
    #     shutil.copy("\\\\77.0.0.134\\cd_output(mis)\\code\\BuildCss\\tabs.css", machine_folder_path)
    
    machine_file_name = get_machine_file_name(machine_number)
    manual_path = os.path.join(machine_folder_path, machine_file_name)
    print(manual_path)

    # 文件名為空或找不到檔案
    if not machine_file_name or not os.path.exists(os.path.join(machine_folder_path, machine_file_name)):
        machine_file_name = machine_number + "_Index.html"
        manual_path = os.path.join(machine_folder_path, machine_file_name)
        # return send_file(manual_path)
    print(machine_folder_path)
    print(machine_file_name)
    print(manual_path)
    # a = send_from_directory("\\\\77.0.0.134\\cd_output(mis)\\code", machine_number)
    # a = send_from_directory(machine_folder_path, machine_file_name)
    return f'<h2>請在瀏覽器輸入此路徑: {manual_path}</h2>'

@app.route('/')
def root():
    # return redirect('/home')
    return redirect('/login')

@app.route('/confirmation', methods=['GET', 'POST'])
def confirmation():
    if 'agent_code' not in session:
        return redirect('/login')
    else:
        agent = session.get('agent_code')
    if request.method == 'POST':
        selected_data_json = request.form.get('selected_data', '[]')
        selected_data = json.loads(selected_data_json)
        # 在confirmation.hrml頁面中，使用selected_data當作頁面顯示資料的來源
    print(selected_data)
    machine_number = selected_data[0]['code']
    return render_template('confirmation.html', selected_data=selected_data)

@app.route('/add_to_cart', methods=['GET', 'POST'])
def add_to_cart():
    if 'agent_code' not in session:
        return redirect('/login')
    else:
        agent = session.get('agent_code')
    if request.method == 'POST':
        selected_data_json = request.form.get('selected_data', '[]')
        selected_data = json.loads(selected_data_json)
    
    machine_number = selected_data[0]['sbom_code']
    for i in range(len(selected_data)):
        if selected_data[i]['sbom_code'] == '':
            selected_data[i]['sbom_code'] = machine_number
            selected_data[i]['type'] = '零件包內零件'
        elif selected_data[i]['sbom_material'] == '':
            selected_data[i]['type'] = '零件包'
        else:
            selected_data[i]['type'] = '一般零件'
 
    cart = session.get('cart')
    if cart is None:
        cart = []
    cart.append(selected_data)
    print("cart now:",cart)
    session['cart'] = cart

    # session['notify'] = '新增成功'
    
    return search(message='新增成功')

@app.route('/receive_data', methods=['POST'])
def receive_data():
    if request.method == 'POST':
            datas = request.get_json()  # 獲取前端發送的JSON資料
            machine_number = datas['machine_number']  # 從JSON資料中獲取機號
            connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
            cursor = connection.cursor()
            
            # cursor.execute(f"SELECT TOP 1 {'inq_num'} FROM {'inq_mstr'} ORDER BY {'inq_num'} DESC")
            # latest_num = cursor.fetchone()
            # if latest_num:
            #     # 若已有資料則在舊的編號上+1
            #     new_num = int(latest_num[0][2:]) + 1
            # else:
            #     # 若無主檔資料則設為初始值
            #     new_num = 1
            # new_num = f'Q2{new_num:05}'
            cart = session.get('cart')

            if cart is None:
                cart = []
            
            query = f"SELECT Xsom_cust FROM Xsom_refMC WHERE Xsom_code = '{machine_number}'"
            cursor.execute(query)
            cust = cursor.fetchone()[0]
            if 'agent_code' in session:
                agent = session['agent_code']
            # current_datetime = datetime.datetime.now()
            # formatted_date = current_datetime.strftime('%Y-%m-%d')
            # formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

            # print(agent, cust, machine_number, formatted_date, formatted_datetime)
            # Insert到主檔資料表
            # cursor.execute("INSERT INTO inq_mstr (inq_num, inq_bill, inq_cust, inq_code, inq_createdate, inq_summitdate) VALUES (?, ?, ?, ?, CAST(? AS DATE), CAST(? AS DATETIME))",
            #    (new_num, agent, cust, machine_number, formatted_date, formatted_datetime))
            # 遞迴資料內容並逐一插入table
            data = datas['data']
            for i in range(len(data)):
                inq_item = data[i]['項次']
                inq_comp = data[i]['詢價料號']
                inq_mach_qty = data[i]['機台用量']
                inq_order_qty = data[i]['訂購量']
                inq_type = data[i]['類型']
                if data[i]['機台用量'] in ["","None"]:
                    data[i]['機台用量'] = None
                if data[i]['訂購量'] in ["","None"]:
                    data[i]['訂購量'] = None
                # inq_price = row['詢價金額']
                data[i]['機號'] = machine_number
                data[i]['客戶'] = cust
                
                # cursor.execute("INSERT INTO inq_det (inq_det_num, inq_item, inq_comp, inq_mach_qty, inq_order_qty, inq_type, inq_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
                #             (new_num,inq_item, inq_comp, inq_mach_qty, inq_order_qty, inq_type,machine_number))
                # connection.commit()
            cart.append(data)
            print("cart now:",cart)
            session['cart'] = cart
            return 'Data submitted successfully'

@app.route('/show_cart', methods=['GET', 'POST'])
def show_cart():
    cart = session.get('cart')
    print(cart)
    data = []
    for i in cart:
        for j in i:
            data.append(j)
    return render_template('cart.html',cart=cart,data=data)

@app.route('/list_inquiries')
def list_inquiries():
    if 'agent_code' not in session:
        return redirect('/login')
    else:
        agent = session['agent_code']
    # 在此處編寫代碼來檢索代理商的所有詢價紀錄（inq_mstr資料表）
    # 並根據詢價狀態設置狀態為「詢價中」或「報價完成」。

    # 示例詢價紀錄列表（代碼需要替換成實際的查詢和設置狀態邏輯）
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()
    cursor.execute(f"SELECT inq_num as 單號, inq_bill as 代理 ,(SELECT cust_name FROM customer WHERE cust_id = inq_bill) as 代理名稱, cust_id as 客戶ID, cust_name as 客戶名稱,  inq_summitdate as 詢價日 ,inq_completedate as 完成日 from inq_mstr join customer on inq_mstr.inq_cust = customer.cust_id WHERE inq_bill = '{agent}' ORDER BY inq_summitdate DESC")
    inquiries = cursor.fetchall()
    return render_template('list_inquiries.html', inquiries=inquiries)

@app.route('/view_inquiry/<inquiry_id>', methods=['GET'])
def view_inquiry(inquiry_id):
    if 'agent_code' not in session:
        return redirect('/login')
    else:
        agent = session['agent_code']
    # 在此處編寫代碼來檢索詳細的詢價紀錄列表（inq_det資料表）
    # 使用 inquiry_id 來查詢相關信息。

    # 示例詳細的詢價紀錄列表（代碼需要替換成實際的查詢）
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()
    cursor.execute(f"SELECT  inq_item as 項次, inq_comp as 料號, inq_mach_qty as 機台用量, inq_order_qty as 訂購量, inq_inq_price as 詢價金額 ,inq_type as 類型, inq_code as 機號 FROM inq_det WHERE inq_det_num = '{inquiry_id}' order by inq_item")
    inquiry_details = cursor.fetchall()
    cursor.execute(f"SELECT inq_num as 單號, inq_bill as 代理 ,(SELECT cust_name FROM customer WHERE cust_id = inq_bill) as 代理名稱, cust_id as 客戶ID, cust_name as 客戶名稱, inq_summitdate as 詢價日 ,inq_completedate as 完成日 from inq_mstr join customer on inq_mstr.inq_cust = customer.cust_id WHERE inq_bill = '{agent}' AND inq_num = '{inquiry_id}'")
    basic = cursor.fetchall()
    return render_template('view_inquiry.html', inquiry_details=inquiry_details,inquiry_id=inquiry_id,basic=basic)



app.logger.setLevel(logging.ERROR)  # 只記錄錯誤信息
# if __name__ == '__main__':
#     app.run(debug=False,port=8071,host='0.0.0.0')
if __name__ == '__main__':
    app.run(debug=True)