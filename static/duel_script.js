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

                // Заголовок дуэли (дата + слово)
                const title = document.createElement('div');
                title.textContent = `${duel.date}. ${duel.word}`;
                listItem.appendChild(title);

                // Список участников
                const participantsUl = document.createElement('ul');
                duel.participants.forEach(p => {
                    const participantLi = document.createElement('li');
                    participantLi.textContent = `${p.name}`;
                    participantsUl.appendChild(participantLi);
                });
                listItem.appendChild(participantsUl);

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

