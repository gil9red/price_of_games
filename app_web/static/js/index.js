const COLUMN_DETAIL = 0;
const COLUMN_NAME = 1;
const COLUMN_PLATFORM = 2;
const COLUMN_APPEND_DATE = 3;
const COLUMN_PRICE = 4;


$.noty.defaults.theme = 'defaultTheme';
$.noty.defaults.layout = 'bottomRight';
$.noty.defaults.timeout = 6000;


function on_ajax_success(data) {
    console.log(data);

    let ok = data.status == 'ok';
    if (data.text) {
        noty({
            text: data.text,
            type: ok ? 'success' : 'warning',
        });
    }

    let isReloadTableOnAjax = $('#cbReloadTableOnAjax').is(':checked');
    if (isReloadTableOnAjax && ok && data.result) {
        load_tables();
    }
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
        url: "/run_check_prices",
        method: "POST",
        success: on_ajax_success,
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
        url: "/run_check_genres",
        method: "POST",
        success: on_ajax_success,
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
        if (isShowCurAndMaxNumberGames) {
            $('.finished_game_statistic').removeClass("d-none");
            $('.finished_watched_game_statistic').removeClass("d-none");
        } else {
            $('.finished_game_statistic').addClass("d-none");
            $('.finished_watched_game_statistic').addClass("d-none");
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

function fill_statistics() {
    let statistic_1 = statistic_for_table(window.finished_games);
    let statistic_2 = statistic_for_table(window.finished_watched_games);

    $('.finished_game_statistic').html(statistic_1);
    $('.finished_watched_game_statistic').html(statistic_2);

    // Добавление статистики о количестве игр в таблицах
    $('.number_finished_games').text(finished_games.length);
    $('.number_finished_watched_games').text(finished_watched_games.length);
    $('.sum_number_games').text(finished_games.length + finished_watched_games.length);
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

function createTags(elementJQuery, items, tableEl, queryTag) {
    let tagify = new Tagify(elementJQuery[0], {
        whitelist: items,
        enforceWhitelist: true,
        skipInvalid: true,
        dropdown: {
            enabled: 0,
            closeOnSelect: false,
            maxItems: items.length,
        },
        callbacks: {
            // Удаление тега при клике на него
            "click": (e) => e.detail.tagify.removeTags(e.detail.tag),
        },
    });

    tableEl.on('click', queryTag, function () {
        let text = $(this).text();
        tagify.addTags(text);
    });
}

function createFilterOfPlatforms(table, tableEl) {
    // Под колонку платформы добавлен фильтр
    let columnPlatform = table.api().column(COLUMN_PLATFORM);

    let filterPlatform = $('<input placeholder="Платформы...">')
        .appendTo($(columnPlatform.footer()).empty())
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
        });

    let platforms = [];
    columnPlatform
        .data()
        .unique()
        .sort()
        .each(function (d, j) {
            platforms.push(d);
        });

    let commonCallbacks = {
        // Удаление тега при клике на него
        "click": (e) => e.detail.tagify.removeTags(e.detail.tag),
    };

    // Инициализация платформ
    createTags(filterPlatform, platforms, tableEl, '.platform');
}

function createFilterOfGenres(table, tableEl) {
    // Под колонку названия добавлен фильтр по жанрам
    let columnName = table.api().column(COLUMN_NAME);

    // Но поиск будет в колонке деталей - там размещен рендер для поиска жанров
    let columnDetail = table.api().column(COLUMN_DETAIL);

    let filterGenres = $('<input placeholder="Жанры...">')
        .appendTo($(columnName.footer()).empty())
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
        });

    // Заполнение жанров из текущей таблицы
    let uniqueGenres = new Set();
    table.api().rows().every(function (rowIdx, tableLoop, rowLoop) {
        for (let name of this.data().genres) {
            uniqueGenres.add(name);
        }
    });

    let genres = new Array();
    for (let name of Array.from(uniqueGenres).sort()) {
        genres.push({
            value: name,
            searchBy: ALL_GENRES[name].aliases, // Для альтернативного поиска жанров
            title: get_genre_description(name), // Для всплывающих подсказок при наведении мышки
        });
    }

    // Инициализация жанров
    createTags(filterGenres, genres, tableEl, '.genre');
}

function fill_table(table_selector, total_class, items) {
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
        columns: [
            {
                class: 'dt-control',
                orderable: false,
                data: null,
                defaultContent: '',
                render: for_filter_render,
            },
            { title: "Название", data: 'name' },
            { title: "Платформа", data: 'platform', render: platform_render },
            { title: "Дата добавления", data: 'append_date', render: append_date_render },
            { title: "Цена (руб.)", data: 'price', type: 'num', render: price_render },
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
            let column_price = this.api().column(COLUMN_PRICE, {search: 'applied'});
            let total = column_price.data().reduce((a, b) => a + b, 0);
            $(column_price.footer()).html(
                toPrettyPrice(total)
            );

            setVisibleProgress(table_selector, false);
        },
        initComplete: function () {
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

function fill_game_tables() {
    fill_table('#finished_game', 'total_price_finished_games', window.finished_games);
    fill_table('#finished_watched_game', 'total_price_finished_watched_games', window.finished_watched_games);

    // Функция для подсчета итоговых сумм всех игр
    update_total_price_all_tables();

    // Добавление статистики о играх в таблице
    fill_statistics();
}

function callStatisticsByGames(games) {
    let platform_by_total_price = new Map();
    let platform_by_number = new Map();
    let genre_by_number = new Map();
    let genre_by_total_price = new Map();
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
        genre_by_total_price
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

function createOrUpdateCharts(chartId, title, labels, datasets, options) {
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
            type: 'pie',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: thisOptions,
        }
    );
}

function fill_charts() {
    let [
        platform_by_total_price_of_finished_games,
        platform_by_number_of_finished_games,
        total_price_of_finished_games,
        genre_by_number_of_finished_games,
        genre_by_total_price_of_finished_games
    ] = callStatisticsByGames(window.finished_games);
    let [
        platform_by_total_price_of_finished_watched_games,
        platform_by_number_of_finished_watched_games,
        total_price_of_finished_watched_games,
        genre_by_number_of_finished_watched_games,
        genre_by_total_price_of_finished_watched_games
    ] = callStatisticsByGames(window.finished_watched_games);

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
                    window.finished_games.length,
                    window.finished_watched_games.length
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
                maxItems: genres.length,
            },
            callbacks: {
                // Удаление тега при клике на него
                "click": (e) => e.detail.tagify.removeTags(e.detail.tag),

                // Управление состояний кнопок формы
                "change": (e) => updateStatesFormSetGenres(),
            },
        });
    }
}

// Функция загружает все игры, перезаполняет таблицы игр, подсчитывает итого и статистику
function load_tables() {
    // TODO: Переиспользование селекторов таблиц
    setVisibleProgress('#finished_game', true);
    setVisibleProgress('#finished_watched_game', true);

    $.ajax({
        url: '/get_games',
        dataType: "json",  // Тип данных загружаемых с сервера
        success: function(data) {
            console.log(data);

            window.finished_games = data[FINISHED_GAME];
            window.finished_watched_games = data[FINISHED_WATCHED];

            fill_game_tables();
            fill_charts();
        },
        error: data => on_ajax_error(data, 'при загрузке игр'),
    });
}

$(document).ready(function() {
    // По умолчанию, флаги всегда стоят
    $('#checkbox_visible_finished_games').prop('checked', true);
    $('#checkbox_visible_finished_watched_games').prop('checked', true);

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
            success: on_ajax_success,
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
                on_ajax_success(data);

                // Очищение полей формы
                thisForm.reset();
            },
            error: data => on_ajax_error(data, 'при удалении игры'),
        });

        return false;
    });
});
