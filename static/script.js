let currentGameId = null;
let currentPlayerId = null;
let updateInterval = null;

function showCreateGame() {
    const playerName = prompt('Введите ваше имя:', 'Игрок');
    if (!playerName) return;
    
    fetch('/api/create_game', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: playerName})
    })
    .then(response => response.json())
    .then(data => {
        currentGameId = data.game_id;
        currentPlayerId = data.player_id;
        showGame();
        alert(`Игра создана! ID игры: ${currentGameId}\nПоделитесь этим ID с другом`);
        startGameUpdate();
    });
}

function showJoinForm() {
    document.getElementById('joinForm').style.display = 'block';
}

function hideJoinForm() {
    document.getElementById('joinForm').style.display = 'none';
}

function joinGame() {
    const gameId = document.getElementById('gameId').value;
    const playerName = document.getElementById('playerName').value || 'Игрок';
    
    fetch('/api/join_game', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({game_id: gameId, name: playerName})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        currentGameId = data.game_id;
        currentPlayerId = data.player_id;
        showGame();
        startGameUpdate();
    });
}

function quickStart() {
    const playerName = prompt('Введите ваше имя:', 'Игрок');
    if (!playerName) return;
    
    fetch('/api/quick_start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: playerName})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        currentGameId = data.game_id;
        currentPlayerId = data.player_id;
        showGame();
        startGameUpdate();
    });
}

function startBotGame() {
    const playerName = prompt('Введите ваше имя:', 'Игрок');
    if (!playerName) return;
    
    const playerId = 'player_' + Math.random().toString(36).substr(2, 9);
    currentPlayerId = playerId;
    
    fetch('/api/bot_game', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: 'create', player_id: playerId})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        currentGameId = data.game_id;
        showGame();
        startGameUpdate();
    });
}

function showGame() {
    document.getElementById('menu').style.display = 'none';
    document.getElementById('gameContainer').style.display = 'flex';
}

function makeMove(row, col) {
    fetch('/api/move', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            game_id: currentGameId,
            player_id: currentPlayerId,
            row: row,
            col: col
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        if (data.winner) {
            alert('Поздравляем! Вы победили!');
            endGame();
        }
        
        updateGameState();
    });
}

function updateGameState() {
    fetch(`/api/game_state?game_id=${currentGameId}&player_id=${currentPlayerId}`)
    .then(response => response.json())
    .then(data => {
        renderBoards(data.your_board, data.opponent_board, data.current_turn);
        updateStatus(data);
    });
}

function renderBoards(yourBoard, opponentBoard, isYourTurn) {
    const yourBoardDiv = document.getElementById('yourBoard');
    const opponentBoardDiv = document.getElementById('opponentBoard');
    
    yourBoardDiv.innerHTML = renderBoard(yourBoard, false);
    opponentBoardDiv.innerHTML = renderBoard(opponentBoard, true, isYourTurn);
}

function renderBoard(board, isOpponent, isYourTurn = false) {
    let html = '<table>';
    for (let i = 0; i < 10; i++) {
        html += '<tr>';
        for (let j = 0; j < 10; j++) {
            let cellClass = board[i][j];
            let clickable = isOpponent && isYourTurn && (cellClass === 'empty');
            let onclick = clickable ? `onclick="makeMove(${i}, ${j})"` : '';
            html += `<td class="cell ${cellClass}" ${onclick}></td>`;
        }
        html += '</tr>';
    }
    html += '</table>';
    return html;
}

function updateStatus(data) {
    const statusDiv = document.getElementById('gameStatus');
    let statusText = '';
    
    if (data.status === 'waiting') {
        statusText = '<h3>⏳ Ожидание соперника...</h3>';
    } else if (data.status === 'active') {
        if (data.current_turn) {
            statusText = '<h3>🎯 Ваш ход!</h3>';
        } else {
            statusText = '<h3>⏰ Ход противника...</h3>';
        }
    } else if (data.status === 'finished') {
        statusText = '<h3>🏆 Игра окончена!</h3>';
        endGame();
    }
    
    statusDiv.innerHTML = statusText;
}

function startGameUpdate() {
    if (updateInterval) clearInterval(updateInterval);
    updateInterval = setInterval(updateGameState, 1000);
}

function endGame() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
    
    setTimeout(() => {
        if (confirm('Хотите сыграть еще раз?')) {
            location.reload();
        }
    }, 1000);
}
