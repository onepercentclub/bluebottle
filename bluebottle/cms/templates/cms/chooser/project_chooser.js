function (modal) {
    console.info('test');


    function ajaxifyLinks (context) {
        $('.listing a', context).click(function() {
            modal.loadUrl(this.href);
            return false;
        });

        $('.pagination a', context).click(function() {
            var page = this.getAttribute("data-page");
            setPage(page);
            return false;
        });
    }

    function search() {
        fetchResults({
            q: $('#id_q').val(),
        });
        return false;
    }

    function fetchResults(requestData) {
        $.ajax({
            url: '{% url 'cms:project_chooser' %}',
            data: requestData,
            success: function(data, status) {
                $('#project-results').html(data);
                ajaxifyLinks($('#project-results'));
            }
        });
    }

    function setPage(page) {
        params = {p: page};

        if ($('#id_q').val().length){
            params['q'] = $('#id_q').val();
        }

        fetchResults(params);
        return false;
    }

    $('form.image-search', modal.body).submit(search);

    $('#id_q').on('input', function() {
        clearTimeout($.data(this, 'timer'));
        var wait = setTimeout(search, 200);
        $(this).data('timer', wait);
    });

    ajaxifyLinks(modal.body);
}
