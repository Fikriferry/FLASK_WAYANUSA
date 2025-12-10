document.addEventListener('DOMContentLoaded', function() {
    loadLeaderboard('Beginner');

    document.getElementById('level-select').addEventListener('change', function() {
        const level = this.value;
        loadLeaderboard(level);
    });
});

async function loadLeaderboard(level) {
    try {
        const response = await fetch(`/api/leaderboard?level=${level}`);
        if (!response.ok) {
            throw new Error('Failed to fetch leaderboard');
        }
        const data = await response.json();
        renderLeaderboard(data);
    } catch (error) {
        console.error('Error loading leaderboard:', error);
        document.getElementById('podium').innerHTML = '<p>Gagal memuat leaderboard.</p>';
        document.getElementById('leaderboard-cards').innerHTML = '';
        document.getElementById('user-position').innerHTML = '';
    }
}

function renderLeaderboard(data) {
    const leaderboard = data.leaderboard;
    const yourRank = data.your_rank;
    const yourScore = data.your_score;

    // Render podium
    const podiumContainer = document.getElementById('podium');
    podiumContainer.innerHTML = '';
    if (leaderboard.length >= 3) {
        for (let i = 0; i < 3; i++) {
            const item = leaderboard[i];
            const podiumItem = document.createElement('div');
            podiumItem.className = `podium-item podium-${i + 1}`;
            podiumItem.innerHTML = `
                <div class="podium-base">
                    <img src="${item.img}" alt="Wayang ${item.rank}">
                    <div class="name">${item.name}</div>
                    <div class="score">${item.score} Poin</div>
                </div>
            `;
            podiumContainer.appendChild(podiumItem);
        }
    }

    // Render table
    const tbody = document.getElementById('leaderboard-tbody');
    tbody.innerHTML = '';
    leaderboard.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.rank}</td>
            <td>${item.name}</td>
            <td>${item.level}</td>
            <td>${item.score}</td>
        `;
        tbody.appendChild(row);
    });

    // Render user position
    const userPosition = document.getElementById('user-position');
    if (yourRank) {
        const total = leaderboard.length;
        const percentage = ((yourRank / total) * 100).toFixed(1);
        userPosition.innerHTML = `Kamu berada di ${percentage}% peringkat teratas pada level ini dengan ${yourScore} poin`;
    } else {
        userPosition.innerHTML = 'Masuk untuk melihat posisi Anda';
    }
}
