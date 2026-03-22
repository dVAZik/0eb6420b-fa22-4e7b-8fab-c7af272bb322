import random
from typing import List, Tuple, Dict
import json

class SeaBattleGame:
    def __init__(self):
        self.board_size = 10
        self.ships = {
            4: 1,  # 4-палубный
            3: 2,  # 3-палубные
            2: 3,  # 2-палубные
            1: 4   # 1-палубные
        }
    
    def create_empty_board(self) -> List[List[int]]:
        """Создает пустое поле 10x10"""
        return [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
    
    def can_place_ship(self, board: List[List[int]], row: int, col: int, size: int, horizontal: bool) -> bool:
        """Проверяет, можно ли разместить корабль"""
        # Проверка границ
        if horizontal:
            if col + size > self.board_size:
                return False
        else:
            if row + size > self.board_size:
                return False
        
        # Проверка соседних клеток
        for i in range(-1, size + 1):
            for j in range(-1, 2):
                r = row + (i if not horizontal else j)
                c = col + (j if not horizontal else i)
                
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if board[r][c] != 0:
                        return False
        return True
    
    def place_ship(self, board: List[List[int]], row: int, col: int, size: int, horizontal: bool):
        """Размещает корабль на поле"""
        for i in range(size):
            if horizontal:
                board[row][col + i] = size
            else:
                board[row + i][col] = size
    
    def generate_random_board(self) -> List[List[int]]:
        """Генерирует случайное поле с кораблями"""
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
    
    def make_shot(self, board: List[List[int]], row: int, col: int) -> Tuple[bool, bool]:
        """
        Делает выстрел по полю
        Возвращает: (попал ли, уничтожил ли корабль)
        """
        if board[row][col] > 0:  # Попадание
            board[row][col] = -1  # Отмечаем как подбитый
            # Проверяем, уничтожен ли корабль
            destroyed = self.is_ship_destroyed(board, row, col)
            return True, destroyed
        elif board[row][col] == 0:  # Промах
            board[row][col] = -2  # Отмечаем как промах
            return False, False
        return False, False
    
    def is_ship_destroyed(self, board: List[List[int]], row: int, col: int) -> bool:
        """Проверяет, уничтожен ли корабль после попадания"""
        # Находим весь корабль
        ship_cells = [(row, col)]
        
        # Проверяем горизонталь
        c = col - 1
        while c >= 0 and board[row][c] > 0:
            ship_cells.append((row, c))
            c -= 1
        
        c = col + 1
        while c < self.board_size and board[row][c] > 0:
            ship_cells.append((row, c))
            c += 1
        
        # Проверяем вертикаль
        r = row - 1
        while r >= 0 and board[r][col] > 0:
            ship_cells.append((r, col))
            r -= 1
        
        r = row + 1
        while r < self.board_size and board[r][col] > 0:
            ship_cells.append((r, col))
            r += 1
        
        # Проверяем, все ли клетки корабля подбиты
        for r, c in ship_cells:
            if board[r][c] > 0:
                return False
        return True
    
    def check_winner(self, board: List[List[int]]) -> bool:
        """Проверяет, все ли корабли уничтожены"""
        for row in board:
            for cell in row:
                if cell > 0:
                    return False
        return True
    
    def get_board_state(self, board: List[List[int]], is_own: bool = True) -> List[List[str]]:
        """Возвращает состояние поля для отображения"""
        state = []
        for row in board:
            row_state = []
            for cell in row:
                if cell == -2:
                    row_state.append('miss')  # Промах
                elif cell == -1:
                    row_state.append('hit')   # Попадание
                elif cell > 0 and is_own:
                    row_state.append('ship')  # Свой корабль
                else:
                    row_state.append('empty') # Пустая клетка
            state.append(row_state)
        return state

class BotAI:
    def __init__(self):
        self.last_hits = []
        self.hunting_mode = False
        
    def get_shot(self, game: SeaBattleGame, board: List[List[int]]) -> Tuple[int, int]:
        """ИИ выбирает клетку для выстрела"""
        if self.hunting_mode and self.last_hits:
            # Режим охоты - стреляем рядом с последним попаданием
            for hit_row, hit_col in self.last_hits:
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    row, col = hit_row + dr, hit_col + dc
                    if 0 <= row < game.board_size and 0 <= col < game.board_size:
                        if board[row][col] not in [-1, -2]:
                            return row, col
        
        # Случайный выстрел
        while True:
            row = random.randint(0, game.board_size - 1)
            col = random.randint(0, game.board_size - 1)
            if board[row][col] not in [-1, -2]:
                return row, col
    
    def update_after_shot(self, row: int, col: int, hit: bool, destroyed: bool):
        """Обновляет состояние ИИ после выстрела"""
        if hit:
            self.last_hits.append((row, col))
            self.hunting_mode = True
            if destroyed:
                self.last_hits.clear()
                self.hunting_mode = False
        else:
            if not self.hunting_mode:
                pass  # Просто промах
