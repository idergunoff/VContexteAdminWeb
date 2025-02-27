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

// Main


function logout() {
    // Выполняем выход
    window.location.href = "/logout";  // Переход на маршрут выхода
}

// WORD

async function onWordClick(wordId) {
    try {
        // Проверяем, поддерживает ли устройство сенсорный ввод
        const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints || navigator.msMaxTouchPoints;
        const tryingSort = document.querySelector('input[name="trying-sort"]:checked').value;

        const response = await fetch(`/trying/${wordId}?trying_sort=${tryingSort}`);
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

//            for (const [userId, userData] of Object.entries(data.dict_result)) {
            data.dict_result.forEach((userData, index) => {
                const listItem = document.createElement('li');
                if (isTouchDevice) {
                    listItem.innerHTML = `${index}. ${userData.text}<br>${userData.title}`;
                } else {
                    listItem.innerHTML = `${index}. ${userData.text}`;
                    listItem.setAttribute('title', `${userData.title}`);
                };


                listItem.style.backgroundColor = userData.color;

                listItem.addEventListener('click', () => loadUserVersions(userData.t_id));
                userListContainer.appendChild(listItem);
            });
        } else {
            userListContainer.innerHTML = '<li>Нет данных по этому слову</li>';
        }
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}


async function onNewWordClick(wordId) {
    try {
        const response = await fetch(`/word/${wordId}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        }
        const data = await response.json();
        const header = document.getElementById('word-header');
        header.setAttribute('data-word-id', wordId);
        const wordListContainer = document.getElementById('word-list');
        wordListContainer.innerHTML = ''; // очищаем предыдущий список

        if (data) {
            header.textContent = `Слово: ${data.word} id ${data.id} order ${data.order} — Всего: ${data.context.length}`;

            // Цикл по списку data.context
            data.context.forEach((item, index) => {
                const listItem = document.createElement('li');
                listItem.textContent = `${index}. ${item}`; // Индекс и значение элемента списка
                setBgItem(index, listItem)
                listItem.classList.add('word-item');
                wordListContainer.appendChild(listItem); // Добавляем элемент в список
            });
            } else {
                wordListContainer.innerHTML = '<li>Нет данных по этому слову</li>';
            }
        } catch (error) {
            console.error('Ошибка загрузки данных:', error);
        }
        // Вызываем функцию для добавления обработчиков
        enableDragAndDrop();
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
                listItem.addEventListener('click', function () {
                    if (selectedMonth === 'new') {
                        onNewWordClick(word.id);  // Вызываем другую функцию
                    } else {
                        onWordClick(word.id);  // Вызываем стандартную функцию
                    }
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



document.querySelectorAll('input[name="trying-sort"]').forEach(radio => {
    radio.addEventListener('change', () => {
        const header = document.getElementById('trying-header');
        const wordId = header.getAttribute('data-word-id');
        if (wordId) {
            onWordClick(wordId);
        }
    });
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



//let draggedItem = null;  // Хранит элемент, который перетаскивается
//
//function enableDragAndDrop() {
//    const listItems = document.querySelectorAll('#word-list li');
//
//    listItems.forEach(item => {
//        item.setAttribute('draggable', 'true');  // Делаем элементы списка перетаскиваемыми
//
//        item.addEventListener('dragstart', function (event) {
//            draggedItem = event.target;  // Запоминаем элемент
//            event.target.style.opacity = '0.5';  // Задаём прозрачность
//        });
//
//        item.addEventListener('dragover', function (event) {
//            event.preventDefault();  // Разрешаем сброс элемента
//        });
//
//        item.addEventListener('drop', function (event) {
//            event.preventDefault();
//            if (draggedItem !== event.target) {
//                const parent = event.target.parentNode;
//
//                // Переставляем элементы
//                parent.insertBefore(draggedItem, event.target.nextSibling);
//
//                // Обновляем данные на сервере
//                updatedContext();
//            }
//        });
//
//        item.addEventListener('dragend', function () {
//            draggedItem.style.opacity = '1';  // Восстанавливаем прозрачность
//            draggedItem = null;  // Сбрасываем перетаскиваемый элемент
//        });
//    });
//}

document.addEventListener('DOMContentLoaded', function() {
    const wordList = document.getElementById('word-list');

    new Sortable(wordList, {
        animation: 150,  // Плавная анимация
        delay: 800,
        delayOnTouchOnly: true,
        touchStartThreshold: 15,
        supportPointer: false,
        ghostClass: 'sortable-ghost',  // Класс для стилизации перетаскиваемого элемента
        onEnd: function(evt) {
            console.log("Элемент перемещён:", evt.item.textContent);
            updatedContext();  // Вызываем функцию обновления порядка
        }
    });
});


// Функция для отправки обновлённого порядка элементов на сервер
function updatedContext() {
    const wordId = document.getElementById('word-header').getAttribute('data-word-id');
    const items = document.querySelectorAll('#word-list li');
    const updatedContext = Array.from(items).map((item, index) => {
        return {
            word_text: item.textContent,
            new_position: index
        };
    });

    console.log('Обновлённый порядок:', updatedContext);  // Для проверки порядка в консоли

// Отправка данных на сервер
    fetch(`/update-context/${wordId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order: updatedContext })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Порядок обновлён на сервере:', data);
        return onNewWordClick(wordId);  // Правильный вызов функции
    })
    .catch(error => console.error('Ошибка при обновлении порядка:', error));
}

