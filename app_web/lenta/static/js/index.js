const not_found_class = "not_found";

const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent);

const $filterPlatform = $('#filter-by-platform-select');
const $filterCategory = $('#filter-by-category-select');


function search(init=false, search_from_id=null) {
    let search_text = $('#search').val().toLowerCase();

    let filteredPlatforms = $filterPlatform.val() || [];
    let filteredCategories = $filterCategory.val() || [];

    let numberOfFilters = filteredPlatforms.length + filteredCategories.length;
    let is_empty = search_text.length == 0 && numberOfFilters == 0;

    // Если функция вызвана при прогрузке страницы и текста в поиске нет,
    // то ничего не делаем -- по умолчанию все элементы и так видимые
    if (init && is_empty) {
        return;
    }

    // При очистке строки поиска, убираем класс у всех не найденных ранее элементов
    if (is_empty) {
        $('.' + not_found_class).removeClass(not_found_class);
    }

    let query = '.media.game';
    if (search_from_id != null) {
        query = `#${search_from_id} ${query}`;
    }

    console.log(`Call search "${search_text}", using "${query}", platforms: [${filteredPlatforms}], categories: [${filteredCategories}]`);

    let $buttonFilter = $("#button-filter");
    let $buttonFilterIcon = $buttonFilter.find(".icon");
    let $buttonFilterValue = $buttonFilter.find(".value");

    if (numberOfFilters > 0) {
        $buttonFilterValue.text(numberOfFilters);

        $buttonFilterIcon.hide();
        $buttonFilterValue.show();
    } else {
        $buttonFilterIcon.show();
        $buttonFilterValue.hide();
    }

    let day_by_games = new Map();

    $(query).each(function() {
        let $game = $(this);
        let $day = $game.parent().parent()
        let day_value = $day.find('.day').text();

        let text = day_value + $game.text().replace(/\s\s+/g, ' ').trim().toLowerCase();

        let platform = $game.attr("data-platform");
        let category = $game.attr("data-category");

        let is_visible = text.includes(search_text)
            && (filteredPlatforms.length == 0 || filteredPlatforms.includes(platform))
            && (filteredCategories.length == 0 || filteredCategories.includes(category))
        ;

        $game.toggleClass(not_found_class, !is_visible);

        // Если хоть одна игра видима, то показываем блок ее карточки
        // Иначе, если уже был поиск и ее карточка была скрыта, то при проверке
        // видимости игры она не будет показана, т.к. ее карточка скрыта
        if (is_visible) {
            $day.removeClass(not_found_class);
        }

        let day_el_dom = $day[0];
        if (!day_by_games.has(day_el_dom)) {
            day_by_games.set(day_el_dom, []);
        }

        day_by_games.get(day_el_dom).push($game);
    });

    for (let [day_el_dom, games] of day_by_games) {
        let number_visible = 0;
        for (let $game of games) {
            if (!$game.hasClass(not_found_class)) {
                number_visible++;
            }
        }
        $(day_el_dom).toggleClass(not_found_class, number_visible == 0);
    }

    let total_number_visible = 0;
    $('.collapse[data-year]').each(function() {
        let $collapse = $(this);

        let number_visible = 0;
        $collapse.find('.game').each(function() {
            let $game = $(this);
            if (!$game.hasClass(not_found_class)) {
                number_visible++;
            }
        });
        total_number_visible += number_visible;

        $collapse.find('.no_results').toggleClass('hide', number_visible > 0);

        let $year_filtered = $collapse.parent().find(".filtered");
        $year_filtered.toggleClass('hide', is_empty);
        $year_filtered.find(".number").text(number_visible);
    });

    let $stats_found_game = $("#stats_found_game");
    $stats_found_game.text(total_number_visible);
    $stats_found_game.parent().toggleClass('hide', is_empty);
}

$(function() {
    // Использование нативного меню для выбора элементов
    if (isMobile) {
        $('.selectpicker').selectpicker('mobile');
    }

    // Загрузка остальных годов
    $(".card:has(.not-loaded)").each(function() {
        let $card = $(this);

        let $progress = $card.find(".progress");
        $progress.removeClass('hide');

        let $body = $card.find(".not-loaded");

        let $collapse = $card.find(".collapse.multi-collapse");
        let year = $card.find("[data-year]").data("year");

        $.get(
            '/lenta/year/' + year,
            function(data) {
                $body.html(data);
                $body.removeClass('not-loaded');

                // Применение поиска на только что подгруженные игры
                search(true, $collapse.attr('id'));

                $progress.addClass('hide');
            }
        );
    });

    $('#clear_search').click(function() {
        $('#search').val('');
        search();
    });

    let typingTimer = null; // Timer identifier
    const doneTypingInterval = 300; // Time in ms

    $('#search').on('input', function() {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(search, doneTypingInterval);
    });

    search(true);

    // Copy text by double click
    $(".card").on("dblclick", ".media.game > .media-body", function() {
        let text = $(this).find('.name').text();

        // SOURCE: https://stackoverflow.com/a/48948114/5909792
        $("<textarea/>")
            .appendTo("body")
            .val(text)
            .select()
            .each(() => document.execCommand('copy'))
            .remove();

        noty({
            text: 'Скопировано в буфер обмена',
            type: 'success',
            layout: 'bottomCenter',
            timeout: 2000,
        });
    });
});
