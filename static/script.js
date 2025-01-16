async function loadUserVersions(tryingId) {
    try {
        // Отправляем запрос на сервер для получения списка версий
        const response = await fetch(`/versions/${tryingId}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        }
        const data = await response.json();
        // Очищаем список в третьем блоке и добавляем новые элементы
        const header = document.getElementById('version-header');
        const versionList = document.getElementById('version-list');
        versionList.innerHTML = ''; // Очищаем предыдущий список
        if (data.versions.length > 0) {
            // Обновляем заголовок с именем пользователя и количеством версий
            header.textContent = `Версии пользователя: ${data.username} — Всего: ${data.count_vers}`;

            data.versions.forEach((version, index) => {
                const listItem = document.createElement('li');
                listItem.textContent = `${version.text}`;
                listItem.style.backgroundColor = version.bg_color;
                versionList.appendChild(listItem);
            });
        } else {
            versionList.innerHTML = '<li>Нет версий для данного пользователя</li>';
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
}


function setBgItem(index, listItem) {
    if (index >= 5000) {
        listItem.style.backgroundColor = '#f4bcfe';  // Светло-фиолетовый
    } else if (index >= 2500 && index < 5000) {
        listItem.style.backgroundColor = '#aad5ff';  // Голубой
    } else if (index >= 500 && index < 2500) {
        listItem.style.backgroundColor = '#d6ffab';  // Светло-зеленый
    } else if (index >= 100 && index < 500) {
        listItem.style.backgroundColor = '#ffffbf';  // Желтый
    } else if (index >= 20 && index < 100) {
        listItem.style.backgroundColor = '#ffc673';  // Оранжевый
    } else if (index >= 0 && index < 20) {
        listItem.style.backgroundColor = '#ff9f98';  // Красный
    }
}

function logout() {
    // Выполняем выход
    window.location.href = "/logout";  // Переход на маршрут выхода
}


async function onWordClick(wordId) {
    try {
        const response = await fetch(`/trying/${wordId}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        }
        const data = await response.json();
        const header = document.getElementById('trying-header');
        const userListContainer = document.getElementById('trying-list');
        userListContainer.innerHTML = ''; // очищаем предыдущий список

        if (data.dict_result) {
            header.textContent = `Слово: ${data.word} ${data.date_play} — Всего: ${Object.keys(data.dict_result).length}`;

            for (const [userId, userData] of Object.entries(data.dict_result)) {
                const listItem = document.createElement('li');
                listItem.setAttribute('title', `Зарегистрирован: ${userData.date_register}`);

                listItem.style.backgroundColor = userData.skip ? '#ffbfbf' : userData.done_tt ? '#45ece7': userData.done ? '#bfffbf' : '#f7faa6';

                let innerHTML = '';

                if (userData.user_day) innerHTML += '🕺';
                if (userData.user_remind) innerHTML += '🔔';
                innerHTML += `<strong>${userData.username}</strong> - 📦${userData.count_vers}`;

                if (userData.hint > 0) innerHTML += ` 🧿${userData.hint}`;
                if (userData.hint_allusion) innerHTML += ' 💎';
                if (userData.hint_center) innerHTML += ' 🌎';
                if (userData.hint_word_pixel) innerHTML += ' 🖼️';
                if (userData.hint_word_tail) innerHTML += ' 🦎';
                if (userData.hint_word_metr) innerHTML += ' 📏';

                innerHTML += `<br>`;
                if (userData.tt_id) {
                    innerHTML += `🐛${userData.count_vers_tt}(${userData.count_word_tt})`;
                    if (userData.hint_top_ten) innerHTML += ' 🍤';
                }

                listItem.innerHTML = innerHTML;
                listItem.addEventListener('click', () => loadUserVersions(userData.t_id));
                userListContainer.appendChild(listItem);
            }
        } else {
            userListContainer.innerHTML = '<li>Нет данных по этому слову</li>';
        }
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}

// Добавляем обработчик события для выпадающего списка
document.getElementById('dropdown').addEventListener('change', async function () {
    const selectedMonth = this.value;  // Получаем выбранное значение (месяц)

    try {
        const response = await fetch(`/month_word/${selectedMonth}`);  // Запрос к серверу
        if (!response.ok) throw new Error('Ошибка при загрузке данных');
        const data = await response.json();

        const wordList = document.getElementById('word-list');  // Список слов ниже
        wordList.innerHTML = '';  // Очищаем список перед обновлением

        if (data.words.length > 0) {
            data.words.forEach((word, index) => {
                const listItem = document.createElement('li');
                listItem.textContent = `${word.order}. ${word.word}`;
                listItem.classList.add('word-item');  // Добавляем класс для стилей
                listItem.addEventListener('click', function () {
                    onWordClick(word.id);  // Вызываем функцию при клике на слово
                });
                wordList.appendChild(listItem);  // Добавляем слово в список
            });
        } else {
            wordList.innerHTML = '<li>Нет слов за выбранный месяц</li>';
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
});

