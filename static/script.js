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

async function onWordClick(wordId, getContext) {
    try {
        // Проверяем, поддерживает ли устройство сенсорный ввод
        const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints || navigator.msMaxTouchPoints;
        const tryingSort = document.querySelector('input[name="trying-sort"]:checked').value;

        const response = await fetch(`/trying/${wordId}?trying_sort=${tryingSort}&get_context=${getContext}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        }

        const data = await response.json();

        if (getContext == 1) {
            const headerWord = document.getElementById('word-header');
            headerWord.setAttribute('data-word-id', wordId);
            const wordListContainer = document.getElementById('word-list');
            wordListContainer.innerHTML = ''; // очищаем предыдущий список

            if (data.word_context) {
                headerWord.textContent = `Слово: ${data.word_context.word} id ${data.word_context.id} order ${data.date_play} — Всего: ${data.word_context.context.length}`;


                // Цикл по списку data.context
                data.word_context.context.forEach((item, index) => {
                    const listItem = document.createElement('li');
                    listItem.textContent = `${index}. ${item}`; // Индекс и значение элемента списка
                    setBgItem(index, listItem)
                    listItem.classList.add('word-item');
                    wordListContainer.appendChild(listItem); // Добавляем элемент в список
                });
            }
        }
        const header = document.getElementById('trying-header');
        header.setAttribute('data-word-id', wordId);
        const userListContainer = document.getElementById('trying-list');
        userListContainer.innerHTML = ''; // очищаем предыдущий список

        if (data.dict_result) {
            header.innerHTML = data.text_header;

//            for (const [userId, userData] of Object.entries(data.dict_result)) {
            data.dict_result.forEach((userData, index) => {
                const listItem = document.createElement('li');
                if (isTouchDevice) {
                    listItem.innerHTML = `${index + 1}. ${userData.text}<br>${userData.title}`;
                } else {
                    listItem.innerHTML = `${index + 1}. ${userData.text}`;
                    listItem.setAttribute('title', `${userData.title}`);
                };

                listItem.setAttribute('data-trying-id', userData.t_id);
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


async function wordsByMonth(selectedMonth) {
    try {
        const response = await fetch(`/month_word/${selectedMonth}`);  // Запрос к серверу
        if (!response.ok) throw new Error('Ошибка при загрузке данных');
        const data = await response.json();

        renderWordList(data.words, selectedMonth);
    } catch (error) {
        console.error('Ошибка:', error);
    }
}


function renderWordList(words, selectedMonth) {
    const wordList = document.getElementById('word-list');
    wordList.innerHTML = '';

    if (!words || words.length === 0) {
        wordList.innerHTML = '<li>Нет слов за выбранный месяц</li>';
        return;
    }

    words.forEach((word) => {
        const listItem = document.createElement('li');
        listItem.textContent = `${word.order}. ${word.fact || ''}${word.word}`;
        listItem.addEventListener('click', function () {
            if (selectedMonth === 'new') {
                onNewWordClick(word.id);
            } else {
                onWordClick(word.id, 1);
            }
        });
        wordList.appendChild(listItem);
    });
}


// Добавляем обработчик события для выпадающего списка
document.getElementById('dropdown').addEventListener('change', async function () {
    const selectedMonth = this.value;  // Получаем выбранное значение (месяц)
    wordsByMonth(selectedMonth);
});


document.getElementById('words-back-btn').addEventListener('click', async () => {
    const selectedMonth = document.getElementById('dropdown').value;
    wordsByMonth(selectedMonth);
});


async function handleMoveWordClick() {
    try {
        const wordHeader = document.getElementById('word-header');
        if (!wordHeader) {
            return;
        }
document.getElementById('move-word-btn').addEventListener('click', async () => {
    try {
        const wordHeader = document.getElementById('word-header');
        const wordId = wordHeader.getAttribute('data-word-id');
        if (!wordId) {
            return;
        }

        const orderInput = document.getElementById('word-order-input');
        if (!orderInput) {
            return;
        }
        const newOrder = parseInt(orderInput.value, 10);
        if (Number.isNaN(newOrder)) {
            return;
        }

        const selectedMonth = document.getElementById('dropdown').value;
        const includeWords = selectedMonth === 'new';

        const response = await fetch('/word/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                word_id: Number(wordId),
                new_order: newOrder,
                include_words: includeWords,
            }),
        });

        if (!response.ok) {
            throw new Error('Ошибка при перемещении слова');
        }

        const data = await response.json();

        if (data.status === 'skipped') {
            return;
        }

        if (data.word && typeof data.word.order === 'number') {
            orderInput.value = data.word.order;
        }

        if (includeWords) {
            if (data.words) {
                renderWordList(data.words, selectedMonth);
            } else {
                await wordsByMonth(selectedMonth);
            }
            await onNewWordClick(Number(wordId));
        } else {
            await onWordClick(Number(wordId), 1);
        }
    } catch (error) {
        console.error('Ошибка при перемещении слова:', error);
    }
}

const moveWordBtn = document.getElementById('move-word-btn');
if (moveWordBtn) {
    moveWordBtn.addEventListener('click', handleMoveWordClick);
}
});


document.querySelectorAll('input[name="trying-sort"]').forEach(radio => {
    radio.addEventListener('change', () => {
        const header = document.getElementById('trying-header');
        const wordId = header.getAttribute('data-word-id');
        if (wordId) {
            onWordClick(wordId, 0);
        }
    });
});


function findListItemByTryingId(tryingId) {
    return document.querySelector(`li[data-trying-id="${tryingId}"]`);
}


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

        if (result) {
            const listItem = findListItemByTryingId(result.trying_id);
            listItem.style.backgroundColor = result.color;
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
});


document.getElementById('alpha-user-btn').addEventListener('click', async () => {
        const tryingId = document.getElementById('version-header').getAttribute('data-trying-id');
        const wordId = document.getElementById('trying-header').getAttribute('data-word-id');

    try {
        const response = await fetch(`/user_alpha/${tryingId}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        } else {
            onWordClick(wordId, 0)
        }

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
});


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


async function controlAiListItems() {
    try {
        const userListContainer = document.getElementById('trying-list');
        const listItems = userListContainer.querySelectorAll('li'); // Получаем все элементы списка

        if (listItems.length === 0) {
            console.log('Список пуст');
            return;
        }

        for (const listItem of listItems) {
            const tryingId = listItem.getAttribute('data-trying-id'); // Получаем data-trying-id

            if (!tryingId) {
                console.warn(`Пропущен элемент без атрибута data-trying-id`);
                continue;
            }

            // Отправляем запрос на сервер
            const response = await fetch(`/trying/control_ai/${tryingId}`);
            if (!response.ok) {
                throw new Error(`Ошибка при обновлении данных для tryingId: ${tryingId}`);
            }

            const data = await response.json(); // Получаем ответ от сервера
            const newValue = data.text || 'Нет данных'; // Используем значение из ответа или placeholder

            // Добавляем новое значение в элемент списка
            listItem.innerHTML += `<br>${newValue}`;
        }
    } catch (error) {
        console.error('Ошибка при обновлении списка:', error);
    }
}


// Привязываем функцию к кнопке
document.getElementById('control-ai-btn').addEventListener('click', controlAiListItems);


document.getElementById('graph-vers-btn').addEventListener('click', async () => {
    const tryingId = document.getElementById('version-header').getAttribute('data-trying-id');

    try {
        window.open(`/graph_vers/${tryingId}`, '_blank');

    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить график');
    }
});

document.getElementById('graph-user-btn').addEventListener('click', async () => {
    const tryingId = document.getElementById('version-header').getAttribute('data-trying-id');

    try {
        window.open(`/graph_trying/${tryingId}`, '_blank');

    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить график');
    }
});


document.getElementById('trying-graph-btn').addEventListener('click', async () => {
    const wordId = document.getElementById('trying-header').getAttribute('data-word-id');

    try {
        window.open(`/graph_word/${wordId}`, '_blank');

    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить график');
    }
});


document.getElementById('trying-distr-btn').addEventListener('click', async () => {
    const wordId = document.getElementById('trying-header').getAttribute('data-word-id');

    try {
        window.open(`/graph_distr_trying/${wordId}`, '_blank');

    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить график');
    }
});


document.getElementById('word-fact-btn').addEventListener('click', async () => {
    const wordId = document.getElementById('word-header').getAttribute('data-word-id');

    try {
        window.open(`/word_fact/${wordId}`, '_blank');

    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить страницу с фактами о слове');
    }
});

// DUEL
document.getElementById('duel-btn').addEventListener('click', () => {
    window.open('/duel', '_blank');
});


document.getElementById('search-word').addEventListener('input', () => {
    const searchValue = document.getElementById('search-word').value.toLowerCase().trim();
    if (!searchValue) return;

    const listItems = document.querySelectorAll('#word-list li');

    for (const item of listItems) {
        // Отделяем текст после первой точки
        const match = item.textContent.match(/^\s*\d+\.\s*(.*)$/);
        if (match) {
            const word = match[1].toLowerCase(); // Берем только слово
            if (word === searchValue) {
                item.scrollIntoView({ behavior: 'smooth', block: 'start' });
                break;
            }
        }
    }
});


document.getElementById('first-words-btn').addEventListener('click', async () => {
    const tryingId = document.getElementById('version-header').getAttribute('data-trying-id');
    try {
        const response = await fetch(`/first_word/${tryingId}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        }
        const data = await response.json();

        const versionList = document.getElementById('version-list');
        versionList.innerHTML = ''; // Очищаем предыдущий список

        if (data) {
            const header = document.getElementById('version-header')
            header.textContent = `${data.statistics}`;

            data.result.forEach((userData, index) => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `${userData.text}`;

                listItem.style.backgroundColor = userData.color;

                versionList.appendChild(listItem);
            });
        } else {
            userListContainer.innerHTML = '<li>Нет данных по этому слову</li>';
        }
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
});

document.getElementById('reset-ai-btn').addEventListener('click', async () => {
    const header = document.getElementById('trying-header');
    const wordId = header.getAttribute('data-word-id');

    try {
        const response = await fetch(`/reset_ai/${wordId}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        } else {
            onWordClick(wordId, 0)
        }

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
});


// CONTROL AI

document.getElementById("toggle-panel").onclick = () => {
  updateListTryingTrainAI();
  document.getElementById("label-panel").classList.toggle("show");
};


async function updateListTryingTrainAI() {
    try {
        const response = await fetch(`/control_ai/update_list`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        }
        const data = await response.json();

        const listTrue = document.getElementById('true-list');
        listTrue.innerHTML = '';
        const listFalse = document.getElementById('false-list');
        listFalse.innerHTML = '';

        document.getElementById("true-count").textContent = data.count_true;
        document.getElementById("false-count").textContent = data.count_false;

        if (data.list_true.length > 0) {
            data.list_true.forEach((trying, index) => {
                const listItem = document.createElement('li');
                listItem.textContent = `${index + 1}. ${trying[0]}`;
                listItem.addEventListener('click', function () {
                    onControlTryingClick(trying[1]);
                });
                listTrue.appendChild(listItem);
            });
        } else {
            listTrue.innerHTML = '<li>Нет данных</li>';
        }
        if (data.list_false.length > 0) {
            data.list_false.forEach((trying, index) => {
                const listItem = document.createElement('li');
                listItem.textContent = `${index + 1}. ${trying[0]}`;
                listItem.addEventListener('click', function () {
                    onControlTryingClick(trying[1]);
                });
                listFalse.appendChild(listItem);
            });
        } else {
            listFalse.innerHTML = '<li>Нет данных</li>';
        }
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}


async function getWordIdByTryingId(tryingId) {
    try {
        const response = await fetch(`/get_word_id_by_trying_id/${tryingId}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        }
        const data = await response.json();
        return data.word_id;
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}


async function onControlTryingClick(tryingId) {
    loadUserVersions(tryingId);
    const wordId = await getWordIdByTryingId(tryingId);
    onWordClick(wordId, 1)
}

let trueCount = 0;
let falseCount = 0;

function updateCount() {
  document.getElementById("true-count").textContent = trueCount;
  document.getElementById("false-count").textContent = falseCount;
}

async function addTrue() {
    const tryingId = document.getElementById('version-header').getAttribute('data-trying-id');

    const response = await fetch(`/control_ai/add_trying_true/${tryingId}`);
    if (!response.ok) {
        throw new Error('Ошибка при загрузке данных');
    }
    const data = await response.json();
    showCustomAlert(data.message);
    updateListTryingTrainAI();
}

async function removeTrue() {
  const tryingId = document.getElementById('version-header').getAttribute('data-trying-id');

  const response = await fetch(`/control_ai/rm_trying/${tryingId}`);
  if (!response.ok) {
      throw new Error('Ошибка при загрузке данных');
  }
  const data = await response.json();
  showCustomAlert(data.message);
  updateListTryingTrainAI();
}


async function addFalse() {
    const tryingId = document.getElementById('version-header').getAttribute('data-trying-id');

    const response = await fetch(`/control_ai/add_trying_false/${tryingId}`);
    if (!response.ok) {
        throw new Error('Ошибка при загрузке данных');
    }
    const data = await response.json();
    showCustomAlert(data.message);
    updateListTryingTrainAI();
}


async function removeFalse() {
  const tryingId = document.getElementById('version-header').getAttribute('data-trying-id');

  const response = await fetch(`/control_ai/rm_trying/${tryingId}`);
  if (!response.ok) {
      throw new Error('Ошибка при загрузке данных');
  }
  const data = await response.json();
  showCustomAlert(data.message);
  updateListTryingTrainAI();
}

function train() {
    try {
        window.open(`/control_ai/training`, '_blank');

    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить график');
    }
}

async function autoAddTrue() {
  const count = parseInt(document.getElementById("auto-count").value);
  const response = await fetch(`/control_ai/auto_add_trying_true/${count}`);
  if (!response.ok) {
      throw new Error('Ошибка при загрузке данных');
  }
  const data = await response.json();
  showCustomAlert(data.message);
  updateListTryingTrainAI();
}

async function autoAddFalse() {
  const count = parseInt(document.getElementById("auto-count").value);
  const response = await fetch(`/control_ai/auto_add_trying_false/${count}`);
  if (!response.ok) {
      throw new Error('Ошибка при загрузке данных');
  }
  const data = await response.json();
  showCustomAlert(data.message);
  updateListTryingTrainAI();
}


function showCustomAlert(message) {
  const modal = document.createElement('div');
  modal.style.position = 'fixed';
  modal.style.left = '0'; modal.style.top = '0';
  modal.style.width = '100vw'; modal.style.height = '100vh';
  modal.style.background = 'rgba(0,0,0,0.4)';
  modal.style.display = 'flex'; modal.style.alignItems = 'center'; modal.style.justifyContent = 'center';
  modal.innerHTML = `
    <div style="background:#fff;padding:20px 40px;border-radius:8px;box-shadow:0 0 16px #222">
      <p>${message}</p>
      <button id="close-modal-btn">OK</button>
    </div>`;
  document.body.appendChild(modal);
  document.getElementById('close-modal-btn').onclick = () => document.body.removeChild(modal);
}


async function saveModel() {
    const response = await fetch(`/control_ai/save_model`);
    if (!response.ok) {
        throw new Error('Ошибка при загрузке данных');
    }
    const data = await response.json();
    showCustomAlert(data.message);
}