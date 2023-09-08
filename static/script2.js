$(document).ready(function() {
    // 點擊展開/收縮按鈕切換表格和高度
    function toggleTable(buttonId, tableId, divId) {
        $(buttonId).click(function() {
            $(tableId).toggle();
            var myDiv = document.getElementById(divId);
            var currentHeight = myDiv.style.maxHeight;
            if (currentHeight === "12vh") {
                myDiv.style.maxHeight = 70 + "vh";
            } else {
                myDiv.style.maxHeight = 12 + "vh";
            }
        });
    }
    toggleTable('#toggleButton1', '#bomTable', 'bomdiv');
    toggleTable('#toggleButton2', '#partTable', 'bomdiv2');

    // 點擊搜尋按鈕提交表單
    $('#searchButton').click(function() {
        $('#searchForm').submit();
    });

    // 處理匯出 CSV 按鈕點擊事件
    $('.export-csv-button').click(function() {
        var table = $(this).closest('.table');
        var rows = table.find('tr:has(td)').toArray().map(function(row) {
            return $(row).find('td').toArray().map(function(cell) {
                return $(cell).text().trim();
            }).join(',');
        }).join('\n');
        
        var header = table.find('th').toArray().map(function(cell) {
            return $(cell).text().trim();
        }).join(',');
        rows = header + '\n' + rows;
    
        var machineNumber = table.find('tr:eq(1) td:first-child').text().trim();
        var filenamePrefix = machineNumber + '_' + table.find('h2').text().trim();
        var filename = filenamePrefix + '.csv';
    
        var blob = new Blob([new Uint8Array([0xEF, 0xBB, 0xBF]), rows], { type: 'text/csv;charset=utf-8;' });
    
        var link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', filename);
        link.style.display = 'none';
    
        document.body.appendChild(link);
        link.click();
    
        document.body.removeChild(link);
    });
    
    // 處理欲購數量欄位輸入框值變化
    $('input[name="purchase_quantity"]').on('input', function() {
        // 獲取輸入的欲購數量
        var purchaseQuantity = parseFloat($(this).val());

        // 獲取所在行的勾選框
        var checkbox = $(this).closest('tr').find('.purchase_checkbox');

        // 根據輸入框的值來設置勾選框的狀態
        checkbox.prop('checked', !isNaN(purchaseQuantity) && purchaseQuantity > 0);

        // 獲取祖名，用於同步其他零件的輸入框
        var partGroupName = $(this).closest('tr').find('.qtyinput').attr('id');
        if (partGroupName){
            var partGroupName = $(this).closest('tr').find('.qtyinput').attr('id').split('_')[2]; // 获取组名
            // 找到所有同一組的零件的行並更新輸入框內的值和勾選狀態
            $('input[id^="part_quantity_' + partGroupName + '"]').each(function() {
                // 獲取零件的單位數量
                var qtyPer = parseFloat($(this).closest('tr').find('td:eq(7)').text());
                if (!isNaN(purchaseQuantity) && !isNaN(qtyPer) && purchaseQuantity>0) {
                    $(this).val((purchaseQuantity * qtyPer).toFixed(2));
                    // 設置零件格勾選
                    var partCheckbox = $(this).closest('tr').find('.purchase_checkbox');
                    partCheckbox.prop('checked', true);
                } else {
                    $(this).val('');
                    // 取消零件格子勾選
                    var partCheckbox = $(this).closest('tr').find('.purchase_checkbox');
                    partCheckbox.prop('checked', false);
                    }
            });
        }
    });

    // 監聽購買欄位的變化事件
    $('input[name="purchase_checkbox"]').on('change', function() {
        // 如果勾選了購買，但未輸入欲購數量，則自動填入 1
        if ($(this).is(':checked')) {
            var quantityInput = $(this).closest('tr').find('input[name="purchase_quantity"]');
            if (quantityInput.val().trim() === '') {
                quantityInput.val('1');
            }
            var purchaseQuantity = parseFloat(quantityInput.val())
            var partGroupName = quantityInput.closest('tr').find('.qtyinput').attr('id');
            if (partGroupName){
                var partGroupName = quantityInput.closest('tr').find('.qtyinput').attr('id').split('_')[2]; // 获取组名
                // 找到所有同一組的零件的輸入框並更新值和勾選狀態
                $('input[id^="part_quantity_' + partGroupName + '"]').each(function() {
                    // 獲取每個零件的數量
                    var qtyPer = parseFloat($(this).closest('tr').find('td:eq(7)').text());
                    $(this).val((purchaseQuantity * qtyPer).toFixed(2));
                    // 設置零件勾選
                    var partCheckbox = $(this).closest('tr').find('.purchase_checkbox');
                    partCheckbox.prop('checked', true);
                    
                });
            }
        }
        else{
            var quantityInput = $(this).closest('tr').find('input[name="purchase_quantity"]');
            var partGroupName = quantityInput.closest('tr').find('.qtyinput').attr('id');
            if (partGroupName){
                var partGroupName = quantityInput.closest('tr').find('.qtyinput').attr('id').split('_')[2]; // 获取组名
                // 找到所有同一組的零件的輸入框並更新值和勾選狀態
                $('input[id^="part_quantity_' + partGroupName + '"]').each(function() {
                    // 獲取每個零件的數量
                    $(this).val('');
                    // 設置零件格勾選
                    var partCheckbox = $(this).closest('tr').find('.purchase_checkbox');
                    partCheckbox.prop('checked', false);
                    
                });
            }
        }
    });

    // 處理點擊篩選按鈕事件
    $('#filter-checkbox').change(function() {
        try {
            // 如果篩選框被勾選
            if ($(this).is(':checked')) {
                // 隱藏未勾選的行
                $('input[name="purchase_checkbox"]').not(':checked').closest('tr').hide();
            } else {
                // 顯示所有行
                $('tr').show();
            }
        } catch (error) {
            console.error("Error in filter-checkbox change event:", error);
        }
    });
    // 確認詢價單按鈕事件
    $('#checkout-button').click(function() {
        var selectedRowsData = [];
    
        // 遞迴所有以勾選的行
        $('input[name="purchase_checkbox"]:checked').closest('tr').each(function() {
            var rowData = {
                sbom_par: $(this).find('td:eq(1)').text(),
                sbom_code: $(this).find('td:eq(2)').text(),
                sbom_lot: $(this).find('td:eq(3)').text(),
                sbom_material: $(this).find('td:eq(4)').text(),
                sbom_desc: $(this).find('td:eq(5)').text(),
                sbom_group: $(this).find('td:eq(6)').text(),
                sbom_qty_per: $(this).find('td:eq(7)').text(),
                purchase_quantity: $(this).find('td:eq(8)').find('input').val(),
            };
            selectedRowsData.push(rowData);
        });
    
        // 將以勾選的數據轉換為JSON字串，並設置為隱藏表單內的值
        $('#selected_data').val(JSON.stringify(selectedRowsData));
    
        // 提交表單，路徑導到confirmation_form
        $('#confirmation_form').submit();
    });
    
    // 恢復零件包內零件的輸入值
    function restoreSubPartsInputValues() {
        $('input[name="purchase_checkbox"]').each(function() {
            if ($(this).is(':checked')) {
                $(this).prop('checked', false);
                $(this).prop('checked', true);
            var quantityInput = $(this).closest('tr').find('input[name="purchase_quantity"]');
            if (quantityInput.val().trim() === '') {
                quantityInput.val('1');
            }
            var purchaseQuantity = parseFloat(quantityInput.val())
            var partGroupName = quantityInput.closest('tr').find('.qtyinput').attr('id');
            if (partGroupName){
                var partGroupName = quantityInput.closest('tr').find('.qtyinput').attr('id').split('_')[2]; // 獲取組名
                // 找到所有同一組的零件的輸入框並更新值和勾選狀態
                $('input[id^="part_quantity_' + partGroupName + '"]').each(function() {
                    // 獲取每個零件的數量
                    var qtyPer = parseFloat($(this).closest('tr').find('td:eq(7)').text());
                    $(this).val((purchaseQuantity * qtyPer).toFixed(2));
                    // 設置零件格勾選
                    var partCheckbox = $(this).closest('tr').find('.purchase_checkbox');
                    partCheckbox.prop('checked', true);
                    
                });
            }
            }
        });
    }

    // 頁面載入時恢復零件包內零件的輸入值
    restoreSubPartsInputValues();
    
    
});
20
function openManual(machine_number) {
    // 使用AJAX向後端發送請求以獲取machine_file_name
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var machine_file_name = xhr.responseText;
            
            // 使用file:// URL方式打開檔案
            var fileURL = "file://77.0.0.134/cd_output(mis)/code/" + machine_number + "/" + machine_file_name;
            // 在新窗口中打開檔案
            window.open(fileURL);
        }
    };
    
    xhr.open("GET", "/get_machine_file_name/" + machine_number, true);
    xhr.send();
}

function searchTable() {
    var keyword = document.getElementById('keyword').value.toLowerCase();
    var rows = document.querySelectorAll('#bomTable tr');

    var parentToDisplay = new Set(); // 用于存储要显示的父件/零件包字段

    // 第一次循环：筛选出包含关键字的行并记录零件包内零件行的父件
    rows.forEach(function (row, index) {
        var text = row.innerText.toLowerCase();
        var shouldShow = text.includes(keyword) || keyword === '';

        if (index === 0) {
            row.style.display = 'table-row'; // 保持表格头部始终显示
        } else {
            var tdMachine = row.querySelector('td:nth-child(3)'); // 机号列
            var tdParent = row.querySelector('td:nth-child(2)'); // 父件/零件包列
            var parentText = tdParent ? tdParent.textContent.trim() : '';

            if (tdMachine && tdMachine.textContent.trim() === '') {
                // 处理零件包内零件
                if (shouldShow) {
                    parentToDisplay.add(parentText);
                    row.style.display = 'table-row';
                } else {
                    row.style.display = 'none';
                }
            } else {
                // 处理其他行
                row.style.display = shouldShow ? 'table-row' : 'none';
            }
        }
    });

    // 第二次循环：显示与记录下来的父件相同的行
    rows.forEach(function (row, index) {
        if (index > 0) {
            var tdParent = row.querySelector('td:nth-child(2)'); // 父件/零件包列
            var parentText = tdParent ? tdParent.textContent.trim() : '';

            if (parentToDisplay.has(parentText)) {
                row.style.display = 'table-row';
            }
        }
    });
}



function clearFilter() {
    // 清除输入框的值
    document.getElementById('keyword').value = '';

    // 触发表格重新筛选
    searchTable();
}


