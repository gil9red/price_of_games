
$.noty.defaults.theme = 'defaultTheme';
$.noty.defaults.layout = 'bottomRight';
$.noty.defaults.timeout = 6000;

function run_check() {
    $.ajax({
        url: "/run_check",
        method: "POST",
        success: function(data) {
            console.log(data);
//            console.log(JSON.stringify(data));

            let ok = data.status == 'ok';
            noty({
                text: data.text,
                type: ok ? 'success' : 'warning',
            });

            if (ok && data.data != null) {
                setTimeout(() => location.reload(true), 2000);
            }
        },

        error: function(data) {
            noty({
                text: 'На сервере произошла ошибка',
                type: 'error',
            });
        }
    });
}

$(document).ready(function() {
    // hide #back-top first
    $("#back-top").hide();

    // fade in #back-top
    $(function () {
        $(window).scroll(function () {
            if ($(this).scrollTop() > 250) {
                $('#back-top').fadeIn();
            } else {
                $('#back-top').fadeOut();
            }
        });

        // scroll body to 0px on click
        $('#back-top a').click(function () {
            $('body,html').animate({
                scrollTop: 0
            }, 800);
            return false;
        });
    });

    $('#switch_more_actions').prop('checked', false);
    $('#switch_more_actions').change(function(){
        $('#more_actions').toggle(this.checked);
    });
});

function set_visible_finished_game(visible) {
    $('#finished_game').toggle(visible);
}

function set_visible_finished_watched_game(visible) {
    $('#finished_watched_game').toggle(visible);
}

/**
 * Number.prototype.toMoney(n, x, s, c)
 *
 * Example: 12345678.9.toMoney(2, 3, ' ', ',')  // "12 345 678,90"
 *
 * @param integer n: length of decimal
 * @param integer x: length of whole part
 * @param mixed   s: sections delimiter
 * @param mixed   c: decimal delimiter
 */
Number.prototype.toMoney = function(n, x, s, c) {
    var re = '\\d(?=(\\d{' + (x || 3) + '})+' + (n > 0 ? '\\D' : '$') + ')';
    var num = this.toFixed(Math.max(0, ~~n));

    return (c ? num.replace('.', c) : num).replace(new RegExp(re, 'g'), '$&' + (s || ','));
};

/**
 *   Example: 12345678.9.toPrettyPrice()  // "12 345 678,90"
 */
function toPrettyPrice(num) {
    // 12345678.9 -> 12 345 678,90
    // 12345678   -> 12 345 678
    return num.toMoney(2, 3, ' ', ',').replace(/,00$/, '');
}

function update_total_price_all_tables() {
    let total_price_of_finished_game = 0;
    for (let row of window.finished_games) {
        if (row.price) {
            total_price_of_finished_game += row.price;
        }
    }

    let total_price_of_finished_watched_game = 0;
    for (let row of window.finished_watched_games) {
        if (row.price) {
            total_price_of_finished_watched_game += row.price;
        }
    }

    let pretty_total_price_of_finished_game = toPrettyPrice(total_price_of_finished_game);
    let pretty_total_price_of_finished_watched_game = toPrettyPrice(total_price_of_finished_watched_game);
    let sum_total = toPrettyPrice(total_price_of_finished_game + total_price_of_finished_watched_game);

    // Установка итого цен
    $('.total_price_finished_games').html(pretty_total_price_of_finished_game);
    $('.total_price_finished_games.add_ccy').html(pretty_total_price_of_finished_game + " руб.");

    $('.total_price_finished_watched_games').html(pretty_total_price_of_finished_watched_game);
    $('.total_price_finished_watched_games.add_ccy').html(pretty_total_price_of_finished_watched_game + " руб.");

    $('.sum_total_price_games.add_ccy').html(sum_total + " руб.");
}

function open_tab_with_steam_search_from_game_name(game_name) {
    let url = 'http://store.steampowered.com/search/?term=' + game_name;
    console.log(`open_tab_with_steam_search("${game_name}") -> ${url}`);

    window.open(url);
}

function open_tab_with_yandex_search_from_game_name(game_name) {
    let url = 'https://yandex.ru/yandsearch?text=' + game_name;
    console.log(`open_tab_with_yandex_search("${game_name}") -> ${url}`);

    window.open(url);
}

function open_tab_with_google_search_from_game_name(game_name) {
    let url = 'https://www.google.ru/#newwindow=1&q=' + game_name;
    console.log(`open_tab_with_google_search("${game_name}") -> ${url}`);

    window.open(url);
}

// Функция возвращает строку с статистикой: сколько всего игр, сколько имеют цены, и процент.
// Пример: (0 / 160 (0%))
function statistic_for_table(items) {
    let price_is_none_rows_number = 0;
    for (let row of items) {
        if (row == null) {
            price_is_none_rows_number++;
        }
    }
    let all_rows_number = items.length;
    let number_price_rows = all_rows_number - price_is_none_rows_number;
    let percent = all_rows_number > 0 ? (number_price_rows / all_rows_number * 100) : 0;

    // 99.065 -> 99.1
    percent = percent.toFixed(1);

    // 100.0 -> 100
    percent = percent.toString().replace('.0', '')

    return `(${number_price_rows} / ${all_rows_number} (${percent}%))`
}

function fill_statistics() {
    var statistic_1 = statistic_for_table(window.finished_games);
    var statistic_2 = statistic_for_table(window.finished_watched_games);

    $('.finished_game_statistic').html(statistic_1);
    $('.finished_watched_game_statistic').html(statistic_2);

    // Добавление статистики о количестве игр в таблицах
    $('.number_finished_games').text(finished_games.length + " " + statistic_1);
    $('.number_finished_watched_games').text(finished_watched_games.length + " " + statistic_2);
    $('.sum_number_games').text(finished_games.length + finished_watched_games.length);
}

function price_render(data, type, row, meta) {
    if (data != null) {
        return data;
    }

    // Для display и filter показываем текстом что цены нет и добавляем картинки для поиска
    if (type === 'display' || type === 'filter') {
        // Добавление иконки для поиска игры в стиме
        let img_steam_search = $(`<img src="${IMG_STEAM_SEARCH}" width="16" height="16"/>`);
        img_steam_search.attr('onclick', `open_tab_with_steam_search_from_game_name("${row.name}")`);
        img_steam_search.attr('alt', 'steam');
        img_steam_search.attr('title', 'Поиск игры в стиме');

        // Добавление иконки для поиска игры в гугле
        let img_google_search = $(`<img src="${IMG_GOOGLE_SEARCH}" width="16" height="16"/>`);
        img_google_search.attr('onclick', `open_tab_with_google_search_from_game_name("${row.name}")`);
        img_google_search.attr('alt', 'google');
        img_google_search.attr('title', 'Поиск игры в гугле');

        // Добавление иконки для поиска игры в яндексе
        let img_yandex_search = $(`<img src="${IMG_YANDEX_SEARCH}" width="16" height="16"/>`);
        img_yandex_search.attr('onclick', `open_tab_with_yandex_search_from_game_name("${row.name}")`);
        img_yandex_search.attr('alt', 'yandex');
        img_yandex_search.attr('title', 'Поиск игры в яндексе');

        let buttons_div = $('<div style="display: inline-block; float: right;"></div>');
        buttons_div.append(img_steam_search);
        buttons_div.append("&nbsp;");
        buttons_div.append(img_google_search);
        buttons_div.append("&nbsp;");
        buttons_div.append(img_yandex_search);

        return '<div>Цена не задана</div>' + buttons_div.html();
    }

    // Для сортировки возвращаем null
    return data;
}

function append_date_render(data, type, row, meta) {
    if (type === 'display' || type === 'filter') {
        return row.append_date;
    }

    return row.append_date_timestamp;
}

function fill_table(table_selector, total_class, items) {
    if ($.fn.dataTable.isDataTable(table_selector)) {
        $(table_selector).DataTable()
            .clear()
            .rows.add(items)
            .draw();
        return;
    }

    let table = $(table_selector).DataTable({
        // Теперь поле поиска будет занимать 9/12 места, вместо 6/12
        dom: "<'row'<'col-sm-12 col-md-3'l><'col-sm-12 col-md-9'f>>",

        data: items,
        lengthMenu: [ [10, 25, 50, -1], ["10 записей", "25 записей", "50 записей", "Все записи"] ],
        columns: [
            { title: "Название", data: 'name' },
            { title: "Дата добавления", data: 'append_date', render: append_date_render },
            { title: "Цена (руб.)", data: 'price', type: 'num', render: price_render },
        ],
        order: [[ 1, "desc" ]],  // Сортировка по убыванию даты добавления
        footerCallback: function(tfoot, data, start, end, display) {
            let api = this.api();
            let total = api.column(2).data().reduce((a, b) => a + b, 0);
            $(api.column(2).footer()).html(
                toPrettyPrice(total)
            );
        },
        search: {
            smart: false,
        },
        language: {
            // NOTE: https://datatables.net/plug-ins/i18n/Russian.html
            search: "",
            lengthMenu: "_MENU_",
            zeroRecords: "Записи отсутствуют.",
            info: "Записи с _START_ до _END_ из _TOTAL_ записей",
            infoEmpty: "Записи с 0 до 0 из 0 записей",
            infoFiltered: "(отфильтровано из _MAX_ записей)",
            paginate: {
                previous: '←',
                next: '→',
            }
        },
    });

    // Добавление кнопки очищения к полю поиска
    $(table_selector + '_filter label').contents().unwrap(); //strip off that label tag Bootstrap doesn't like
    $(table_selector + '_filter input')
        .attr('placeholder', 'Введите для поиска...')
        .wrap('<div class="input-group"></div>')
        .after('<div class="input-group-append"><button type="button" class="btn btn-danger">&times;</button></div>')
        .removeClass('form-control-sm')
        .css('margin-left','0');
    $(table_selector + '_wrapper button.btn.btn-danger').click(function() {
        $(table_selector + '_filter input').val('');
        table.search('').columns().search('').draw();
    });

    $(table_selector).on('click', 'tbody tr', function () {
        var row = table.row($(this)).data();

        $('#form_name').val(row.name);
        $('#form_old_name').val(row.name);

        if ($(this).hasClass('selected') ) {
            $(this).removeClass('selected');
        } else {
            table.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }
    });

}

function fill_game_tables() {
    fill_table('#finished_game', 'total_price_finished_games', window.finished_games);
    fill_table('#finished_watched_game', 'total_price_finished_watched_games', window.finished_watched_games);

    // Функция для подсчета итоговых сумм всех игр
    update_total_price_all_tables();

    // Добавление статистики о играх в таблице
    fill_statistics();
}

// Функция загружает все игры, перезаполняет таблицы игр, подсчитывает итого и статистику
function load_tables() {
    $.ajax({
        url: '/get_games',
        dataType: "json",  // тип данных загружаемых с сервера
        success: function(data) {
            console.log(data);
//            console.log(JSON.stringify(data));

            var FINISHED = 'Finished';
            var FINISHED_WATCHED = 'Finished watched';

            window.finished_games = data[FINISHED];
            window.finished_watched_games = data[FINISHED_WATCHED];

            fill_game_tables();
        },

        error: function(data) {
            noty({
                text: 'Не удалось загрузить игры: на сервере произошла ошибка',
                type: 'error',
            });
        }
    });
}

$(document).ready(function() {
    // По умолчанию, флаги всегда стоят
    $('#checkbox_visible_finished_games').prop('checked', true);
    $('#checkbox_visible_finished_watched_games').prop('checked', true);

    load_tables();

    // Обработка изменения цены конкретной игры
    $("#form__set_price").submit(function() {
        var thisForm = this;

        var url = $(this).attr("action");
        var method = $(this).attr("method");
        if (method === undefined) {
            method = "get";
        }

        var data = $(this).serialize();

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // тип данных загружаемых с сервера
            success: function(data) {
                console.log(data);
//                console.log(JSON.stringify(data));

                var ok = data.status == 'ok';
                if (ok && data.result) {
                    load_tables();
                }

                noty({
                    text: data.text,
                    type: ok ? 'success' : 'warning',
                });

                // Очищение полей формы
                thisForm.reset();
            },

            error: function(data) {
                noty({
                    text: 'На сервере произошла ошибка',
                    type: 'error',
                });
            }
        });

        return false;
    });


    // Обработка переименования игры
    $("#form__rename_game").submit(function() {
        var thisForm = this;

        var url = $(this).attr("action");
        var method = $(this).attr("method");
        if (method === undefined) {
            method = "get";
        }

        var data = $(this).serialize();

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // тип данных загружаемых с сервера
            success: function(data) {
                console.log(data);
//                console.log(JSON.stringify(data));

                var ok = data.status == 'ok';
                if (ok && data.result) {
                    load_tables();
                }

                noty({
                    text: data.text,
                    type: ok ? 'success' : 'warning',
                });

                // Очищение полей формы
                thisForm.reset();
            },

            error: function(data) {
                noty({
                    text: 'На сервере произошла ошибка',
                    type: 'error',
                });
            }
        });

        return false;
    });


    // Обработка проверки цены игры
    $("#form__check_price").submit(function() {
        var thisForm = this;

        var url = $(this).attr("action");
        var method = $(this).attr("method");
        if (method === undefined) {
            method = "get";
        }

        var data = $(this).serialize();

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // тип данных загружаемых с сервера

            success: function(data) {
                console.log(data);
//                console.log(JSON.stringify(data));

                var ok = data.status == 'ok';
                if (ok && data.result) {
                    load_tables();
                }

                noty({
                    text: data.text,
                    type: ok ? 'success' : 'warning',
                });

                // Очищение полей формы
                thisForm.reset();
            },

            error: function(data) {
                noty({
                    text: 'На сервере произошла ошибка',
                    type: 'error',
                });
            }
        });

        return false;
    });


    // Проверка всех цен игр без цены
    $("#form__check_price_all_non_price_games").submit(function() {
        var thisForm = this;

        var url = $(thisForm).attr("action");
        var method = $(thisForm).attr("method");
        if (method === undefined) {
            method = "get";
        }

        var data = $(thisForm).serialize();

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // тип данных загружаемых с сервера
            success: function(data) {
                console.log(data);
//                console.log(JSON.stringify(data));

                var ok = data.status == 'ok';
                if (ok && data.result) {
                    load_tables();
                }

                noty({
                    text: data.text,
                    type: ok ? 'success' : 'warning',

                    timeout: false,
                });
            },

            error: function(data) {
                noty({
                    text: 'На сервере произошла ошибка',
                    type: 'error',
                });
            },

            beforeSend: function() {
                $(thisForm).find('.loading').show();
            },

            complete: function() {
                $(thisForm).find('.loading').hide();
            }
        });

        return false;
    });

    // Обработка удаления конкретной игры
    $("#form__delete_game").submit(function() {
        var thisForm = this;

        var url = $(this).attr("action");
        var method = $(this).attr("method");
        if (method === undefined) {
            method = "get";
        }

        var data = $(this).serialize();

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // тип данных загружаемых с сервера
            success: function(data) {
                console.log(data);
//                console.log(JSON.stringify(data));

                var ok = data.status == 'ok';
                if (ok && data.result) {
                    load_tables();
                }

                noty({
                    text: data.text,
                    type: ok ? 'success' : 'warning',
                });

                // Очищение полей формы
                thisForm.reset();
            },

            error: function(data) {
                noty({
                    text: 'На сервере произошла ошибка',
                    type: 'error',
                });
            }
        });

        return false;
    });
});
