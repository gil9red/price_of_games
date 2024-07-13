const COLUMN_DETAIL = 0;
const COLUMN_KIND = 1;
const COLUMN_NAME = 2;
const COLUMN_PLATFORM = 3;
const COLUMN_APPEND_DATE = 4;
const COLUMN_PRICE = 5;

const TABLE_ID = "#games";


$.noty.defaults.theme = 'defaultTheme';
$.noty.defaults.layout = 'bottomRight';
$.noty.defaults.timeout = 6000;


function get_table() {
    return $(TABLE_ID).DataTable();
}

function get_table_row_by_id(id) {
    return get_table().row("#" + id);
}

function process_games_from_response(rs, callback) {
    let ok = rs.status == 'ok';

    if (ok && rs.result != null) {
        for (let game of rs.result) {
            let row = get_table_row_by_id(game.id);
            callback(game, row);
        }
    }
}

function update_rows_table_by_response(rs) {
    process_games_from_response(
        rs,
        (game, row) => {
            let is_exist = row.any();
            if (is_exist) {
                row.data(game).draw("full-hold"); // full-hold сохраняет пагинацию
            } else {
                row.table().row.add(game).draw(); // Тут пагинация вернется к первой странице
            }
        }
    );
}

function delete_rows_table_by_response(rs) {
    process_games_from_response(
        rs,
        (game, row) => {
            let is_exist = row.any();
            if (is_exist) {
                row.remove().draw("full-hold"); // full-hold сохраняет пагинацию
            }
        }
    );
}

function on_ajax_success(data, callback=update_rows_table_by_response) {
    let ok = data.status == 'ok';
    if (data.text) {
        noty({
            text: data.text,
            type: ok ? 'success' : 'warning',
        });
    }

    callback(data);
}

function on_ajax_error(data, reason) {
    noty({
        text: `На сервере произошла неожиданная ошибка ${reason}`,
        type: 'error',
    });
}

function showDialogWithIFrame(idDialog, iframeSrc) {
    let $iframe = $(`#${idDialog} iframe`);
    $iframe.attr('src', iframeSrc);

    // TODO: Не работает
    // Отключение логов
//    $iframe[0].contentWindow.console.log = function() { /* nop */ };

    let dialogName = `dialog ${idDialog}`;

    if (!window[dialogName]) {
        window[dialogName] = new DialogBox(
            idDialog,
            (btnName) => {
                // Очищение iframe при закрытии диалога
                $iframe.attr('src', '');
            }
        );
    }
    window[dialogName].showDialog();

    $dialog = $(`#${idDialog}`);
    $dialog.css('top', $dialog.data('top'));
    $dialog.css('left', $dialog.data('left'));
}

function showDialogIFrameGoogle(src) {
    showDialogWithIFrame('dialog-iframe-google', src);
}

function showDialogIFrameGamefaqs(src) {
    showDialogWithIFrame('dialog-iframe-gamefaqs', src);
}

function run_check_prices() {
    $.ajax({
        url: "/api/run_check_prices",
        method: "POST",
        success: data => on_ajax_success(data),
        error: data => on_ajax_error(data, 'при запуске проверки цен'),

        beforeSend: function() {
            $('.run_check.loading').show();
        },

        complete: function() {
            $('.run_check.loading').hide();
        }
    });
}

function run_check_genres() {
    $.ajax({
        url: "/api/run_check_genres",
        method: "POST",
        success: data => on_ajax_success(data),
        error: data => on_ajax_error(data, 'при запуске проверки жанров игр'),

        beforeSend: function() {
            $('.run_check.loading').show();
        },

        complete: function() {
            $('.run_check.loading').hide();
        }
    });
}

function onChangeVisibleFixedRightPanel(visible) {
    localStorage.fixed_right_panel = visible;
}

function getGenresFromForm() {
    let inputGenres = $('#form_genres');
    let value = JSON.parse(inputGenres.val() || "[]");
    return value.map(e => e.value).sort();
}

function updateStatesFormSetGenres() {
    let genres = getGenresFromForm();

    let inputGenres = $('#form_genres');
    let oldGenres = inputGenres.data('old-value').sort();

    let isNoGenres = genres.length == 0;
    let isNoChanges = JSON.stringify(oldGenres) === JSON.stringify(genres);

    // Отключение кнопки отправки при пустом списке жанров
    window.formGenresButtonOk.prop("disabled", isNoGenres || isNoChanges);

    window.formGenresButtonCancel.prop("disabled", isNoChanges);
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

    let $cbShowCurAndMaxNumberGames = $('#cbShowCurAndMaxNumberGames');
    if (localStorage.cbShowCurAndMaxNumberGames != null) {
        let checked = localStorage.cbShowCurAndMaxNumberGames == "true";
        $cbShowCurAndMaxNumberGames.prop('checked', checked);
    }
    function doShowCurAndMaxNumberGames() {
        let isShowCurAndMaxNumberGames = $cbShowCurAndMaxNumberGames.is(':checked');

        let $finished_game_statistic = $('.finished_game_statistic');
        let $finished_watched_game_statistic = $('.finished_watched_game_statistic');
        let $games_statistic = $('.games_statistic');

        if (isShowCurAndMaxNumberGames) {
            $finished_game_statistic.removeClass("d-none");
            $finished_watched_game_statistic.removeClass("d-none");
            $games_statistic.removeClass("d-none");
        } else {
            $finished_game_statistic.addClass("d-none");
            $finished_watched_game_statistic.addClass("d-none");
            $games_statistic.addClass("d-none");
        }

        localStorage.cbShowCurAndMaxNumberGames = isShowCurAndMaxNumberGames;
    }
    doShowCurAndMaxNumberGames();  // Инициализация от значения
    $cbShowCurAndMaxNumberGames.change(function() {
        doShowCurAndMaxNumberGames();
    });

    let fixedRightPanel = $('#fixed_right_panel');
    if (localStorage.fixed_right_panel != null) {
        let visible = localStorage.fixed_right_panel == "true";
        fixedRightPanel.collapse(visible ? 'show' : 'hide');
    }
    fixedRightPanel.on("show.bs.collapse", () => onChangeVisibleFixedRightPanel(true));
    fixedRightPanel.on("hide.bs.collapse", () => onChangeVisibleFixedRightPanel(false));

    $('#form__set_genres')[0].reset();

    window.formGenresButtonOk = $('#form__set_genres button[data-role="accept"]');

    window.formGenresButtonCancel = $('#form__set_genres button[data-role="cancel"]');
    window.formGenresButtonCancel.click(function () {
        let inputGenres = $('#form_genres');
        let genres = inputGenres.data('old-value');
        window.formGenres.removeAllTags();
        window.formGenres.addTags(genres);
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
    let re = '\\d(?=(\\d{' + (x || 3) + '})+' + (n > 0 ? '\\D' : '$') + ')';
    let num = this.toFixed(Math.max(0, ~~n));

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

function update_total_price_all_tables(finished_games, finished_watched_games) {
    let total_price_of_finished_game = 0;
    for (let row of finished_games) {
        if (row.price) {
            total_price_of_finished_game += row.price;
        }
    }

    let total_price_of_finished_watched_game = 0;
    for (let row of finished_watched_games) {
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

function open_tab_steam(query) {
    let url = 'http://store.steampowered.com/search/?term=' + encodeURIComponent(query);
    console.log(`open_tab_steam("${query}") -> ${url}`);

    window.open(url);
}

function open_google(query, inTab=true) {
    let url = 'https://www.google.com/search?q=' + encodeURIComponent(query);
    console.log(`open_google("${query}", inTab=${inTab}) -> ${url}`);

    if (inTab) {
        window.open(url);
    } else {
        showDialogIFrameGoogle(url + '&igu=1');
    }
}

function open_tab_google(query) {
    open_google(query, true);
}

function open_dialog_google(query) {
    open_google(query, false);
}

function open_gamefaqs(query, inTab=true) {
    let url = 'https://gamefaqs.gamespot.com/search?game=' + encodeURIComponent(query);
    console.log(`open_gamefaqs("${query}", inTab=${inTab}) -> ${url}`);

    if (inTab) {
        window.open(url);
    } else {
        showDialogIFrameGamefaqs(url);
    }
}

function open_tab_gamefaqs(query) {
    open_gamefaqs(query, true);
}

function open_dialog_gamefaqs(query) {
    open_gamefaqs(query, false);
}

// Функция возвращает строку с статистикой: сколько всего игр, сколько имеют цены, и процент.
// Пример: (0 / 160 (0%))
function statistic_for_table(items) {
    let price_is_none_rows_number = 0;
    for (let row of items) {
        if (row.price == null) {
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

function fill_statistics(finished_games, finished_watched_games) {
    let games = finished_games.concat(finished_watched_games);
    let statistic_1 = statistic_for_table(finished_games);
    let statistic_2 = statistic_for_table(finished_watched_games);

    $('.finished_game_statistic').html(statistic_1);
    $('.finished_watched_game_statistic').html(statistic_2);
    $('.games_statistic').html(statistic_for_table(games));

    // Добавление статистики о количестве игр в таблицах
    $('.number_finished_games').text(finished_games.length);
    $('.number_finished_watched_games').text(finished_watched_games.length);
    $('.sum_number_games').text(games.length);
}

function price_render(data, type, row, meta) {
    if (data != null) {
        return data;
    }

    // Для display и filter показываем текстом что цены нет и добавляем картинки для поиска
    if (type === 'display' || type === 'filter') {
        return '<div>Цена не задана</div>';
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

function get_genre_description(genre_name) {
    let genre = ALL_GENRES[genre_name];
    let description = genre.aliases;

    if (genre.description) {
        description = `${genre.description}\n\n${description}`;
    }

    return description;
}

function genres_render(genres) {
    let tags = [];
    for (let name of genres) {
        let description = get_genre_description(name);

        // Для визуальной разницы
        let genre = ALL_GENRES[name];
        if (genre.description) {
            tags.push(`<abbr class="genre" title="${description}">${name}</abbr>`);
        } else {
            tags.push(`<span class="genre" title="${description}">${name}</span>`);
        }
    }
    return tags.join(', ');
}

function format_detail_row(row) {
    let genres = genres_render(row.genres);
    return `
        <table class="table-borderless table-sm">
            <tbody>
                <tr><td class="font-weight-bold">Жанры:</td><td>${genres}</td></tr>
            </tbody>
        </table>
    `
}

function for_filter_render(data, type, row, meta) {
    if (type === 'filter') {
        return row.genres.join(', ');
    }
    return data;
}

function setVisibleProgress(table_selector, visible) {
    let selector = `${table_selector}_caption_table .loading-spinner`;
    $(selector).toggle(visible);
}

function platform_render(data, type, row, meta) {
    if (type === 'filter') {
        return data;
    }
    return `<span class="platform">${data}</span>`;
}

function kind_render(data, type, row, meta) {
    let emoji = KIND_BY_EMOJI[data];
    return `<span class="kind">${emoji}</span>`;
}

function createTags(
        $element,
        getTagsFunc,
        tableEl,
        queryTag,
        preprocessOptionsFunc = null,
) {
    let options = {
        whitelist: getTagsFunc(),
        enforceWhitelist: true,
        skipInvalid: true,
        dropdown: {
            enabled: 0, // Показывать при фокусе
            closeOnSelect: false,
            maxItems: Infinity,
        },
        callbacks: {
            // Удаление тега при клике на него
            click: (e) => e.detail.tagify.removeTags(e.detail.tag),
        },
    };

    if (preprocessOptionsFunc != null) {
        preprocessOptionsFunc(options);
    }

    let tagify = new Tagify($element[0], options);
    tagify.custom__need_reread_whitelist = true;

    tagify.on("dropdown:show", function (e) {
        tagify.custom__need_reread_whitelist = false;
    });

    tagify.on("dropdown:hide", function (e) {
        tagify.custom__need_reread_whitelist = true;
    });

    let origFilterListItems = tagify.dropdown.filterListItems;
    tagify.dropdown.filterListItems = function (value, options) {
        if (tagify.custom__need_reread_whitelist) {
            // Подмена на актуальный список
            tagify.settings.whitelist = getTagsFunc();
        }
        return origFilterListItems(value, options);
    };

    tableEl.on('click', queryTag, function () {
        let value = $(this).text();
        tagify.addTags(value);
    });
}

function createFilterOfKinds(table, tableEl) {
    // Под колонку типа добавлен фильтр
    let column = table.api().column(COLUMN_KIND);

    let $filterKind = $(".column-kind > input")
        .on('change', function () {
            let val = $(this).val();
            if (val) {
                let values = JSON.parse(val).map(x => '^' + $.fn.dataTable.util.escapeRegex(x.value) + '$');
                let query = values.join('|');
                column.search(
                    query,
                    true,  // regexp
                    false  // smart
                ).draw();
            } else {
                column.search("").draw();
            }
        })
    ;

    // Применение фильтра
    $filterKind.trigger("change");

    function getTags() {
        let values = [];
        table
            .api()
            .column(COLUMN_KIND, {search: "applied"})
            .data()
            .unique()
            .sort()
            .each(function (value, index) {
                // Значение в фильтре типов будут сами эмодзи
                let title = KIND_BY_EMOJI[value];
                values.push(title);
            })
        ;
        return values;
    }

    function preprocessOptions(options) {
        options.dropdown.closeOnSelect = true;

        // Удаление всех тегов, чтобы при добавлении был только выбранный
        // Типов всего 2, поэтому фильтрация только по одному имеет смысл
        options.callbacks.add = (e) => e.detail.tagify.removeTags();
    }

    // Инициализация
    createTags($filterKind, getTags, tableEl, '.kind', preprocessOptions);
}

function createFilterOfPlatforms(table, tableEl) {
    // Под колонку платформы добавлен фильтр
    let columnPlatform = table.api().column(COLUMN_PLATFORM);

    let $filterPlatform = $(".column-platform > input")
        .on('change', function () {
            let val = $(this).val();
            if (val) {
                let values = JSON.parse(val).map(x => '^' + $.fn.dataTable.util.escapeRegex(x.value) + '$');
                let query = values.join('|');
                columnPlatform.search(
                    query,
                    true,  // regexp
                    false  // smart
                ).draw();
            } else {
                columnPlatform.search("").draw();
            }
        })
    ;

    // Применение фильтра
    $filterPlatform.trigger("change");

    function getTags() {
        let platforms = [];
        table
            .api()
            .column(COLUMN_PLATFORM, {search: "applied"})
            .data()
            .unique()
            .sort()
            .each(function (value, index) {
                platforms.push(value);
            })
        ;
        return platforms;
    }

    // Инициализация платформ
    createTags($filterPlatform, getTags, tableEl, '.platform');
}

function createFilterOfGenres(table, tableEl) {
    // Под колонку названия добавлен фильтр по жанрам
    let columnName = table.api().column(COLUMN_NAME);

    // Но поиск будет в колонке деталей - там размещен рендер для поиска жанров
    let columnDetail = table.api().column(COLUMN_DETAIL);

    let $filterGenres = $(".column-name > input")
        .on('change', function () {
            let val = $(this).val();
            if (val) {
                let values = JSON.parse(val).map(x => `"${x.value}"`);
                let query = values.join(' ');
                columnDetail.search(
                    query,
                    false, // regexp
                    true   // smart
                ).draw();
            } else {
                columnDetail.search("").draw();
            }
        })
    ;

    // Применение фильтра
    $filterGenres.trigger("change");

    function getTags() {
        // Заполнение жанров из текущей таблицы
        let uniqueGenres = new Set();
        table
            .api()
            .rows({search: "applied"})
            .every(function (rowIdx, tableLoop, rowLoop) {
                for (let name of this.data().genres) {
                    uniqueGenres.add(name);
                }
            })
        ;

        let genres = new Array();
        for (let name of Array.from(uniqueGenres).sort()) {
            genres.push({
                value: name,
                searchBy: ALL_GENRES[name].aliases, // Для альтернативного поиска жанров
                title: get_genre_description(name), // Для всплывающих подсказок при наведении мышки
            });
        }

        return genres;
    }

    function preprocessOptions(options) {
        options.dropdown.closeOnSelect = true;
    }

    // Инициализация жанров
    createTags($filterGenres, getTags, tableEl, '.genre', preprocessOptions);
}

function fill_table(table_selector, items) {
    let tableEl = $(table_selector);

    if ($.fn.dataTable.isDataTable(table_selector)) {
        tableEl.DataTable()
            .clear()
            .rows.add(items)
            .draw();
        return;
    }

    let table = tableEl.DataTable({
        // Теперь поле поиска будет занимать 9/12 места, вместо 6/12
        dom: "<'row'<'col-sm-12 col-md-3'l><'col-sm-12 col-md-9'f>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
        data: items,
        lengthMenu: [
            [5, 10, 25, 50, -1],
            ["5 записей", "10 записей", "25 записей", "50 записей", "Все записи"]
        ],
        rowId: "id",  // Заполняет в строках id из поля id в data
        columns: [
            {
                class: 'dt-control',
                orderable: false,
                data: null,
                defaultContent: '',
                render: for_filter_render,
            },
            { data: "kind", render: kind_render, orderable: false },
            { data: "name" },
            { data: 'platform', render: platform_render },
            { data: 'append_date', render: append_date_render },
            { data: 'price', type: 'num', render: price_render },
        ],
        order: [
            // Сортировка по убыванию даты добавления
            [ COLUMN_APPEND_DATE, "desc" ]
        ],
        search: {
            smart: false,
        },
        select: {
            toggleable: false,  // Нельзя убирать выделение повторным кликом
        },
        stateSave: true,
        stateDuration: 0, // Без ограничения срока хранения
        stateSaveParams: function (settings, data) {
            // Убрана фильтрация по столбцам, чтобы ее делать
            // из тегов после их загрузки из data.custom_filters
            for (let column of data.columns) {
                column.search.search = "";
            }

            if (data.custom_filters == null) {
                data.custom_filters = {
                    kinds: [],
                    genres: [],
                    platforms: [],
                };
            }

            function get_tagify_items(tagify_el) {
                return tagify_el.__tagify.value.map((obj) => obj.value);
            }

            // Под колонку типа добавлен фильтр
            let columnKind = this.api().column(COLUMN_KIND);
            let inputKind = $(columnKind.footer()).find("input")[0];
            if (inputKind != null && inputKind.__tagify != null) {
                data.custom_filters.kinds = get_tagify_items(inputKind);
            } else {
                data.custom_filters.kinds = [];
            }

            // Под колонку названия добавлен фильтр по жанрам
            let columnName = this.api().column(COLUMN_NAME);
            let inputName = $(columnName.footer()).find("input")[0];
            if (inputName != null && inputName.__tagify != null) {
                data.custom_filters.genres = get_tagify_items(inputName);
            } else {
                data.custom_filters.genres = [];
            }

            // Под колонку платформы добавлен фильтр
            let columnPlatform = this.api().column(COLUMN_PLATFORM);
            let inputPlatform = $(columnPlatform.footer()).find("input")[0];
            if (inputPlatform != null && inputPlatform.__tagify != null) {
                data.custom_filters.platforms = get_tagify_items(inputPlatform);
            } else {
                data.custom_filters.platforms = [];
            }
        },
        stateLoadParams: function (settings, data) {
            // NOTE: childRows и пагинация не восстанавливаются. Возможно, из-за последующих .draw()

            function set_tagify_items($tagify_el, items) {
                let value = items.length > 0
                    ? JSON.stringify(
                        items.map(x => ({value: x}))
                    )
                    : ""
                ;
                $tagify_el.attr("value", value);
            }

            if (data != null && data.custom_filters != null) {
                set_tagify_items($(".column-kind > input"), data.custom_filters.kinds);
                set_tagify_items($(".column-name > input"), data.custom_filters.genres);
                set_tagify_items($(".column-platform > input"), data.custom_filters.platforms);
            }
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
            },
            // Убираем строку внизу таблицы, отображающаяся при выделении строки таблицы
            select: {
                rows: {
                    _: "",
                }
            }
        },
        footerCallback: function (tfoot, data, start, end, display) {
            // Собираем цены с учетом поиска и фильтров и выводим в итоговую сумму
            let column_price = this.api().column(COLUMN_PRICE, {search: "applied"});
            let total = column_price.data().reduce((a, b) => a + b, 0);
            $(column_price.footer()).html(
                toPrettyPrice(total)
            );

            setVisibleProgress(table_selector, false);
        },
        drawCallback: function (settings) {
            let finished_games = [];
            let finished_watched_games = [];

            this.api().rows().every(function (rowIdx, tableLoop, rowLoop) {
                let data = this.data();
                if (data.kind == FINISHED_GAME) {
                    finished_games.push(data);
                } else {
                    finished_watched_games.push(data);
                }
            });

            // Функция для подсчета итоговых сумм всех игр
            update_total_price_all_tables(finished_games, finished_watched_games);

            // Добавление статистики о играх в таблице
            fill_statistics(finished_games, finished_watched_games);

            // Рисование графиков
            fill_charts(finished_games, finished_watched_games);
        },
        initComplete: function (settings, json) {
            createFilterOfKinds(this, tableEl);
            createFilterOfPlatforms(this, tableEl);
            createFilterOfGenres(this, tableEl);

            tableEl.show();
            this.api().columns.adjust().draw();
        },
    });

    // Добавление обработчика для отображения/скрытия деталей строки
    $(table_selector + ' tbody').on('click', 'td.dt-control', function () {
        let tr = $(this).closest('tr');
        let row = table.row(tr);

        if (row.child.isShown()) {
            // This row is already open - close it
            row.child.hide();
            tr.removeClass('shown');
        } else {
            // Open this row
            row.child(format_detail_row(row.data())).show();
            tr.addClass('shown');
        }
    });

    // Удаление -sm из виджета выбора количества записей
    $(table_selector + '_length select')
        .removeClass('custom-select-sm')
        .removeClass('form-control-sm');

    // Добавление кнопки очищения к полю поиска
    $(table_selector + '_filter label').contents().unwrap(); //strip off that label tag Bootstrap doesn't like
    let filterInput = $(table_selector + '_filter input')
        .attr('placeholder', 'Введите для поиска...')
        .wrap('<div class="input-group"></div>')
        .after('<div class="input-group-append"><button type="button" class="btn btn-danger glyphicon glyphicon-remove top-0"></button></div>')
        .removeClass('form-control-sm')
        .css('margin-left', '0');

    let filterClearButton = $(table_selector + '_wrapper button.btn.btn-danger');
    function updateStatsClearButton() {
        filterClearButton.prop('disabled', !filterInput.val());
    }

    // Установка состояния кнопки
    updateStatsClearButton();

    filterInput.on("input", function() {
        updateStatsClearButton();
    });

    filterClearButton.click(function() {
        filterInput.val('');
        updateStatsClearButton();
        table.search('').draw();
    });

    table.on('select', function(e, dt, type, indexes) {
        let row = table.row(indexes[0]).data();

        // Если у текущей игры цены нет, то автоматически добавляем название игры
        // в поле установки цены
        if (row.price == null) {
            $('#form_name').val(row.name);
        }

        $('form input.game-id').val(row.id);
        $('form input.game-name').val(row.name);

        let genres = row.genres;
        let inputGenres = $('#form_genres');
        inputGenres.data('old-value', genres);

        window.formGenres.removeAllTags();
        window.formGenres.addTags(genres);

        $('[data-game-name]').attr('data-game-name', row.name);
        $('[data-game-platform]').attr('data-game-platform', row.platform);

        $(".search-img-group").toggleClass('disabled', false);

        updateStatesFormSetGenres();
    });
}

function callStatisticsByGames(games) {
    let platform_by_total_price = new Map();
    let platform_by_number = new Map();
    let genre_by_number = new Map();
    let genre_by_total_price = new Map();
    let hour_by_number = new Map();
    let year_by_number = new Map();
    let total_price = 0;

    for (let row of games) {
        total_price += row.price;

        let platform_name = row.platform;

        let price = platform_by_total_price.has(platform_name)
            ? platform_by_total_price.get(platform_name)
            : 0;
        platform_by_total_price.set(platform_name, row.price + price);

        let number = platform_by_number.has(platform_name)
            ? platform_by_number.get(platform_name)
            : 0;
        platform_by_number.set(platform_name, number + 1);

        let append_date = new Date(row.append_date_timestamp * 1000);

        let hour = append_date.getHours();
        let numberByHour = hour_by_number.has(hour)
            ? hour_by_number.get(hour)
            : 0;
        hour_by_number.set(hour, numberByHour + 1);

        let year = append_date.getFullYear();
        let numberByYear = year_by_number.has(year)
            ? year_by_number.get(year)
            : 0;
        year_by_number.set(year, numberByYear + 1);

        for (let genre_name of row.genres) {
            let number = genre_by_number.has(genre_name)
                ? genre_by_number.get(genre_name)
                : 0;
            genre_by_number.set(genre_name, number + 1);

            let price = genre_by_total_price.has(genre_name)
                ? genre_by_total_price.get(genre_name)
                : 0;
            genre_by_total_price.set(genre_name, row.price + price);
        }
    }

    return [
        platform_by_total_price,
        platform_by_number,
        total_price,
        genre_by_number,
        genre_by_total_price,
        hour_by_number,
        year_by_number
    ];
}

function sumMaps(map1, map2) {
    let newMap = new Map();
    for (let [key, value] of map1) {
        newMap.set(key, value);
    }
    for (let [key, value] of map2) {
        if (newMap.has(key)) {
            value += newMap.get(key);
        }
        newMap.set(key, value);
    }
    return newMap;
}

function sortReversedMapByValue(map) {
    return new Map([...map.entries()].sort((a, b) => b[1] - a[1]));
}

function sortMapByKey(map) {
    return new Map([...map.entries()].sort((a, b) => a[0] - b[0]));
}

function createOrUpdateCharts(chartId, title, labels, datasets, options, type="pie") {
    let thisOptions = structuredClone(options);
    thisOptions.plugins.title.text = title;

    let keyChartId = `obj-${chartId}`;
    let objChart = window[keyChartId];
    if (objChart) {
        objChart.data.labels = labels;
        for (let i = 0; i < datasets.length; i++) {
            objChart.data.datasets[i].data = datasets[i].data;
        }
        objChart.update();
        return;
    }

    window[keyChartId] = new Chart(
        document.getElementById(chartId),
        {
            type: type,
            data: {
                labels: labels,
                datasets: datasets
            },
            options: thisOptions,
        }
    );
}

function fill_charts(finished_games, finished_watched_games) {
    let [
        platform_by_total_price_of_finished_games,
        platform_by_number_of_finished_games,
        total_price_of_finished_games,
        genre_by_number_of_finished_games,
        genre_by_total_price_of_finished_games,
        hour_by_number_of_finished_games,
        year_by_number_of_finished_games
    ] = callStatisticsByGames(finished_games);
    let [
        platform_by_total_price_of_finished_watched_games,
        platform_by_number_of_finished_watched_games,
        total_price_of_finished_watched_games,
        genre_by_number_of_finished_watched_games,
        genre_by_total_price_of_finished_watched_games,
        hour_by_number_of_finished_watched_games,
        year_by_number_of_finished_watched_games
    ] = callStatisticsByGames(finished_watched_games);

    let backgroundColor = [
        '#ff6384',
        '#36a2eb',
    ];
    let options = {
        plugins: {
            legend: {
                labels: {
                    color: "white",
                },
            },
            title: {
                display: true,
                color: 'white',
            }
        }
    };

    createOrUpdateCharts(
        'chartKindBy',
        'Категория по...',
        // labels
        [
            'Пройденные',
            'Просмотренные',
        ],
        // datasets
        [
            {
                label: 'Категория по играм',
                data: [
                    finished_games.length,
                    finished_watched_games.length
                ],
                backgroundColor: backgroundColor
            },
            {
                label: 'Категория по ценам',
                data: [
                    total_price_of_finished_games,
                    total_price_of_finished_watched_games
                ],
                backgroundColor: backgroundColor
            },
            {
                label: 'Категория по платформам',
                data: [
                    platform_by_total_price_of_finished_games.size,
                    platform_by_total_price_of_finished_watched_games.size
                ],
                backgroundColor: backgroundColor
            },
        ],
        options
    );

    const numberOfTop = 5;

    let platform_by_number = sortReversedMapByValue(
        sumMaps(platform_by_number_of_finished_games, platform_by_number_of_finished_watched_games)
    );
    createOrUpdateCharts(
        'chartPlatformByNumber',
        `Топ ${numberOfTop} платформ по играм`,
        // labels
        Array.from(
            platform_by_number.keys()
        ).slice(0, numberOfTop),
        // datasets
        [{
            data: Array.from(
                platform_by_number.values()
            ).slice(0, numberOfTop),
        }],
        options
    );

    let platform_by_total_price = sortReversedMapByValue(
        sumMaps(platform_by_total_price_of_finished_games, platform_by_total_price_of_finished_watched_games)
    );
    createOrUpdateCharts(
        'chartPlatformByPrice',
        `Топ ${numberOfTop} платформ по ценам`,
        // labels
        Array.from(
            platform_by_total_price.keys()
        ).slice(0, numberOfTop),
        // datasets
        [{
            data: Array.from(
                platform_by_total_price.values()
            ).slice(0, numberOfTop),
        }],
        options
    );

    let genre_by_number = sortReversedMapByValue(
        sumMaps(genre_by_number_of_finished_games, genre_by_number_of_finished_watched_games)
    );
    createOrUpdateCharts(
        'chartGenreByNumber',
        `Топ ${numberOfTop} жанров по играм`,
        // labels
        Array.from(
            genre_by_number.keys()
        ).slice(0, numberOfTop),
        // datasets
        [{
            data: Array.from(
                genre_by_number.values()
            ).slice(0, numberOfTop),
        }],
        options
    );

    let genre_by_price = sortReversedMapByValue(
        sumMaps(genre_by_total_price_of_finished_games, genre_by_total_price_of_finished_watched_games)
    );
    createOrUpdateCharts(
        'chartGenreByPrice',
        `Топ ${numberOfTop} жанров по ценам`,
        // labels
        Array.from(
            genre_by_price.keys()
        ).slice(0, numberOfTop),
        // datasets
        [{
            data: Array.from(
                genre_by_price.values()
            ).slice(0, numberOfTop),
        }],
        options
    );

    let hour_by_number = sortMapByKey(
        sumMaps(hour_by_number_of_finished_games, hour_by_number_of_finished_watched_games)
    );
    createOrUpdateCharts(
        "chartHourByNumber",
        "Игры по часам в сутках",
        // labels
        Array.from(
            hour_by_number.keys()
        ),
        // datasets
        [{
            label: "Игр",
            data: Array.from(
                hour_by_number.values()
            ),
        }],
        options,
        "bar"
    );

    let year_by_number = sortMapByKey(
        sumMaps(year_by_number_of_finished_games, year_by_number_of_finished_watched_games)
    );
    let all_year_by_number_of_finished_games = new Map();
    let all_year_by_number_of_finished_watched_games = new Map();
    for (let year of year_by_number.keys()) {
        let value_of_finished_games = year_by_number_of_finished_games.has(year)
            ? year_by_number_of_finished_games.get(year)
            : 0;
        all_year_by_number_of_finished_games.set(year, value_of_finished_games);

        let value_of_finished_watched_games = year_by_number_of_finished_watched_games.has(year)
            ? year_by_number_of_finished_watched_games.get(year)
            : 0;
        all_year_by_number_of_finished_watched_games.set(year, value_of_finished_watched_games);
    }
    createOrUpdateCharts(
        "chartYearByNumber",
        "Игры по годам",
        // labels
        Array.from(
            year_by_number.keys()
        ),
        // datasets
        [
            {
                label: "Всего",
                data: Array.from(
                    year_by_number.values()
                ),
            },
            {
                label: "Пройденных",
                data: Array.from(
                    all_year_by_number_of_finished_games.values()
                ),
            },
            {
                label: "Просмотренных",
                data: Array.from(
                    all_year_by_number_of_finished_watched_games.values()
                ),
            },
        ],
        options,
        "bar"
    );
}

function fill_genres() {
    let genres = new Array();
    for (let name in ALL_GENRES) {
        genres.push({
            value: name,
            searchBy: ALL_GENRES[name].aliases, // Для альтернативного поиска жанров
            title: get_genre_description(name), // Для всплывающих подсказок при наведении мышки
        });
    }
    genres = genres.sort((a, b) => a.value.localeCompare(b.value));

    // Инициализация поля для изменения жанров выбранной игры
    let el = $('#form_genres')[0];
    if (!window.formGenres) {
        window.formGenres = new Tagify(el, {
            whitelist: genres,
            enforceWhitelist: true,
            skipInvalid: true,
            dropdown: {
                enabled: 0,
                closeOnSelect: false,
                maxItems: Infinity,
            },
            callbacks: {
                // Удаление тега при клике на него
                click: (e) => e.detail.tagify.removeTags(e.detail.tag),

                // Управление состояний кнопок формы
                change: (e) => updateStatesFormSetGenres(),
            },
        });
    }
}

// Функция загружает все игры, перезаполняет таблицы игр, подсчитывает итого и статистику
function load_tables() {
    // Пока запрос грузится с сайта и таблица рендерит данные
    setVisibleProgress(TABLE_ID, true);

    $.ajax({
        url: '/api/get_games',
        dataType: "json",  // Тип данных загружаемых с сервера
        success: data => fill_table(TABLE_ID, data),
        error: data => on_ajax_error(data, 'при загрузке игр'),
    });
}

$(document).ready(function() {
    fill_genres();

    load_tables();

    // Обработка изменения цены конкретной игры
    $("#form__set_price").submit(function() {
        let thisForm = this;

        let url = $(this).attr("action");
        let method = $(this).attr("method");
        if (method === undefined) {
            method = "get";
        }

        let data = $(this).serialize();

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // Тип данных загружаемых с сервера
            success: function(data) {
                on_ajax_success(data);

                // Очищение полей формы
                thisForm.reset();
            },
            error: data => on_ajax_error(data, 'при установке цены'),
        });

        return false;
    });

    $('#form__set_genres').submit(function() {
        let thisForm = this;

        let url = $(this).attr("action");
        let method = $(this).attr("method");
        if (method === undefined) {
            method = "get";
        }

        let data = {};
        $(this).find('input, textearea, select').each(function() {
            data[this.name] = $(this).val();
        });
        // У тегов формат немного излишний, заполняем своим
        data['genres'] = JSON.stringify(getGenresFromForm());

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // Тип данных загружаемых с сервера
            success: function(data) {
                on_ajax_success(data);

                // Очищение полей формы
                thisForm.reset();

                // После очищения поля нужно сделать кнопки поиска неактивными
                $(".search-img-group").toggleClass("disabled", true);
            },
            error: data => on_ajax_error(data, 'при установке жанров'),
        });

        return false;
    });

    // Обработка переименования игры
    $("#form__rename_game").submit(function() {
        let thisForm = this;

        let url = $(this).attr("action");
        let method = $(this).attr("method");
        if (method === undefined) {
            method = "get";
        }

        let data = $(this).serialize();

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // Тип данных загружаемых с сервера
            success: function(data) {
                on_ajax_success(data);

                // Очищение полей формы
                thisForm.reset();
            },
            error: data => on_ajax_error(data, 'при переименовании игры'),
        });

        return false;
    });


    // Обработка проверки цены игры
    $("#form__check_price").submit(function() {
        let thisForm = this;

        let url = $(this).attr("action");
        let method = $(this).attr("method");
        if (method === undefined) {
            method = "get";
        }

        let data = $(this).serialize();

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // Тип данных загружаемых с сервера

            success: function(data) {
                on_ajax_success(data);

                // Очищение полей формы
                thisForm.reset();
            },
            error: data => on_ajax_error(data, 'при проверки цены игры'),
        });

        return false;
    });


    // Проверка всех цен игр без цены
    $("#form__check_price_all_non_price_games").submit(function() {
        let thisForm = this;

        let url = $(thisForm).attr("action");
        let method = $(thisForm).attr("method");
        if (method === undefined) {
            method = "get";
        }

        let data = $(thisForm).serialize();

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // Тип данных загружаемых с сервера
            success: data => on_ajax_success(data),
            error: data => on_ajax_error(data, 'при проверки цен всех игр без цены'),

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
        let thisForm = this;

        let url = $(this).attr("action");
        let method = $(this).attr("method");
        if (method === undefined) {
            method = "get";
        }

        let data = $(this).serialize();

        $.ajax({
            url: url,
            method: method,  // HTTP метод, по умолчанию GET
            data: data,
            dataType: "json",  // Тип данных загружаемых с сервера
            success: function(data) {
                on_ajax_success(data, delete_rows_table_by_response);

                // Очищение полей формы
                thisForm.reset();
            },
            error: data => on_ajax_error(data, 'при удалении игры'),
        });

        return false;
    });
});
