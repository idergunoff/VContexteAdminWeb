function logout() {
    window.location.href = '/logout';
}

document.getElementById('duels-back-btn').addEventListener('click', () => {
    window.location.href = '/admin';
});


async function duelsByMonth(selectedMonth) {
    try {
        const response = await fetch(`/duel/month/${selectedMonth}`);
        if (!response.ok) throw new Error('Ошибка при загрузке данных');
        const data = await response.json();

        const duelList = document.getElementById('duel-list');
        duelList.innerHTML = '';

        if (data.duels.length > 0) {
            data.duels.forEach(duel => {
                const listItem = document.createElement('li');

                const header = document.createElement('div');
                header.textContent = `${duel.date}. ${duel.word}`;
                listItem.appendChild(header);

                const firstLine = document.createElement('div');
                const first = duel.participants[0];
                firstLine.textContent = `${first.name} (${first.version_count})${duel.winner_id === first.id ? ' 👑' : ''}`;
                listItem.appendChild(firstLine);

                const secondLine = document.createElement('div');
                const second = duel.participants[1];
                secondLine.textContent = `${second.name} (${second.version_count})${duel.winner_id === second.id ? ' 👑' : ''}`;
                listItem.appendChild(secondLine);

                listItem.title = `Начало: ${duel.start_time}\nКонец: ${duel.end_time}\nДлительность: ${duel.duration} минут`;

                listItem.dataset.duelId = duel.id;
                listItem.addEventListener('click', () => loadDuelVersions(duel.id));

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

        const infoBlock = document.getElementById('duel-info');
        if (infoBlock) {
            const lines = [];
            if (data.word) lines.push(`🖋 ${data.word}`); // 🖋
            if (data.date) lines.push(`📅 ${data.date}`); // 📅
            lines.push(`🕛 ${data.start_time || ''} / 🏁 ${data.end_time || ''}`); // 🕛 / 🏁
            if (Array.isArray(data.participants)) {
                data.participants.forEach(p => {
                    lines.push(`👥 ${p.name} (${p.version_count})${data.winner_id === p.id ? ' 👑' : ''} 💰${p.coins} 🏆${p.vp} 🎖${p.du_r}`); // 👥 ... 👑
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

