from aiohttp import web
import json
import asyncio
import uuid
from typing import Dict
from game_logic import SeaBattleGame, BotAI

games = {}  # Хранилище игр
waiting_players = []  # Очередь для быстрого старта

class GameSession:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.players = {}
        self.game = SeaBattleGame()
        self.current_turn = None
        self.status = "waiting"  # waiting, active, finished
        
    def add_player(self, player_id: str, player_name: str):
        self.players[player_id] = {
            'name': player_name,
            'board': self.game.generate_random_board(),
            'ready': False
        }
        if len(self.players) == 2:
            self.status = "active"
            self.current_turn = list(self.players.keys())[0]
    
    def make_move(self, player_id: str, row: int, col: int) -> dict:
        if self.current_turn != player_id:
            return {'error': 'Не ваш ход'}
        
        opponent_id = [p for p in self.players.keys() if p != player_id][0]
        opponent_board = self.players[opponent_id]['board']
        
        hit, destroyed = self.game.make_shot(opponent_board, row, col)
        
        # Проверка на победу
        winner = None
        if self.game.check_winner(opponent_board):
            self.status = "finished"
            winner = player_id
        
        # Смена хода
        if not hit:
            self.current_turn = opponent_id
        
        return {
            'hit': hit,
            'destroyed': destroyed,
            'winner': winner,
            'current_turn': self.current_turn
        }
    
    def get_state(self, player_id: str) -> dict:
        opponent_id = [p for p in self.players.keys() if p != player_id][0]
        return {
            'your_board': self.game.get_board_state(self.players[player_id]['board'], True),
            'opponent_board': self.game.get_board_state(self.players[opponent_id]['board'], False),
            'current_turn': self.current_turn == player_id,
            'status': self.status
        }

async def handle_game(request: web.Request):
    """Главная страница игры"""
    return web.FileResponse('./templates/game.html')

async def handle_create_game(request: web.Request):
    """Создание новой игры"""
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

async def handle_join_game(request: web.Request):
    """Присоединение к игре по ссылке"""
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

async def handle_quick_start(request: web.Request):
    """Быстрый старт - поиск соперника"""
    data = await request.json()
    player_name = data.get('name', 'Игрок')
    player_id = str(uuid.uuid4())[:8]
    
    waiting_players.append({
        'id': player_id,
        'name': player_name
    })
    
    # Проверяем, есть ли соперник в очереди
    if len(waiting_players) >= 2:
        player1 = waiting_players.pop(0)
        player2 = waiting_players.pop(0)
        
        game_id = str(uuid.uuid4())[:8]
        session = GameSession(game_id)
        session.add_player(player1['id'], player1['name'])
        session.add_player(player2['id'], player2['name'])
        games[game_id] = session
        
        return web.json_response({
            'game_id': game_id,
            'player_id': player1['id'] if player1['id'] == player_id else player2['id']
        })
    
    # Ждем соперника
    await asyncio.sleep(30)  # Таймаут 30 секунд
    # Удаляем игрока из очереди, если соперник не нашелся
    waiting_players[:] = [p for p in waiting_players if p['id'] != player_id]
    return web.json_response({'error': 'Соперник не найден'}, status=404)

async def handle_move(request: web.Request):
    """Обработка хода"""
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

async def handle_game_state(request: web.Request):
    """Получение состояния игры"""
    game_id = request.query.get('game_id')
    player_id = request.query.get('player_id')
    
    if game_id not in games:
        return web.json_response({'error': 'Игра не найдена'}, status=404)
    
    session = games[game_id]
    state = session.get_state(player_id)
    
    return web.json_response(state)

async def handle_bot_game(request: web.Request):
    """Игра с ботом"""
    data = await request.json()
    player_id = data.get('player_id')
    action = data.get('action')
    
    # Создаем игру с ботом
    if action == 'create':
        game_id = str(uuid.uuid4())[:8]
        session = GameSession(game_id)
        session.add_player(player_id, 'Игрок')
        
        # Добавляем бота
        bot_id = 'bot_' + str(uuid.uuid4())[:8]
        session.add_player(bot_id, 'Бот AI')
        session.bot_ai = BotAI()
        
        games[game_id] = session
        return web.json_response({
            'game_id': game_id,
            'player_id': player_id
        })
    
    return web.json_response({'error': 'Неизвестное действие'}, status=400)

def main():
    app = web.Application()
    app.router.add_get('/game', handle_game)
    app.router.add_post('/api/create_game', handle_create_game)
    app.router.add_post('/api/join_game', handle_join_game)
    app.router.add_post('/api/quick_start', handle_quick_start)
    app.router.add_post('/api/move', handle_move)
    app.router.add_get('/api/game_state', handle_game_state)
    app.router.add_post('/api/bot_game', handle_bot_game)
    
    # Статические файлы
    app.router.add_static('/static/', path='./static')
    
    web.run_app(app, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()
