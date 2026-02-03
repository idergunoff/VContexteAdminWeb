function logout() {
    window.location.href = "/logout";
}

function setBgItem(index, listItem) {
    if (index >= 5000) {
        listItem.style.backgroundColor = '#f4bcfe';
    } else if (index >= 2500 && index < 5000) {
        listItem.style.backgroundColor = '#aad5ff';
    } else if (index >= 500 && index < 2500) {
        listItem.style.backgroundColor = '#d6ffab';
    } else if (index >= 100 && index < 500) {
        listItem.style.backgroundColor = '#ffffbf';
    } else if (index >= 20 && index < 100) {
        listItem.style.backgroundColor = '#ffc673';
    } else if (index >= 0 && index < 20) {
        listItem.style.backgroundColor = '#ff9f98';
    }
}

function renderContext(idxList, context) {
    const contextList = document.getElementById('ai-context-list');
    const header = document.getElementById('ai-context-header');
    contextList.innerHTML = '';

    if (!idxList || idxList.length === 0) {
        contextList.innerHTML = '<li>Нет данных для отображения</li>';
        header.textContent = 'Контекст';
        return;
    }

    header.textContent = `Контекст — Всего: ${idxList.length}`;

    idxList.forEach((idx, index) => {
        const word = context?.[idx] ?? '';
        const listItem = document.createElement('li');
        listItem.textContent = `${index + 1}. ${word} (${idx})`;
        setBgItem(idx, listItem);
        contextList.appendChild(listItem);
    });
}

function renderEntries(entries, context) {
    const list = document.getElementById('ai-trying-list');
    list.innerHTML = '';

    if (!entries || entries.length === 0) {
        list.innerHTML = '<li>Нет записей для выбранного слова</li>';
        return;
    }

    entries.forEach((entry, index) => {
        const idxList = Array.isArray(entry.idx) ? entry.idx : [];
        const firstWord = idxList.length > 0 ? (context?.[idxList[0]] ?? '') : '';
        const label = `${idxList.length} ${firstWord}`.trim();
        const listItem = document.createElement('li');
        listItem.textContent = `${index + 1}. ${label}`;
        listItem.classList.add('word-item');
        listItem.addEventListener('click', () => renderContext(idxList, context));
        list.appendChild(listItem);
    });
}

async function loadAiTrying(wordId) {
    if (!wordId) {
        return;
    }

    try {
        const response = await fetch(`/ai_trying/word/${wordId}`);
        if (!response.ok) {
            throw new Error('Ошибка при загрузке данных');
        }
        const data = await response.json();
        const header = document.getElementById('ai-word-header');
        const word = data.word || {};
        const context = word.context || [];
        const entries = data.entries || [];

        header.textContent = `Слово: ${word.word ?? ''} id ${word.id ?? ''} — Всего: ${entries.length}`;
        renderEntries(entries, context);
        renderContext([], []);
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}

const wordSelect = document.getElementById('ai-word-select');
if (wordSelect) {
    wordSelect.addEventListener('change', () => {
        loadAiTrying(wordSelect.value);
    });

    if (wordSelect.value) {
        loadAiTrying(wordSelect.value);
    }
}
