$(document).ready(function() {
    // 找到父件/零件包字段為空的行並添加分類
    $('tr').each(function() {
        var sbom_par = $(this).find('td:eq(0)').text(); 
        if (sbom_par.trim() === '') {
            $(this).addClass('empty-row');
        }
    });
    /// 處理欲購數量 輸入框值變動的狀況
    $('input[name="purchase_quantity"]').on('input', function() {
        // 獲取輸入的欲購數量
        var purchaseQuantity = parseFloat($(this).val());
        // 獲取組名，用於同步其他零件的輸入框
        var partGroupName = $(this).closest('tr').find('.editable-quantity').attr('id'); 
        if (partGroupName){ 
            var partGroupName = $(this).closest('tr').find('.editable-quantity').attr('id').split('_')[2]; // 获取组名
            // 找到所有同一組的零件的輸入框並更新值和勾選狀態
            $('td[id^="part_quantity_' + partGroupName + '"]').each(function() {
                // 獲取每個零件的數量
                var qtyPer = parseFloat($(this).closest('tr').find('td:eq(6)').text());
                if (isNaN(qtyPer)){
                    qtyPer = 0;
                }
                if (!isNaN(purchaseQuantity) && !isNaN(qtyPer)) {
                    $(this).text((purchaseQuantity * qtyPer).toFixed(2));
                }
            });
        }
        updateCart(getCartData());
    });
    $('input[name="normal_quantity"]').on('input', function() {
        updateCart(getCartData());
    });
    // 刪除按鈕功能
    $('.delete-row').on('click', function() {
        const row = $(this).closest('tr'); // 獲取所在行
        const sbom_par = row.find('td:eq(3)').text().trim(); // 獲取父件/零件包內容
        // 如果刪除的行是零件包行 (機號欄位為空的行)，則刪除其底下屬於期的零件包內零件
        if (sbom_par === '') {
            row.nextUntil('tr:has(td:eq(2):not(:empty))').remove();
        }

        row.remove(); // 从表格中移除该行
        updateCart(getCartData());
    });

    
    
    // 進行詢價按鈕
    $('#inquiry-button').on('click', function() {
        // 獲取表格元素
        const table = document.querySelector('#confirmation_detail table');

        // 創建新表格的數據
        const newTableData = [];
        const note = document.querySelector('#note').value;
        console.log(note)
        // 定義項次初始值
        let itemNumber = 0;
        let subItemNumber = 0;
        let currentItem = "一般零件"; // 預設為一般零件
        // const machine_number = document.querySelector('#confirmation_detail table tr:not(.empty-row) td:nth-child(2)').textContent.trim();
        // 遞迴
        table.querySelectorAll('tr').forEach((row) => {
            const cells = row.querySelectorAll('td');

            if (cells.length >= 8) {
                // 獲取父件/零件包案可選材料字段的文本內容
                const sbom_par = cells[0].textContent.trim();
                const sbom_material = cells[3].textContent.trim();

                // 確定項目類型
                let itemType = "";
                if (sbom_material === "") {
                    itemType = "零件包";
                    // const sbom_lot_temp = cells[2].textContent.trim();
                } else if (cells[2].textContent.trim() === "") {
                    itemType = "零件包內零件";
                    // cells[2] = sbom_lot_temp;
                } else {
                    itemType = "一般零件";
                }

                // 更新項次
                if (itemType === "一般零件") {
                    // 如果是一般零件則直接遞增主項次號
                    currentItem = "一般零件";
                    itemNumber += 1;
                    subItemNumber = 1;
                } else if (itemType === "零件包") {
                    // 如果是零件包，先遞增主項次號，並且將子號先設為0
                    currentItem = "零件包";
                    itemNumber += 1;
                    subItemNumber = 0;
                } else if (itemType === "零件包內零件") {
                    // 如果是零件包內零件，則遞增子項次號
                    currentItem = "零件包內零件";
                    subItemNumber += 1;
                }

                // 獲取欲購數量
                let purchase_quantity = 0;
                if (itemType === "零件包內零件" ) {
                    // 零件包內零件直接獲取文本值
                    purchase_quantity = parseFloat(cells[7].textContent.trim());
                } else {
                    // 一般零件及零件包則獲取輸入框的值
                    purchase_quantity = parseFloat(cells[7].querySelector('input.editable-quantity').value);
                }

                // 添加資料到rowData
                const rowData = {};
                rowData.項次 = generateItemNumber(currentItem, itemNumber, subItemNumber);
                rowData.詢價料號 = itemType === "零件包" ? sbom_par : sbom_material;
                rowData.機台用量 = cells[6].textContent.trim();
                rowData.訂購量 = purchase_quantity;
                rowData.詢價金額 = ""; 
                rowData.類型 = itemType;
                rowData.機號 = cells[1].textContent.trim();
                newTableData.push(rowData);
            }
        });

        const requestData = {
            data: newTableData,
            note: note
            // machine_number: machine_number
        };

        // 將rowData發送到Flask端
        fetch('/receive_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(data => {
            setTimeout(function() {
                // 跳轉至清單頁面
                window.location.href = '/list_inquiries';
            }, 500);
        })
        .then(response => response.json())
        .catch(error => {
            // 
            console.error('Error:', error);
            // window.location.href = '/search'
        });

    });
});

document.getElementById("cart-clear").addEventListener("click", function() {
    // 發送請求至flask端清空購物車
    fetch('/clear_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(function(response) {
        if (response.ok) {
            // 清除成功後，刷新購物車頁面
            window.location.reload(); 
        } else {
            console.error('清空失敗');
        }
    })
    .catch(function(error) {
        console.error('錯誤:', error);
    });
});


// 生成項次用函式
function generateItemNumber(itemType, itemNumber, subItemNumber) {
    if (itemType === "一般零件") {
        return itemNumber.toString();
    } else if (itemType === "零件包") {
        return itemNumber.toString();
    } else if (itemType === "零件包內零件") {
        return `${itemNumber}.${subItemNumber}`;
    }
}


// 定義一個函數，用於獲取購物車內容
function getCartData() {
    var cartData = [];
    // 獲取所有購物車表格中的行
    var cartRows = document.querySelectorAll('#confirmation_detail table tr');
    
    // 遍歷每一行，獲取購物車內容
    cartRows.forEach(function(row) {
        var cartItem = {};
        var columns = row.querySelectorAll('td');

        if (columns.length >= 8) {
            // 提取所需的資料
            cartItem.sbom_par = columns[0].textContent.trim();
            cartItem.sbom_code = columns[1].textContent.trim();
            cartItem.sbom_lot = columns[2].textContent.trim();
            cartItem.sbom_material = columns[3].textContent.trim();
            cartItem.sbom_desc = columns[4].innerHTML.replace(/\n/g, '').trim();
            cartItem.sbom_group = columns[5].textContent.trim();
            cartItem.sbom_qty_per = columns[6].textContent.trim();
            
            // 獲取購買數量，區分不同情況
            if (row.classList.contains('empty-row')) {
                // 零件包內零件行
                cartItem.type = '零件包內零件'
                cartItem.purchase_quantity = parseFloat(columns[7].textContent.trim());
            } else if (columns[7].querySelector('input.editable-quantity')) {
                // 一般零件行和零件包行
                cartItem.type = '零件包'
                cartItem.purchase_quantity = parseFloat(columns[7].querySelector('input.editable-quantity').value);
            } else if (columns[7].querySelector('input[name="normal_quantity"]')) {
                // 一般零件行（在一般零件行中，input 的 name 屬性為 "normal_quantity"）
                cartItem.type = '一般零件'
                cartItem.purchase_quantity = parseFloat(columns[7].querySelector('input[name="normal_quantity"]').value);
            } else {
                // 其他情況（可能是空行等）
                '一般零件'
                cartItem.purchase_quantity = 0;
            }

            // 將資料添加到購物車內容中
            cartData.push(cartItem);
        }
    });

    return cartData;
}

// 在用戶對購物車進行更改後，將購物車數據發送到後端
function updateCart(cartData) {
    fetch('/update_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(cartData)
    })
    .then(function(response) {
        if (response.ok) {
            console.log('購物車已更新');
            // 在此處執行頁面刷新或其他操作（如果需要）
        } else {
            console.error('更新購物車時出錯');
        }
    })
    .catch(function(error) {
        console.error('錯誤:', error);
    });
}
