$(document).ready(function() {
    $('table').on('click', '.clickable-row', function() {
        window.location = $(this).data('href');
        // window.open($(this).data('href'));
        // var customer_id = $(this).data('customer-id'); // 获取customer_id
        // $.ajax({
        //     type: 'POST',  // 或者 'GET'，取决于您的需求
        //     url: '/search',  // 指向您的'/search'路由
        //     data: {customer_id: customer_id}, // 将customer_id发送到后端
        //     success: function(response) {
        //         // 处理成功响应，如果需要的话
        //         window.location = $(this).data('href');
        //     }
        // });
    });

    $('table').on('click', 'th[data-sort]', function() {
        var column = $(this).data('sort');
        var table = $(this).closest('table');
        var currentSort = $(this).hasClass('asc') ? 'asc' : 'desc';

        // 切換排序方向
        if (currentSort === 'asc') {
            $(this).removeClass('asc').addClass('desc');
        } else {
            $(this).removeClass('desc').addClass('asc');
        }

        var rows = table.find('tbody > tr').toArray().sort(compareCells(column, currentSort));
        table.find('tbody').empty().append(rows);
    });
    
});
// $(document).ready(function () {
//     var $table = $(".table");

//     $table.scroll(function () {
//         if ($table.length) {
//             var tableScrollTop = $table.scrollTop();
//             if (tableScrollTop > 0) {
//                 $table.addClass("scrolled");
//             } else {
//                 $table.removeClass("scrolled");
//             }
//         }
//     });
// });
function compareCells(column, sortDirection) {
    console.log("sortDirection: " + sortDirection);

    return function(a, b) {
        var valA = $(a).find('td[data-column="' + column + '"]').text();
        var valB = $(b).find('td[data-column="' + column + '"]').text();
        var result = $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.localeCompare(valB);

        return sortDirection === 'asc' ? result : -result;
    };
}
