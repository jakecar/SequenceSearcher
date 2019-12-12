$(document).ready(function() {
    var table;
    refreshData();

    $("#sequence_form").submit(function(e) {
        e.preventDefault();
        query = e.target.elements[0].value;
        $('textarea').val('');
        $.post("/align", {
                query: query
            })
            .done(function() {
                refreshData();
            })
            .fail(function(data) {
                alert(data.responseText);
            });
    });

    function refreshData() {
        $.get("/all-alignments")
            .done(function(data) {
                data = JSON.parse(data);
                data = data.map(alignment => {
                    return {
                        matched_protein: alignment[0],
                        query: alignment[1],
                        match_pos: alignment[2]
                    }
                });

                if (table) {
                    table.fnDestroy();
                }

                table = $('#alignmentResults').dataTable({
                    info: false,
                    searching: false,
                    paging: false,
                    data: data,
                    columns: [{
                            data: 'matched_protein'
                        },
                        {
                            data: 'query'
                        },
                        {
                            data: 'match_pos'
                        }
                    ]
                });
                console.log(data);
            });
    }
    var $loading = $('svg').hide();
    $(document)
        .ajaxStart(function() {
            $loading.show();
        })
        .ajaxStop(function() {
            $loading.hide();
        });
});
