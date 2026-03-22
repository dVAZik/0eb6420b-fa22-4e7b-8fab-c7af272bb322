from aiohttp import web
import json
import asyncio
import uuid
import random
from typing import Dict
import os

# Хранилище игр
games = {}
waiting_players = []

class SeaBattleGame:
    def __init__(self):
        self.board_size = 10
        self.ships = {
            4: 1,  # 4-палубный
            3: 2,  # 3-палубные
            2: 3,  # 2-палубные
            1: 4   # 1-палубные
        }
    
    def create_empty_board(self):
        return [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
    
    def can_place_ship(self, board, row, col, size, horizontal):
        if horizontal:
            if col + size > self.board_size:
                return False
        else:
            if row + size > self.board_size:
                return False
        
        for i in range(-1, size + 1):
            for j in range(-1, 2):
                r = row + (i if not horizontal else j)
                c = col + (j if not horizontal else i)
                
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if board[r][c] != 0:
                        return False
        return True
    
    def place_ship(self, board, row, col, size, horizontal):
        for i in range(size):
            if horizontal:
                board[row][col + i] = size
            else:
                board[row + i][col] = size
    
    def generate_random_board(self):
        board = self.create_empty_board()
        
        for size, count in self.ships.items():
            for _ in range(count):
                placed = False
                attempts = 0
                while not placed and attempts < 1000:
                    horizontal = random.choice([True, False])
                    row = random.randint(0, self.board_size - 1)
                    col = random.randint(0, self.board_size - 1)
                    
                    if self.can_place_ship(board, row, col, size, horizontal):
                        self.place_ship(board, row, col, size, horizontal)
                        placed = True
                    attempts += 1
                
                if not placed:
                    return self.generate_random_board()
        
        return board
    
    def make_shot(self, board, row, col):
        if board[row][col] > 0:
            board[row][col] = -1
            destroyed = self.is_ship_destroyed(board, row, col)
            return True, destroyed
        elif board[row][col] == 0:
            board[row][col] = -2
            return False, False
        return False, False
    
    def is_ship_destroyed(self, board, row, col):
        ship_cells = [(row, col)]
        
        c = col - 1
        while c >= 0 and board[row][c] > 0:
            ship_cells.append((row, c))
            c -= 1
        
        c = col + 1
        while c < self.board_size and board[row][c] > 0:
            ship_cells.append((row, c))
            c += 1
        
        r = row - 1
        while r >= 0 and board[r][col] > 0:
            ship_cells.append((r, col))
            r -= 1
        
        r = row + 1
        while r < self.board_size and board[r][col] > 0:
            ship_cells.append((r, col))
            r += 1
        
        for r, c in ship_cells:
            if board[r][c] > 0:
                return False
        return True
    
    def check_winner(self, board):
        for row in board:
            for cell in row:
                if cell > 0:
                    return False
        return True
    
    def get_board_state(self, board, is_own=True):
        state = []
        for row in board:
            row_state = []
            for cell in row:
                if cell == -2:
                    row_state.append('miss')
                elif cell == -1:
                    row_state.append('hit')
                elif cell > 0 and is_own:
                    row_state.append('ship')
                else:
                    row_state.append('empty')
            state.append(row_state)
        return state

class BotAI:
    def __init__(self):
        self.last_hits = []
        self.hunting_mode = False
        
    def get_shot(self, game, board):
        if self.hunting_mode and self.last_hits:
            for hit_row, hit_col in self.last_hits:
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    row, col = hit_row + dr, hit_col + dc
                    if 0 <= row < game.board_size and 0 <= col < game.board_size:
                        if board[row][col] not in [-1, -2]:
                            return row, col
        
        while True:
            row = random.randint(0, game.board_size - 1)
            col = random.randint(0, game.board_size - 1)
            if board[row][col] not in [-1, -2]:
                return row, col
    
    def update_after_shot(self, row, col, hit, destroyed):
        if hit:
            self.last_hits.append((row, col))
            self.hunting_mode = True
            if destroyed:
                self.last_hits.clear()
                self.hunting_mode = False

class GameSession:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.players = {}
        self.game = SeaBattleGame()
        self.current_turn = None
        self.status = "waiting"
        self.bot_ai = None
        
    def add_player(self, player_id: str, player_name: str):
        self.players[player_id] = {
            'name': player_name,
            'board': self.game.generate_random_board(),
            'ready': False
        }
        if len(self.players) == 2:
            self.status = "active"
            self.current_turn = list(self.players.keys())[0]
    
    def make_move(self, player_id: str, row: int, col: int):
        if self.current_turn != player_id:
            return {'error': 'Не ваш ход'}
        
        opponent_id = [p for p in self.players.keys() if p != player_id][0]
        opponent_board = self.players[opponent_id]['board']
        
        hit, destroyed = self.game.make_shot(opponent_board, row, col)
        
        winner = None
        if self.game.check_winner(opponent_board):
            self.status = "finished"
            winner = player_id
        
        if not hit:
            self.current_turn = opponent_id
        
        return {
            'hit': hit,
            'destroyed': destroyed,
            'winner': winner,
            'current_turn': self.current_turn
        }
    
    def get_state(self, player_id: str):
        opponent_id = [p for p in self.players.keys() if p != player_id][0]
        return {
            'your_board': self.game.get_board_state(self.players[player_id]['board'], True),
            'opponent_board': self.game.get_board_state(self.players[opponent_id]['board'], False),
            'current_turn': self.current_turn == player_id,
            'status': self.status
        }

async def handle_game(request):
    return web.FileResponse('./templates/game.html')

async def handle_create_game(request):
    data = await request.json()
    player_name = data.get('name', 'Игрок')
    
    game_id = str(uuid.uuid4())[:8]
    session = GameSession(game_id)
    session.add_player(game_id, player_name)
    games[game_id] = session
    
    return web.json_response({
        'game_id': game_id,
        'player_id': game_id
    })

async def handle_join_game(request):
    data = await request.json()
    game_id = data.get('game_id')
    player_name = data.get('name', 'Игрок')
    
    if game_id not in games:
        return web.json_response({'error': 'Игра не найдена'}, status=404)
    
    session = games[game_id]
    if len(session.players) >= 2:
        return web.json_response({'error': 'Игра уже началась'}, status=400)
    
    player_id = str(uuid.uuid4())[:8]
    session.add_player(player_id, player_name)
    
    return web.json_response({
        'game_id': game_id,
        'player_id': player_id
    })

async def handle_quick_start(request):
    data = await request.json()
    player_name = data.get('name', 'Игрок')
    player_id = str(uuid.uuid4())[:8]
    
    waiting_players.append({
        'id': player_id,
        'name': player_name
    })
    
    # Проверяем через 2 секунды
    await asyncio.sleep(2)
    
    # Ищем соперника
    if len(waiting_players) >= 2:
        player1 = waiting_players.pop(0)
        player2 = waiting_players.pop(0)
        
        game_id = str(uuid.uuid4())[:8]
        session = GameSession(game_id)
        session.add_player(player1['id'], player1['name'])
        session.add_player(player2['id'], player2['name'])
        games[game_id] = session
        
        # Возвращаем правильный player_id
        if player1['id'] == player_id:
            return web.json_response({
                'game_id': game_id,
                'player_id': player1['id']
            })
        else:
            return web.json_response({
                'game_id': game_id,
                'player_id': player2['id']
            })
    
    # Удаляем игрока из очереди
    waiting_players[:] = [p for p in waiting_players if p['id'] != player_id]
    return web.json_response({'error': 'Соперник не найден'}, status=404)

async def handle_move(request):
    data = await request.json()
    game_id = data.get('game_id')
    player_id = data.get('player_id')
    row = data.get('row')
    col = data.get('col')
    
    if game_id not in games:
        return web.json_response({'error': 'Игра не найдена'}, status=404)
    
    session = games[game_id]
    result = session.make_move(player_id, row, col)
    
    return web.json_response(result)

async def handle_game_state(request):
    game_id = request.query.get('game_id')
    player_id = request.query.get('player_id')
    
    if game_id not in games:
        return web.json_response({'error': 'Игра не найдена'}, status=404)
    
    session = games[game_id]
    state = session.get_state(player_id)
    
    return web.json_response(state)

async def handle_bot_game(request):
    data = await request.json()
    player_id = data.get('player_id')
    action = data.get('action')
    
    if action == 'create':
        game_id = str(uuid.uuid4())[:8]
        session = GameSession(game_id)
        session.add_player(player_id, 'Игрок')
        
        bot_id = 'bot_' + str(uuid.uuid4())[:8]
        session.add_player(bot_id, 'Бот AI')
        session.bot_ai = BotAI()
        
        games[game_id] = session
        
        # Запускаем задачу для хода бота
        asyncio.create_task(bot_move_loop(game_id))
        
        return web.json_response({
            'game_id': game_id,
            'player_id': player_id
        })
    
    return web.json_response({'error': 'Неизвестное действие'}, status=400)

async def bot_move_loop(game_id):
    """Асинхронный цикл для ходов бота"""
    await asyncio.sleep(1)  # Небольшая задержка перед первым ходом
    
    while game_id in games:
        session = games[game_id]
        
        if session.status != "active":
            break
            
        # Если очередь бота
        if session.current_turn and session.current_turn.startswith('bot_'):
            player_id = session.current_turn
            
            # Получаем поле игрока
            player_id_human = [p for p in session.players.keys() if not p.startswith('bot_')][0]
            player_board = session.players[player_id_human]['board']
            
            # Бот выбирает клетку
            row, col = session.bot_ai.get_shot(session.game, player_board)
            
            # Делаем ход
            result = session.make_move(player_id, row, col)
            
            # Обновляем состояние бота
            session.bot_ai.update_after_shot(row, col, result.get('hit', False), result.get('destroyed', False))
            
            # Проверка на победу
            if result.get('winner'):
                session.status = "finished"
                break
        
        await asyncio.sleep(1)  # Пауза между ходами

async def health_check(request):
    """Health check для Render.com"""
    return web.json_response({'status': 'ok', 'games': len(games)})

def main():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/game', handle_game)
    app.router.add_post('/api/create_game', handle_create_game)
    app.router.add_post('/api/join_game', handle_join_game)
    app.router.add_post('/api/quick_start', handle_quick_start)
    app.router.add_post('/api/move', handle_move)
    app.router.add_get('/api/game_state', handle_game_state)
    app.router.add_post('/api/bot_game', handle_bot_game)
    
    # Статические файлы
    app.router.add_static('/static/', path='./static')
    
    port = int(os.environ.get('PORT', 8080))
    web.run_app(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
