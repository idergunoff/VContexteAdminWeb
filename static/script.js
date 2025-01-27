async function loadUserVersions(tryingId) {
    try {
        const versionSort = document.querySelector('input[name="version-sort"]:checked').value;
        const versionType = document.querySelector('input[name="version-type"]:checked').value;

        // Отправляем запрос на сервер для получения списка версий
        const response = await fetch(`/versions/${tryingId}?version_sort=${versionSort}&version_type=${versionType}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        }
        const data = await response.json();
        // Очищаем список в третьем блоке и добавляем новые элементы
        const header = document.getElementById('version-header');
        header.setAttribute('data-trying-id', tryingId);
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


document.querySelectorAll('input[name="version-sort"]').forEach(radio => {
    radio.addEventListener('change', () => {
        const header = document.getElementById('version-header');
        const tryingId = header.getAttribute('data-trying-id');
        if (tryingId) {
            loadUserVersions(tryingId);
        }
    });
});


document.querySelectorAll('input[name="version-type"]').forEach(radio => {
    radio.addEventListener('change', () => {
        const header = document.getElementById('version-header');
        const tryingId = header.getAttribute('data-trying-id');
        if (tryingId) {
            loadUserVersions(tryingId);
        }
    });
});


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
        // Проверяем, поддерживает ли устройство сенсорный ввод
        const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints || navigator.msMaxTouchPoints;


        const response = await fetch(`/trying/${wordId}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        }
        const data = await response.json();
        const header = document.getElementById('trying-header');
        header.setAttribute('data-word-id', wordId);
        const userListContainer = document.getElementById('trying-list');
        userListContainer.innerHTML = ''; // очищаем предыдущий список

        if (data.dict_result) {
            header.textContent = `Слово: ${data.word} ${data.date_play} — Всего: ${Object.keys(data.dict_result).length}`;

            for (const [userId, userData] of Object.entries(data.dict_result)) {
                const listItem = document.createElement('li');
                if (isTouchDevice) {
                    listItem.innerHTML = `${userData.text}<br>${userData.title}`;
                } else {
                    listItem.innerHTML = `${userData.text}`;
                    listItem.setAttribute('title', `${userData.title}`);
                };


                listItem.style.backgroundColor = userData.color;

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


document.getElementById('skip-user-btn').addEventListener('click', async () => {
    try {
        const tryingId = document.getElementById('version-header').getAttribute('data-trying-id');
        const wordId = document.getElementById('trying-header').getAttribute('data-word-id');

        // Выполняем POST-запрос на сервер
        const response = await fetch(`/trying/skip/${tryingId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error('Ошибка при отправке данных на сервер');
        }

        const result = await response.json();
        console.log('Ответ сервера:', result);

        // После успешного выполнения вызываем loadUserVersions
        await onWordClick(wordId);
    } catch (error) {
        console.error('Ошибка:', error);
    }
});

