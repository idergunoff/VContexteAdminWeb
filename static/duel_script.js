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
                firstLine.textContent = `${first.name} (${first.versions})${duel.winner_id === first.id ? ' 👑' : ''}`;
                listItem.appendChild(firstLine);

                const secondLine = document.createElement('div');
                const second = duel.participants[1];
                secondLine.textContent = `${second.name} (${second.versions})${duel.winner_id === second.id ? ' 👑' : ''}`;
                listItem.appendChild(secondLine);

                listItem.title = `Начало: ${duel.start_time}\nКонец: ${duel.end_time}\nДлительность: ${duel.duration}`;

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

