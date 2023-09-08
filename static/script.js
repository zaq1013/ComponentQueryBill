$(document).ready(function() {
    $('table').on('click', '.clickable-row', function() {
        window.location = $(this).data('href');
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

function compareCells(column, sortDirection) {
    console.log("sortDirection: " + sortDirection);

    return function(a, b) {
        var valA = $(a).find('td[data-column="' + column + '"]').text();
        var valB = $(b).find('td[data-column="' + column + '"]').text();
        var result = $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.localeCompare(valB);

        return sortDirection === 'asc' ? result : -result;
    };
}
