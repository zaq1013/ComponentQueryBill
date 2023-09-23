from flask import Flask, render_template, request, make_response, redirect, session, flash, send_file, send_from_directory, Response,jsonify
import pyodbc
import os
import shutil
import json
import datetime
import logging

app = Flask(__name__)

app.secret_key = ''  # 設定一個安全的密鑰，用於加密session

server = ''
database = ''
username = ''
password = ''

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

# 用於獲取代理商帳號列表的函數
def get_agent_accounts():
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()
    
    # 使用SQL語句獲取唯一的代理商帳號
    cursor.execute("SELECT DISTINCT cust_bill FROM customer")
    agent_accounts = [row[0] for row in cursor.fetchall()]
    for i in range(len(agent_accounts)):
        if (agent_accounts[i] is not None):
            agent_accounts[i] = agent_accounts[i].upper()
    # print(agent_accounts)
    connection.close()
    
    return agent_accounts

@app.route('/login', methods=['GET', 'POST'])
def login():
    # session['agent_code'] = None
    # session['customer'] = None
    if request.method == 'POST':
        agent_code = request.form.get('agent_code', '')
        agent_code = agent_code.upper()
        agent_accounts = get_agent_accounts()

        if agent_code in agent_accounts:
            session['agent_code'] = agent_code
            if 'cart' in session:
                # 重置購物車
                session['cart'] = {}
            return redirect('/search_customer')
            # return redirect('/search')
        else:
            flash('登入失敗，請檢查代號')

    return render_template('login.html')

@app.route('/search_customer', methods=['GET', 'POST'])
def search_customer():
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()
    show_result_table = False
    query_results = []
    session['customer'] = None
    session['sp_inq'] = False
    if 'agent_code' not in session:
        return redirect('/login')
    else:
        agent_code = session['agent_code']
        customer_id = request.form.get('customer_id', '')
        customer_name = request.form.get('customer_name', '')
        # query = f"SELECT c.cust_id as 客戶ID, c.cust_name as 客戶名, c.cust_bill as 代理, (SELECT cust_name FROM customer a WHERE  c.cust_bill = a.cust_id) AS 代理名 FROM customer c where cust_bill is not null AND cust_bill = '{agent_code}' and cust_id like '%{customer_id}%' and cust_name LIKE '%{customer_name}%' order by cust_id desc"
        query = f"SELECT c.cust_id as 客戶ID, c.cust_name as 客戶名, c.cust_bill as 代理, (SELECT cust_name FROM customer a WHERE  c.cust_bill = a.cust_id) AS 代理名, (SELECT COUNT(*) FROM xsom_refMC WHERE Xsom_cust = c.cust_id) AS 訂單數 FROM customer c WHERE  cust_bill = '{agent_code}' and cust_id like '%{customer_id}%' and cust_name LIKE '%{customer_name}%' order by 訂單數 desc"
        cursor.execute(query)
        query_results = cursor.fetchall()
        show_result_table = True
    if request.method == 'POST':
        agent_code = session['agent_code']
        customer_id = request.form.get('customer_id', '')
        customer_name = request.form.get('customer_name', '')
        # query = f"SELECT c.cust_id as 客戶ID, c.cust_name as 客戶名, c.cust_bill as 代理, (SELECT cust_name FROM customer a WHERE  c.cust_bill = a.cust_id) AS 代理名 FROM customer c where cust_bill is not null AND cust_bill = '{agent_code}' and cust_id like '%{customer_id}%' and cust_name LIKE '%{customer_name}%' order by cust_id desc"
        query = f"SELECT c.cust_id as 客戶ID, c.cust_name as 客戶名, c.cust_bill as 代理, (SELECT cust_name FROM customer a WHERE  c.cust_bill = a.cust_id) AS 代理名, (SELECT COUNT(*) FROM xsom_refMC WHERE Xsom_cust = c.cust_id) AS 訂單數 FROM customer c WHERE  cust_bill = '{agent_code}' and cust_id like '%{customer_id}%' and cust_name LIKE '%{customer_name}%' order by 訂單數 desc"
        cursor.execute(query)
        query_results = cursor.fetchall()
        show_result_table = True

    return render_template('customer.html', query_results=query_results,show_result_table = show_result_table)

@app.route('/search', methods=['GET', 'POST'])
def search(message=''):
    if 'agent_code' not in session:
        return redirect('/login')
    elif 'agent_code' in session:
        agent_code = session['agent_code']
    query_results = []
    show_result_table = True
    # if request.method == 'POST':
    agent_code = session['agent_code']
    customer_id = request.form.get('customer_id', '')
    if customer_id != '':
        session['customer'] = customer_id
    else:
        customer_id = session['customer']
    customer_name = request.form.get('customer_name', '')
    machine_number = request.form.get('machine_number', '')

    query_results = perform_search(agent_code, customer_id, customer_name, machine_number)
    show_result_table = True

    if message != '':
        flash(message)
        message = ''
    # print(session['customer'])
    return render_template('search.html', query_results=query_results, show_result_table=show_result_table)

def perform_search(agent_code, customer_id, customer_name, machine_number):
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()

    query = f"""
        SELECT Xsom_cust as 客戶ID, cust_bill as 代理, Xsom_nbr as 訂單號碼, Xsom_code as 機號, Xsom_part as 機台料號,
        Xsom_cmmt as 機種, Xsom_inch as 尺吋, Xsom__chr01 as 工單ID, Xsom_cust_name as 客戶名, Xsom_slspsn as 業務員,
        CONVERT(NVARCHAR(10), Xsom_acsh_date, 120) as 出貨日期, Xsom_desc1 as 說明一, xsom_feeder as 口數, (SELECT cust_name FROM customer a WHERE  c.cust_bill = a.cust_id) AS 代理名
        FROM customer c
        JOIN xsom_refMC ON c.cust_id = xsom_refMC.Xsom_cust
        WHERE cust_bill = ? AND c.cust_id LIKE ? AND c.cust_name LIKE ? AND xsom_code LIKE ? 
        ORDER BY xsom_code DESC
    """

    cursor.execute(query, (agent_code, f'%{customer_id}%', f'%{customer_name}%', f'%{machine_number}%'))
    query_results = cursor.fetchall()
    connection.close()

    return query_results

@app.route('/special_search', methods=['GET', 'POST'])
def special_search(message=''):
    if 'agent_code' not in session:
        return redirect('/login')
    elif 'agent_code' in session:
        agent_code = session['agent_code']
    query_results = []
    show_result_table = True
    # if request.method == 'POST':
    agent_code = session['agent_code']
    machine_number = request.form.get('machine_number', '')

    query_results = perform_search(agent_code, '', '', machine_number)
    show_result_table = True

    session['sp_inq'] = True
    session['customer'] = session['agent_code']
    return render_template('special_search.html', query_results=query_results, show_result_table=show_result_table)


@app.route('/component/<machine_number>', methods=['GET', 'POST'])
def component(machine_number, message= ''):
    if 'agent_code' not in session:
        return redirect('/login')
    else:
        agent = session['agent_code']
    bom_rows = []
    part_rows = []
    if (request.method == 'POST')&(machine_number==''):
        machine_number = request.form.get("machine_number", default='')

    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()
    query = f"SELECT sbom_code,sbom_lot,sbom_comp,sbom_desc,sbom_group,sbom_qty_per,sbom_par,sbom_code_par,sbom_desc1,sbom_desc2,sbom_desc3,sbom_desc4 from sbom_det WHERE sbom_code = '{machine_number}' order by sbom_code_par"
    cursor.execute(query)
    data = cursor.fetchall()
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
    try:
        detail = perform_search(agent,'','',machine_number)[0]
    except:
        return redirect('/login')
    # print(detail)
    # print(grouped_parts)
    connection.close()
    if message != '':
        flash(message)
        message = ''
    return render_template('machine.html', bom_rows=bom_rows, part_rows=part_rows, machine_number=machine_number,grouped_parts=grouped_parts,detail=detail)

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
        return [result,"Index.html"]
    else:
        return [result,result+"_Index.html"]


@app.route('/link/<machine_number>')
def link(machine_number):
    folder_detail = get_machine_file_name(machine_number)
    inner_forder = folder_detail[0]
    manual_file_name = folder_detail[1]
    machine_folder_path = os.path.join("\\\\77.0.0.134\\cd_output(mis)\\code", machine_number)
    inner_folder_path = os.path.join("\\\\77.0.0.134\\cd_output(mis)\\code", machine_number,inner_forder)
    # 如果機號資料夾中沒有 tabs.css 文件，就將其複製到機號資料夾中
    # print(inner_folder_path)
    if not os.path.exists(os.path.join(inner_folder_path, 'tabs.css')):
        try:
            shutil.copy("\\\\77.0.0.134\\cd_output(mis)\\code\\BuildCss\\tabs.css", inner_folder_path)
        except:
            print("copy failed")
            pass
    manual_path = os.path.join(machine_folder_path, manual_file_name)
    # print("manual path:",manual_path)
    
    # 文件名為空或找不到檔案
    if not os.path.exists(manual_path):
        print("can't find manual path")
        manual_file_name = machine_number + "_Index.html"
        manual_path = os.path.join(machine_folder_path, manual_file_name)
        if not os.path.exists(manual_path):
            manual_file_name = "Index.html"
            manual_path = os.path.join(machine_folder_path, manual_file_name)
        # return send_file(manual_path)
    # print(manual_file_name)
    # a = send_from_directory("\\\\77.0.0.134\\cd_output(mis)\\code", machine_number)
    # a = send_from_directory(machine_folder_path, machine_file_name)
    redirect_url = f'/code/{machine_number}/{manual_file_name}'
    return redirect(redirect_url)
    # return render_template('manual.html',manual_path=manual_path,machine_number= machine_number)

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

@app.route('/receive_data', methods=['POST'])
def receive_data():
    if request.method == 'POST':
            if 'agent_code' in session:
                agent = session['agent_code']
            customer = session['customer']
            datas = request.get_json()  # 獲取前端發送的JSON資料
            connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
            cursor = connection.cursor()
            cursor.execute(f"SELECT TOP 1 {'inq_num'} FROM {'inq_mstr'} ORDER BY {'inq_summitdate'} DESC")
            latest_num = cursor.fetchone()
            if latest_num:
                # 若已有資料則在舊的編號上+1
                new_num = int(latest_num[0][2:]) + 1
            else:
                # 若無主檔資料則設為初始值
                new_num = 1
            new_num = f'Q2{new_num:06}'

            cart = session.get('cart')
            if cart is None:
                cart = {}

            data = datas['data']
            note = datas['note']
            for i in range(len(data)):
                machine_number = data[i]['機號']
                query = f"SELECT Xsom_cust FROM Xsom_refMC WHERE Xsom_code = '{machine_number}'"
                cursor.execute(query)
                cust = cursor.fetchone()[0]
                data[i]['客戶'] = cust
            
            if(session['sp_inq']):
                cust = session['agent_code']
            current_datetime = datetime.datetime.now()
            formatted_date = current_datetime.strftime('%Y-%m-%d')
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

            print(agent, cust, machine_number, formatted_date, formatted_datetime)
            # Insert到主檔資料表
            cursor.execute("INSERT INTO inq_mstr (inq_num, inq_bill, inq_cust, inq_createdate, inq_summitdate, inq_note) "
                           +f"VALUES ('{new_num}', '{agent}', '{cust}', CAST('{formatted_date}' AS DATE), CAST('{formatted_datetime}' AS DATETIME), N'{note}')")
            # 遞迴資料內容並逐一插入table
            count = 0
            for i in range(len(data)):
                if data[i]['機台用量'] in ["","None"]:
                    data[i]['機台用量'] = None
                if data[i]['訂購量'] in ["","None"]:
                    data[i]['訂購量'] = None
                inq_item = data[i]['項次']
                inq_comp = data[i]['詢價料號']
                inq_mach_qty = data[i]['機台用量']
                inq_order_qty = data[i]['訂購量']
                inq_type = data[i]['類型']
                if inq_type != '零件包內零件':
                    count += 1
                inq_code = data[i]['機號']
                # inq_price = row['詢價金額']
                # print(new_num,inq_item, inq_comp, inq_mach_qty, inq_order_qty, inq_type, inq_code)
                cursor.execute("INSERT INTO inq_det (inq_det_num, inq_item, inq_comp, inq_mach_qty, inq_order_qty, inq_type, inq_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (new_num,inq_item, inq_comp, inq_mach_qty, inq_order_qty, inq_type, inq_code))
                connection.commit()
            
            cart[customer] = []
            # print("cart now:",cart)
            session['cart'] = cart
            'Data submitted successfully'
            message = str(count) + "筆資料詢價成功"
            
            return list_inquiries(message)

@app.route('/add_to_cart', methods=['GET', 'POST'])
def add_to_cart():
    if 'agent_code' not in session:
        return redirect('/login')
    else:
        agent = session.get('agent_code')
    customer = session.get('customer')
    if request.method == 'POST':
        selected_data_json = request.form.get('selected_data', '[]')
        selected_data = json.loads(selected_data_json)
    if len(selected_data) > 0:
        machine_number = selected_data[0]['sbom_code']
        count = 0
        for i in range(len(selected_data)):
            if selected_data[i]['sbom_code'] == '':
                selected_data[i]['sbom_code'] = machine_number
                selected_data[i]['type'] = '零件包內零件'
            elif selected_data[i]['sbom_material'] == '':
                selected_data[i]['type'] = '零件包'
                count += 1
            else:
                selected_data[i]['type'] = '一般零件'
                count += 1
            # selected_data[i]['sbom_desc'] = selected_data[i]['sbom_desc'].split(' <br> ')
            selected_data[i]['sbom_desc'] = str(selected_data[i]['sbom_desc']).split(' <br> ')
            for j in range(len(selected_data[i]['sbom_desc'])):
                selected_data[i]['sbom_desc'][j] = selected_data[i]['sbom_desc'][j].strip(' ')
        cart = session.get('cart')
        if cart is None:
            cart = {}
        if customer not in cart:
            cart[customer] = []
        
        cart[customer].append(selected_data)
        # print("add to cart:",cart)
        session['cart'] = cart
        message = str(count) + '筆資料已加入購物車'
        return component(machine_number=machine_number,message=message)
    else:
        return component(machine_number=machine_number,message="未勾選資料!")

@app.route('/show_cart', methods=['GET', 'POST'])
def show_cart():
    cart = session.get('cart')
    customer = session.get('customer')
    selected_data = []
    if cart is None:
        cart = {}
    if customer not in cart:
        pass
    else:
        for i in cart[customer]:
            for j in i:
                selected_data.append(j)
    return render_template('cart.html',cart=cart,selected_data=selected_data)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    data = json.loads(request.data)  # 接收AJAX POST請求中的購物車數據
    cart = session.get('cart')
    customer = session.get('customer')
    for i in range(len(data)):
        data[i]['sbom_desc'] = str(data[i]['sbom_desc']).split('<br>')
        for j in range(len(data[i]['sbom_desc'])):
            data[i]['sbom_desc'][j] = data[i]['sbom_desc'][j].strip(" ")
        print(data[i]['sbom_desc'])
    cart[customer] = [data]
    session['cart'] = cart  # 更新購物車內容
    # print("update cart:",session['cart'])
    return jsonify({'message': '購物車已更新'})

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    # session.pop('cart', [])
    cart = session.get('cart')
    customer = session.get('customer')
    cart[customer] = []
    session['cart'] = cart
    return '購物車已清空'

@app.route('/list_inquiries')
def list_inquiries(message=''):
    if 'agent_code' not in session:
        return redirect('/login')
    else:
        agent = session['agent_code']
    # 在此處編寫代碼來檢索代理商的所有詢價紀錄（inq_mstr資料表）
    # 並根據詢價狀態設置狀態為「詢價中」或「報價完成」。
    # 示例詢價紀錄列表（代碼需要替換成實際的查詢和設置狀態邏輯）
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()
    cursor.execute(f"SELECT inq_num as 單號, inq_bill as 代理 ,(SELECT cust_name FROM customer WHERE cust_id = inq_bill) as 代理名稱, cust_id as 客戶ID, cust_name as 客戶名稱,  inq_summitdate as 詢價日 ,inq_completedate as 完成日, inq_note as 備註 from inq_mstr join customer on inq_mstr.inq_cust = customer.cust_id WHERE inq_bill = '{agent}' ORDER BY inq_summitdate DESC")
    inquiries = cursor.fetchall()
    if message != '':
        flash(message)
    return render_template('list_inquiries.html', inquiries=inquiries)

@app.route('/view_inquiry/<inquiry_id>', methods=['GET'])
def view_inquiry(inquiry_id):
    if 'agent_code' not in session:
        return redirect('/login')
    else:
        agent = session['agent_code']

    # 以 inquiry_id 來識別。
    connection = pyodbc.connect(f'DRIVER=SQL Server;SERVER={server};DATABASE={database};UID={username};PWD={password}')
    cursor = connection.cursor()
    cursor.execute(f"SELECT  inq_item as 項次, inq_comp as 料號, inq_mach_qty as 機台用量, inq_order_qty as 訂購量, inq_inq_price as 詢價金額 ,inq_type as 類型, inq_code as 機號 FROM inq_det WHERE inq_det_num = '{inquiry_id}' order by CAST(inq_item AS FLOAT)")
    inquiry_details = cursor.fetchall()
    cursor.execute(f"SELECT inq_num as 單號, inq_bill as 代理 ,(SELECT cust_name FROM customer WHERE cust_id = inq_bill) as 代理名稱, cust_id as 客戶ID, cust_name as 客戶名稱, inq_summitdate as 詢價日 ,inq_completedate as 完成日,inq_note as 備註 from inq_mstr join customer on inq_mstr.inq_cust = customer.cust_id WHERE inq_bill = '{agent}' AND inq_num = '{inquiry_id}'")
    basic = cursor.fetchall()
    return render_template('view_inquiry.html', inquiry_details=inquiry_details,inquiry_id=inquiry_id,basic=basic)


@app.route('/')
def root():
    session['cart'] = {}
    session['customer'] = None
    session['sp_inq'] = False
    return redirect('/home')

app.logger.setLevel(logging.ERROR)  # 只記錄錯誤信息
# if __name__ == '__main__':
#     app.run(debug=False,port=8071,host='0.0.0.0')
if __name__ == '__main__':
    app.run(debug=True)
