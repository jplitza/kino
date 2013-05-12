function movie_info() {
    var movie_id = this.href.match(/\d+$/)[0]
    var movie_info = $('#movie_info_' + movie_id);
    if(movie_info.length == 0) {
        var link = this;
        $.getJSON( this.href, {}, function(data, textStatus, jqXHR) {
            var tr = $('<tr>', {id: 'movie_info_' + movie_id, class: 'movie_info'})
                .append($('<td>', {colspan: 4})
                        .append($('<div>', {class: 'movie_info_container'})
                                .append($('<img>', {class: 'poster', src: /\Wpreview="(.*?)"\W/.exec(data['thumb'])[1]}))
                                .append($('<dl>')
                                        .append($('<dt>').append('Originaltitel'))
                                        .append($('<dd>').append(data['orig_name']))
                                        .append($('<dt>').append('Zusammenfassung'))
                                        .append($('<dd>').append(data['description']))
                                        .append($('<dt>').append('Details'))
                                        .append($('<dd>')
                                                .append($('<a>', {href: 'http://www.imdb.com/title/' + data['imdb_id'] + '/'})
                                                        .append('IMDb')
                                                )
                                        )
                                )
                        )
                );
            tr.insertAfter(link.parentNode.parentNode);
            tr.children().children().show('blind');
        });
    } else
        movie_info.find('.movie_info_container').hide({effect: 'blind', complete: function() { movie_info.remove() }});
    return false;
}

function toggle_checked() {
    var checkbox = $(this).parent().find('input[type=checkbox]');
    checkbox.prop('checked', !checkbox.prop('checked'));
    checkbox.change();
}

function checkbox_change() {
    this.parentNode.parentNode.className = this.checked? 'voted' : '';
}

function stop_propagation(ev) {
    ev.stopPropagation();
}

$(function() {
    $('#movie_name').autocomplete({
        source: function(request, response) {
            $.getJSON( "/find_movie", {
                term: request.term
            }, function(data, textStatus, jqXHR) {
                response($.grep(data, function(elem, index) {
                    elem.duplicate = false;
                    $('#movies input[type=checkbox]').each(function() {
                        if(elem.id == this.value) {
                            elem.duplicate = true;
                            return false;
                        }
                    });
                    return elem.duplicate;
                }, true))
            });
        },
        minLength: 2,
        select: function( event, ui ) {
            $('<tr>', {class: 'voted'})
                .append($('<td>')
                        .append($('<input>', {type: 'checkbox', name: 'movies[]', id: "movie_" + ui.item.id, value: ui.item.id, checked: 'checked'}).change(checkbox_change).click(stop_propagation))
                )
                .append($('<td>').append('0'))
                .append($('<td>').append($('<a>', {href: '/movie/' + ui.item.id, class: 'movie_info'}).append('Info').click(movie_info)))
                .append($('<td>')
                        .append($('<label>', {for: 'movie_' + ui.item.id})
                                .append(ui.item.value)
                        )
                )
            .appendTo($('#movies tbody')).find('td').click(toggle_checked);
            $('#movie_name').val('');
            return false;
        }
    });
    $('a.movie_info').click(movie_info);
    $('#movies tbody input[type=checkbox]').change(checkbox_change).click(stop_propagation);
    $('#movies tbody label').click(function(ev) {
        ev.stopPropagation();
    });
    $('#movies tbody td').click(toggle_checked);
});
