function logout() {
    window.location.href = '/logout';
}

document.getElementById('duels-back-btn').addEventListener('click', () => {
    window.location.href = '/admin';
});


const currentDuelMeta = {
    id: null,
    wordId: null,
    word: '',
    participants: [],
};


function createDuelListItem(duel) {
    const listItem = document.createElement('li');

    const header = document.createElement('div');
    header.textContent = `${duel.date}. ${duel.word}`;
    listItem.appendChild(header);

    const participants = Array.isArray(duel.participants) ? duel.participants : [];

    const firstLine = document.createElement('div');
    const first = participants[0];
    if (first) {
        firstLine.textContent = `${first.name} (${first.version_count})${duel.winner_id === first.id ? ' 👑' : ''}`;
        listItem.appendChild(firstLine);
    }

    const second = participants.find((p, idx) => idx !== 0);
    if (second) {
        const secondLine = document.createElement('div');
        secondLine.textContent = `${second.name} (${second.version_count})${duel.winner_id === second.id ? ' 👑' : ''}`;
        listItem.appendChild(secondLine);
    }

    listItem.title = `Начало: ${duel.start_time}\nКонец: ${duel.end_time}\nДлительность: ${duel.duration} минут`;

    listItem.dataset.duelId = duel.id;
    listItem.addEventListener('click', () => loadDuelVersions(duel.id));

    return listItem;
}


function renderDuelList(target, duels) {
    target.innerHTML = '';
    if (duels.length > 0) {
        duels.forEach((duel) => {
            target.appendChild(createDuelListItem(duel));
        });
    } else {
        target.innerHTML = '<li>Нет дуэлей</li>';
    }
}


async function duelsByMonth(selectedMonth) {
    try {
        const response = await fetch(`/duel/month/${selectedMonth}`);
        if (!response.ok) throw new Error('Ошибка при загрузке данных');
        const data = await response.json();

        const duelList = document.getElementById('duel-list');
        duelList.innerHTML = '';

        if (data.duels.length > 0) {
            data.duels.forEach(duel => {
                const listItem = createDuelListItem(duel);
                duelList.appendChild(listItem);
            });
        } else {
            duelList.innerHTML = '<li>Нет дуэлей за выбранный месяц</li>';
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

document.getElementById('dropdown').addEventListener('change', function () {
    const selectedMonth = this.value;
    duelsByMonth(selectedMonth);
});

async function loadDuelVersions(duelId) {
    try {
        const sort = document.querySelector('input[name="duel-version-sort"]:checked').value;
        const response = await fetch(`/duel/versions/${duelId}?sort=${sort}`);
        if (!response.ok) throw new Error('Ошибка при загрузке данных');
        const data = await response.json();

        const header = document.getElementById('duel_vers-header');
        header.dataset.duelId = duelId;
        const total = data.count_vers ?? data.count ?? (data.versions ? data.versions.length : 0);
        if (data.word) {
            header.textContent = `Версии дуэли: ${data.word} — Всего: ${total}`;
        } else {
            header.textContent = `Версии дуэли — Всего: ${total}`;
        }

        currentDuelMeta.id = duelId;
        currentDuelMeta.wordId = data.word_id ?? null;
        currentDuelMeta.word = data.word ?? '';
        currentDuelMeta.participants = Array.isArray(data.participants) ? data.participants : [];

        const infoBlock = document.getElementById('duel-info');
        if (infoBlock) {
            const versionStats = new Map();
            if (Array.isArray(data.versions)) {
                data.versions.forEach(v => {
                    const stats = versionStats.get(v.user_id) || { total: 0, improved: 0 };
                    stats.total += 1;
                    if (v.progress && v.progress > 0) stats.improved += 1;
                    versionStats.set(v.user_id, stats);
                });
            }

            const lines = [];
            if (data.word) lines.push(`🖋 ${data.word}`); // 🖋
            if (data.date) lines.push(`📅 ${data.date}`); // 📅
            lines.push(`🕛 ${data.start_time || ''} / 🏁 ${data.end_time || ''}`); // 🕛 / 🏁
            if (Array.isArray(data.participants)) {
                data.participants.forEach(p => {
                    const stats = versionStats.get(p.id) || { total: p.version_count ?? 0, improved: 0 };
                    const total = p.version_count ?? stats.total ?? 0;
                    const improved = stats.improved ?? 0;
                    const notImproved = Math.max(total - improved, 0);
                    const ratingParts = [];
                    if (p.du_r !== null && p.du_r !== undefined) {
                        ratingParts.push(p.du_r);
                    }
                    if (p.vp !== null && p.vp !== undefined) {
                        ratingParts.push(p.vp);
                    }
                    const ratingSuffix = ratingParts.length ? `-${ratingParts.join('-')}` : '';

                    const vpParts = [];
                    if (typeof p.vp_progress === 'number') {
                        vpParts.push(`🚀${p.vp_progress}`);
                    }
                    if (typeof p.vp_efficiency === 'number') {
                        vpParts.push(`⚡${p.vp_efficiency}`);
                    }
                    if (typeof p.vp_quality_penalty === 'number') {
                        vpParts.push(`⚠️${p.vp_quality_penalty}`);
                    }

                    const vpDetails = vpParts.length ? ` (${vpParts.join(' / ')})` : '';

                    lines.push(`${data.winner_id === p.id ? ' 👑' : ''}👥 ${p.name}${ratingSuffix} (${total} 👍${improved}/👎${notImproved})`);
                    lines.push(`💰${p.coins} 🏆${p.vp_delta} 🎖${p.du_r_delta}`);
                    if (vpDetails) {
                        lines.push(`↳ VP: ${vpDetails}`);
                    }
                });
            }
            infoBlock.innerHTML = lines.map(l => `<div>${l}</div>`).join('');
        }

        const list = document.getElementById('duel_vers-list');
        list.innerHTML = '';
        if (data.versions && data.versions.length > 0) {
            data.versions.forEach((version, index) => {
                const li = document.createElement('li');
                let text = `${version.idx_personal ?? index + 1}. ${version.text ?? ''} ✏️${version.idx_global ?? ''}`;
                if (version.delta_rank && version.delta_rank > 0) {
                    text += ` - 🍀${version.delta_rank}`;
                }

                const tooltipParts = [];
                if (version.progress && version.progress > 0) {
                    tooltipParts.push(`🚀 Прогресс: ${version.progress.toFixed(2)}`);
                    text += ' 🚀';
                } else if (version.penalty && version.penalty > 0) {
                    tooltipParts.push(`⚠️ Пенальти: ${version.penalty.toFixed(4)}`);
                    text += ' ⚠️';
                }

                li.textContent = text;
                if (tooltipParts.length > 0) {
                    li.title = tooltipParts.join('\n');
                }

                if (version.bg_color) {
                    li.style.backgroundColor = version.bg_color;
                } else {
                    setBgItem(index, li);
                }

                const isSecond = version.second_player || version.is_second || version.player === 2 || version.player_idx === 2;
                if (isSecond) {
                    li.classList.add('second-player');
                }
                list.appendChild(li);
            });
        } else {
            list.innerHTML = '<li>Нет версий для данной дуэли</li>';
        }

        updateThirdColumn();
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

document.querySelectorAll('input[name="duel-version-sort"]').forEach((radio) => {
    radio.addEventListener('change', () => {
        const header = document.getElementById('duel_vers-header');
        const duelId = header?.dataset.duelId;
        if (duelId) {
            loadDuelVersions(duelId);
        }
    });
});

document.getElementById('duel-version-graph-btn').addEventListener('click', async () => {
    const duelId = document.getElementById('duel_vers-header').dataset.duelId;

    try {
        window.open(`/duel/graph_vers/${duelId}`, '_blank');
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить график');
    }
});

function formatDateTime(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleString('ru-RU');
}

document.getElementById('duel-word-play-btn').addEventListener('click', async () => {
    const duelId = currentDuelMeta.id || document.getElementById('duel_vers-header').dataset.duelId;
    if (!duelId) {
        alert('Сначала выберите дуэль.');
        return;
    }

    try {
        const response = await fetch(`/duel/word_play_dates/${duelId}`);
        if (!response.ok) throw new Error('Ошибка при загрузке дат');
        const data = await response.json();

        const lines = [];
        if (data.word || currentDuelMeta.word) {
            lines.push(`Слово: ${data.word || currentDuelMeta.word}`);
        }

        if (!Array.isArray(data.participants) || data.participants.length === 0) {
            lines.push('Нет данных об участниках.');
            alert(lines.join('\n'));
            return;
        }

        data.participants.forEach((participant) => {
            lines.push('');
            lines.push(`${participant.name}:`);

            const entries = [];
            (participant.main_tryings || []).forEach((date) => {
                entries.push({ source: 'Основная', date });
            });
            (participant.duel_tryings || []).forEach((date) => {
                entries.push({ source: 'Дуэль', date });
            });

            entries.sort((a, b) => new Date(a.date) - new Date(b.date));

            if (entries.length === 0) {
                lines.push('— нет');
            } else {
                entries.forEach((entry) => {
                    lines.push(`- ${entry.source}: ${formatDateTime(entry.date)}`);
                });
            }
        });

        alert(lines.join('\n'));
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить даты попыток.');
    }
});

document.getElementById('duel-stats-btn').addEventListener('click', () => {
    window.open('/duel/stats', '_blank');
});


async function renderContextForDuelWord() {
    const header = document.getElementById('any-duel-header');
    const list = document.getElementById('any-duel-list');
    list.innerHTML = '';

    if (!currentDuelMeta.wordId) {
        header.textContent = 'Контекст слова дуэли';
        list.innerHTML = '<li>Сначала выберите дуэль</li>';
        return;
    }

    header.textContent = `Контекст: ${currentDuelMeta.word || ''}`;
    try {
        const response = await fetch(`/word/${currentDuelMeta.wordId}`);
        if (!response.ok) throw new Error('Ошибка при загрузке контекста слова');
        const data = await response.json();

        if (data && Array.isArray(data.context) && data.context.length > 0) {
            data.context.forEach((item, index) => {
                const listItem = document.createElement('li');
                listItem.textContent = `${index}. ${item}`;
                setBgItem(index, listItem);
                list.appendChild(listItem);
            });
        } else {
            list.innerHTML = '<li>Контекст не найден</li>';
        }
    } catch (error) {
        console.error('Ошибка при загрузке контекста слова дуэли', error);
        list.innerHTML = '<li>Не удалось загрузить контекст</li>';
    }
}


async function renderParticipantDuels() {
    const header = document.getElementById('any-duel-header');
    const list = document.getElementById('any-duel-list');
    list.innerHTML = '';

    if (!currentDuelMeta.participants.length) {
        header.textContent = 'Дуэли участников';
        list.innerHTML = '<li>Сначала выберите дуэль</li>';
        return;
    }

    const userIds = currentDuelMeta.participants
        .map((p) => p.id)
        .filter((id) => typeof id === 'number');

    header.textContent = 'Дуэли участников выбранной дуэли';

    if (!userIds.length) {
        list.innerHTML = '<li>Нет данных об участниках</li>';
        return;
    }

    try {
        const params = encodeURIComponent(userIds.join(','));
        const response = await fetch(`/duel/by_users?ids=${params}`);
        if (!response.ok) throw new Error('Ошибка при загрузке дуэлей участников');
        const data = await response.json();
        const duels = Array.isArray(data.duels) ? data.duels : [];

        renderDuelList(list, duels);
    } catch (error) {
        console.error('Ошибка при загрузке дуэлей участников', error);
        list.innerHTML = '<li>Не удалось загрузить дуэли участников</li>';
    }
}


async function renderDuelsByWord() {
    const header = document.getElementById('any-duel-header');
    const list = document.getElementById('any-duel-list');
    list.innerHTML = '';

    if (!currentDuelMeta.wordId) {
        header.textContent = 'Дуэли по слову';
        list.innerHTML = '<li>Сначала выберите дуэль</li>';
        return;
    }

    header.textContent = `Дуэли по слову: ${currentDuelMeta.word || ''}`;
    try {
        const response = await fetch(`/duel/by_word/${currentDuelMeta.wordId}`);
        if (!response.ok) throw new Error('Ошибка при загрузке дуэлей слова');
        const data = await response.json();
        const duels = Array.isArray(data.duels) ? data.duels : [];
        renderDuelList(list, duels);
    } catch (error) {
        console.error('Ошибка при загрузке дуэлей по слову', error);
        list.innerHTML = '<li>Не удалось загрузить дуэли по слову</li>';
    }
}


function updateThirdColumn() {
    const mode = document.querySelector('input[name="duel-sort"]:checked')?.value;
    if (mode === 'participants') {
        renderParticipantDuels();
    } else if (mode === 'word-duels') {
        renderDuelsByWord();
    } else {
        renderContextForDuelWord();
    }
}


document.querySelectorAll('input[name="duel-sort"]').forEach((radio) => {
    radio.addEventListener('change', () => updateThirdColumn());
});

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
